from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.decision_engine.scoring import evaluate
from app.main import create_app
from app.models.analysis import Analysis, Context, Option
from app.models.evaluation import EvaluationInput, analysis_signature


def case():
    options = [Option(id=uuid4(), description=name) for name in ['Accept', 'Decline']]
    analysis = Analysis(decision_id=uuid4(), reviewed=True,
        context=Context(situation='Should I accept the project?', problem='Accept the project?',
                        domain='Work', stakes='High', time_pressure='Low'), options=options)
    criterion = str(uuid4())
    data = {'analysis_signature': analysis_signature(analysis),
            'criteria': [{'id': criterion, 'name': 'Benefit', 'weight': 2}],
            'ratings': [{'option_id': str(o.id), 'scores': {criterion: score}} for o, score in zip(options, [8, 4])],
            'rules': [], 'preferred_option_id': None}
    return analysis, data, criterion


def run(analysis, data):
    return evaluate(analysis, EvaluationInput.model_validate(data))


def rule(criterion, **overrides):
    return {'id': str(uuid4()), 'name': 'Minimum benefit', 'criterion_id': criterion,
            'comparison': 'below', 'threshold': 5, 'effect': 'exclude', 'penalty': 0, **overrides}


def test_weighted_contributions():
    analysis, data, _criterion = case()
    second = str(uuid4())
    data['criteria'].append({'id': second, 'name': 'Reversibility', 'weight': 6})
    data['ratings'][0]['scores'][second] = 2
    data['ratings'][1]['scores'][second] = 10
    result = run(analysis, data)
    assert [o.final_score for o in result.options] == [35, 85]
    assert result.recommended_option_id == analysis.options[1].id
    assert [c.points for c in result.options[0].contributions] == [20, 15]
    assert run(analysis, data) == result


@pytest.mark.parametrize('change,status', [('tie','tie'), ('unknown','incomplete'), ('zero_weights','incomplete'), ('no_criteria','incomplete')])
def test_no_false_winner(change, status):
    analysis, data, criterion = case()
    if change == 'tie': data['ratings'][1]['scores'][criterion] = 8
    if change == 'unknown': data['ratings'][0]['scores'][criterion] = None
    if change == 'zero_weights': data['criteria'][0]['weight'] = 0
    if change == 'no_criteria':
        data['criteria'] = []
        for rating in data['ratings']: rating['scores'] = {}
    result = run(analysis, data)
    assert result.status == status
    assert result.recommended_option_id is None


def test_exclusion_overrides_score_and_flags_preference():
    analysis, data, criterion = case()
    data['rules'] = [rule(criterion, comparison='above', threshold=7)]
    data['preferred_option_id'] = str(analysis.options[0].id)
    result = run(analysis, data)
    assert result.options[0].eligible is False
    assert result.options[0].base_score == 80
    assert result.recommended_option_id == analysis.options[1].id
    assert len(result.conflicts) == 2
    assert result.options[0].rules[0].triggered is True


def test_penalties_boundaries_and_all_excluded():
    analysis, data, criterion = case()
    data['rules'] = [rule(criterion, comparison='above', threshold=4, effect='penalize', penalty=60)]
    result = run(analysis, data)
    assert [o.final_score for o in result.options] == [20,40]
    assert result.options[1].rules[0].triggered is False
    data['rules'].append(rule(criterion, threshold=10))
    result = run(analysis, data)
    assert result.status == 'no_eligible_options'
    assert result.recommended_option_id is None


def test_unknown_rule_even_on_zero_weight_blocks_recommendation():
    analysis, data, _criterion = case()
    second = str(uuid4())
    data['criteria'].append({'id':second, 'name':'Risk', 'weight':0})
    for rating in data['ratings']: rating['scores'][second] = None
    assert run(analysis, data).status == 'recommended'
    data['rules'] = [rule(second)]
    result = run(analysis, data)
    assert result.status == 'incomplete'
    assert result.options[0].eligible is None
    assert result.options[0].rules[0].triggered is None


@pytest.mark.parametrize('invalid', ['negative', 'too_large', 'nan', 'duplicate', 'missing_score', 'unknown_rule', 'invalid_penalty'])
def test_input_validation(invalid):
    _analysis, data, criterion = case()
    if invalid == 'negative': data['criteria'][0]['weight'] = -1
    if invalid == 'too_large': data['ratings'][0]['scores'][criterion] = 11
    if invalid == 'nan': data['ratings'][0]['scores'][criterion] = float('nan')
    if invalid == 'duplicate': data['criteria'].append(deepcopy(data['criteria'][0]))
    if invalid == 'missing_score': data['ratings'][0]['scores'] = {}
    if invalid == 'unknown_rule': data['rules'] = [rule(str(uuid4()))]
    if invalid == 'invalid_penalty': data['rules'] = [rule(criterion, effect='penalize', penalty=0)]
    with pytest.raises(ValidationError): EvaluationInput.model_validate(data)


def test_saved_evaluation_and_stale_context(tmp_path):
    settings = Settings(database_url=f'sqlite:///{tmp_path}/db', _env_file=None)
    with TestClient(create_app(settings)) as client:
        decision = client.post('/api/v1/decisions', json={'situation':'Option: Accept\nOption: Decline', 'domain':'Work', 'stakes':'High', 'time_pressure':'Low'}).json()
        path = f"/api/v1/decisions/{decision['id']}"
        analysis = client.post(path+'/analysis').json()
        draft = {k:analysis[k] for k in ['context','options']}
        analysis = client.put(path+'/analysis', json=draft).json()
        envelope = client.get(path+'/evaluation').json()
        assert envelope['evaluation'] is None
        criterion = str(uuid4())
        data = {'analysis_signature':envelope['analysis_signature'],
                'criteria':[{'id':criterion,'name':'Benefit','weight':1}],
                'ratings':[{'option_id':o['id'],'scores':{criterion:v}} for o,v in zip(analysis['options'],[8,4])], 'rules':[]}
        response = client.put(path+'/evaluation',json=data)
        assert response.status_code == 200
        saved = response.json()
        assert saved['result']['status'] == 'recommended'
        invalid = deepcopy(data); invalid['ratings'].pop()
        assert client.put(path+'/evaluation',json=invalid).status_code == 422
        assert client.get(path+'/evaluation').json()['evaluation'] == saved
    with TestClient(create_app(settings)) as client:
        assert client.get(path+'/evaluation').json()['evaluation'] == saved
        draft['context']['problem'] = 'Revised scope for this decision'
        client.put(path+'/analysis',json=draft)
        assert client.get(path+'/evaluation').json()['evaluation']['stale'] is True
        assert client.put(path+'/evaluation',json=data).status_code == 409
        assert client.get(path+'/evaluation').json()['evaluation']['inputs'] == saved['inputs']
