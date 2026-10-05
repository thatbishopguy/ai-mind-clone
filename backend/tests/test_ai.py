import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import OpenAI

from app.core.config import Settings
from app.main import create_app
from app.models.analysis import Analysis
from app.models.decision import Decision
from app.models.suggestion import ProposedContext
from app.providers.reasoning import OpenAIReasoning, ProviderFailure

PROPOSAL = {'problem':'Accept the project?', 'actors':[], 'constraints':[],
            'reported_facts':[{'statement':'An offer was received.', 'source_quote':'I received an offer.'}],
            'unknowns':['Confirm schedule'],
            'options':[{'description':'Accept', 'rationale':'Proceed if timing fits.', 'assumptions':['Time is available']},
                       {'description':'Decline', 'rationale':'Preserve availability.', 'assumptions':[]}],
            'summary':'Compare the opportunity with scheduling constraints.', 'assumptions':[]}


def setup(client):
    decision = client.post('/api/v1/decisions',json={'situation':'I received an offer. Should I accept?', 'domain':'Work','stakes':'High','time_pressure':'Low'}).json()
    path=f"/api/v1/decisions/{decision['id']}"
    analysis=client.post(path+'/analysis').json()
    analysis=client.put(path+'/analysis',json={k:analysis[k] for k in ['context','options']}).json()
    return decision,path,analysis


class FakeProvider:
    def suggest(self, decision, analysis):
        return ProposedContext.model_validate(PROPOSAL)


def test_preview_apply_review_history_and_stale(tmp_path):
    settings=Settings(database_url=f'sqlite:///{tmp_path}/db',openai_api_key=None,_env_file=None)
    app=create_app(settings)
    with TestClient(app) as client:
        _,path,original=setup(client)
        app.state.reasoning=FakeProvider()
        suggestion=client.post(path+'/ai-suggestion').json()
        assert suggestion['source']=='openai'
        assert client.get(path+'/analysis').json()==original
        applied=client.post(path+f"/ai-suggestion/{suggestion['id']}/apply")
        assert applied.status_code==200
        draft=applied.json()
        assert draft['reviewed'] is False
        assert draft['ai_provenance']['suggestion_id']==suggestion['id']
        assert [o['description'] for o in draft['options']]==['Accept','Decline']
        assert client.post(path+f"/ai-suggestion/{suggestion['id']}/apply").status_code==409
        reviewed=client.put(path+'/analysis',json={k:draft[k] for k in ['context','options']}).json()
        assert reviewed['reviewed'] is True
        assert reviewed['ai_provenance']==draft['ai_provenance']
        fresh=client.post(path+'/ai-suggestion').json()
        revised={k:reviewed[k] for k in ['context','options']}
        revised['context']['problem']='Changed decision context'
        client.put(path+'/analysis',json=revised)
        assert client.get(path+'/ai-suggestion').json()['suggestion']['stale'] is True
        assert client.post(path+f"/ai-suggestion/{fresh['id']}/apply").status_code==409
        assert app.state.decisions.get_suggestion(draft['decision_id'],suggestion['id']) is not None
    with TestClient(create_app(settings)) as client:
        assert client.get(path+'/analysis').json()['ai_provenance']==draft['ai_provenance']


def test_no_key_fallback_leaves_saved_analysis_untouched(tmp_path):
    with TestClient(create_app(Settings(database_url=f'sqlite:///{tmp_path}/db',openai_api_key=None,_env_file=None))) as client:
        _,path,original=setup(client)
        assert client.get(path+'/ai-suggestion').json()['configured'] is False
        fallback=client.post(path+'/ai-suggestion').json()
        assert fallback['source']=='rules_fallback'
        assert fallback['model'] is None
        assert 'not configured' in fallback['notice']
        assert client.get(path+'/analysis').json()==original
        assert client.post(path+f"/ai-suggestion/{fallback['id']}/apply").status_code==409


@pytest.mark.parametrize('mode', ['valid','refusal','incomplete','bad_json','bad_quote','duplicate','blank','timeout','rate_limit','auth_error'])
def test_real_sdk_transport_boundary(mode, monkeypatch, tmp_path):
    import app.providers.reasoning as module
    with TestClient(create_app(Settings(database_url=f'sqlite:///{tmp_path}/db',openai_api_key=None,_env_file=None))) as client:
        decision,_,analysis=setup(client)
    payload=deepcopy(PROPOSAL)
    if mode=='bad_quote':payload['reported_facts'][0]['source_quote']='Invented source'
    if mode=='duplicate':payload['options'].append(deepcopy(payload['options'][0]))
    if mode=='blank':payload['actors']=[' ']
    def handler(request):
        body=json.loads(request.content)
        assert body['store'] is False
        assert body['text']['format']['type']=='json_schema'
        assert body['text']['format']['strict'] is True
        assert 'weights' not in body['input'][1]['content']
        if mode=='timeout':raise httpx.ReadTimeout('simulated secret error',request=request)
        if mode in {'rate_limit','auth_error'}:
            return httpx.Response(429 if mode=='rate_limit' else 401,json={'error':{'message':'DO NOT LEAK THIS','type':'error'}})
        content={'type':'refusal','refusal':'Cannot comply'} if mode=='refusal' else {'type':'output_text','text':'{' if mode=='bad_json' else json.dumps(payload),'annotations':[]}
        return httpx.Response(200,json={'id':'resp_test','object':'response','created_at':0,'model':'test-model',
            'status':'incomplete' if mode=='incomplete' else 'completed',
            'output':[{'id':'msg_test','type':'message','role':'assistant','status':'completed','content':[content]}]})
    def factory(**kwargs):
        return OpenAI(**kwargs,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(module,'OpenAI',factory)
    provider=OpenAIReasoning('test-key-not-a-secret','test-model')
    if mode=='valid':
        assert provider.suggest(Decision.model_validate(decision),Analysis.model_validate(analysis)).problem=='Accept the project?'
    else:
        with pytest.raises(ProviderFailure) as error:
            provider.suggest(Decision.model_validate(decision),Analysis.model_validate(analysis))
        assert 'DO NOT LEAK' not in str(error.value)
        assert 'secret' not in str(error.value)
