from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_structure_review_persist_and_preserve_m2(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path}/decisions.db", _env_file=None)
    body = {"situation": "Problem: Accept the project?\nActor: Brian\nFact: I received an offer.\nConstraint: Finish by Friday.\nUnknown: Material availability\nOption: Accept\nOption: Decline", "domain": "Work", "stakes": "High", "time_pressure": "Moderate"}
    with TestClient(create_app(settings)) as client:
        decision = client.post('/api/v1/decisions', json=body).json()
        path = f"/api/v1/decisions/{decision['id']}/analysis"
        assert client.get(path).status_code == 404
        response = client.post(path)
        assert response.status_code == 200
        analysis = response.json()
        assert analysis['context']['actors'] == ['Brian']
        assert analysis['context']['problem'] == 'Accept the project?'
        assert analysis['context']['known_facts'] == ['I received an offer.']
        assert analysis['context']['constraints'] == ['Finish by Friday.']
        assert analysis['context']['unknowns'] == ['Material availability']
        assert [o['description'] for o in analysis['options']] == ['Accept', 'Decline']
        assert len({o['id'] for o in analysis['options']}) == 2
        assert client.post(path).json() == analysis
        payload = deepcopy({key: analysis[key] for key in ['context', 'options']})
        payload['context']['unknowns'] = ['Confirm delivery date']
        saved = client.put(path, json=payload)
        assert saved.status_code == 200
        reviewed = saved.json()
        assert reviewed['reviewed'] is True
        assert reviewed['options'] == analysis['options']
        assert client.post(path).json() == reviewed  # Never discard reviewed work.
        assert client.get(f"/api/v1/decisions/{decision['id']}").json() == decision
    with TestClient(create_app(settings)) as client:
        assert client.get(path).json() == reviewed
        assert client.post(path).json() == reviewed


def test_ambiguous_prose_is_not_invented_context(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path}/db", _env_file=None))) as client:
        prose = "Maybe Brian can help. I don't know if the deadline is firm. Should I wait or ask?"
        decision = client.post('/api/v1/decisions', json={"situation": prose, "domain": "Work", "stakes": "Low", "time_pressure": "None"}).json()
        path = f"/api/v1/decisions/{decision['id']}/analysis"
        analysis = client.post(path).json()
        assert analysis['context']['problem'] == prose
        assert analysis['options'] == []
        for field in ['actors', 'known_facts', 'constraints', 'unknowns']:
            assert analysis['context'][field] == []
        assert analysis['warnings']
        payload = deepcopy({key: analysis[key] for key in ['context', 'options']})
        payload['context']['problem'] = ' '
        assert client.put(path, json=payload).status_code == 422
        payload['context']['problem'] = prose
        option = {'id': str(uuid4()), 'description': 'Ask for clarification'}
        payload['options'] = [option, option]
        assert client.put(path, json=payload).status_code == 422
        payload['options'] = [{**option, 'description': ' '}]
        assert client.put(path, json=payload).status_code == 422
        payload['options'] = [option]
        payload['context']['situation'] = 'Changing the source is not permitted.'
        assert client.put(path, json=payload).status_code == 422
        assert client.get(path).json() == analysis
        absent = f'/api/v1/decisions/{uuid4()}/analysis'
        assert client.post(absent).status_code == 404
        assert client.get(absent).status_code == 404
        assert client.put(absent, json=payload).status_code == 404


def test_m2_database_upgrade_retains_records(tmp_path: Path) -> None:
    import sqlite3

    database = tmp_path / 'legacy.db'
    decision_id = str(uuid4())
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE decisions (id TEXT PRIMARY KEY, situation TEXT NOT NULL, domain TEXT NOT NULL, stakes TEXT NOT NULL, time_pressure TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
        connection.execute('INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (decision_id, 'Should I accept the project?', 'Work', 'High', 'Low',
                            '2026-09-01T00:00:00+00:00', '2026-09-01T00:00:00+00:00'))
    settings = Settings(database_url=f'sqlite:///{database}', _env_file=None)
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/v1/decisions').json()[0]['id'] == decision_id
        response = client.post(f'/api/v1/decisions/{decision_id}/analysis')
        assert response.status_code == 200
        assert response.json()['context']['problem'] == 'Should I accept the project?'
