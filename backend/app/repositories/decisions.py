import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.models.analysis import Analysis
from app.models.decision import Decision, DecisionCreate
from app.models.evaluation import SavedEvaluation, analysis_signature
from app.models.suggestion import Suggestion


class DecisionRepository:
    def __init__(self, database_url: str) -> None:
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("DATABASE_URL must start with sqlite:///")
        path = database_url[len(prefix):]
        if not path or path == ":memory:":
            raise ValueError("DATABASE_URL must reference a persistent SQLite file")
        self.path = Path(path).expanduser().resolve()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    situation TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    stakes TEXT NOT NULL,
                    time_pressure TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS decision_analyses (
                    decision_id TEXT PRIMARY KEY REFERENCES decisions(id),
                    payload TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS decision_evaluations (
                    decision_id TEXT PRIMARY KEY REFERENCES decisions(id),
                    payload TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS decision_suggestions (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL REFERENCES decisions(id),
                    payload TEXT NOT NULL
                )
            """)

    def get_suggestion(self, decision_id: UUID, suggestion_id: UUID | None = None) -> Suggestion | None:
        with closing(self._connect()) as connection:
            query = "SELECT payload FROM decision_suggestions WHERE decision_id = ?"
            params = [str(decision_id)]
            if suggestion_id is not None:
                query += " AND id = ?"
                params.append(str(suggestion_id))
            row = connection.execute(query + " ORDER BY rowid DESC LIMIT 1", params).fetchone()
        return Suggestion.model_validate_json(row["payload"]) if row else None

    def save_suggestion(self, suggestion: Suggestion) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("INSERT INTO decision_suggestions (id, decision_id, payload) VALUES (?, ?, ?)",
                               (str(suggestion.id), str(suggestion.decision_id), suggestion.model_dump_json()))

    def apply_suggestion(self, decision_id: UUID, suggestion_id: UUID, analysis: Analysis) -> bool:
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            suggestion_row = connection.execute("SELECT payload FROM decision_suggestions WHERE decision_id = ? AND id = ?",
                                                (str(decision_id), str(suggestion_id))).fetchone()
            analysis_row = connection.execute("SELECT payload FROM decision_analyses WHERE decision_id = ?",
                                              (str(decision_id),)).fetchone()
            if not suggestion_row or not analysis_row:
                return False
            suggestion = Suggestion.model_validate_json(suggestion_row["payload"])
            current = Analysis.model_validate_json(analysis_row["payload"])
            if suggestion.id != suggestion_id or suggestion.base_signature != analysis_signature(current):
                return False
            connection.execute("UPDATE decision_analyses SET payload = ? WHERE decision_id = ?",
                               (analysis.model_dump_json(), str(decision_id)))
        return True

    def get_evaluation(self, decision_id: UUID) -> SavedEvaluation | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM decision_evaluations WHERE decision_id = ?", (str(decision_id),)
            ).fetchone()
        return SavedEvaluation.model_validate_json(row["payload"]) if row else None

    def save_evaluation(self, decision_id: UUID, evaluation: SavedEvaluation) -> bool:
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload FROM decision_analyses WHERE decision_id = ?", (str(decision_id),)
            ).fetchone()
            if not row or analysis_signature(Analysis.model_validate_json(row["payload"])) != evaluation.inputs.analysis_signature:
                return False
            connection.execute(
                "INSERT INTO decision_evaluations (decision_id, payload) VALUES (?, ?) "
                "ON CONFLICT(decision_id) DO UPDATE SET payload = excluded.payload",
                (str(decision_id), evaluation.model_dump_json()),
            )
        return True

    def get_analysis(self, decision_id: UUID) -> Analysis | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM decision_analyses WHERE decision_id = ?", (str(decision_id),)
            ).fetchone()
        return Analysis.model_validate_json(row["payload"]) if row else None

    def save_analysis(self, analysis: Analysis, *, create_only: bool = False) -> Analysis:
        with closing(self._connect()) as connection, connection:
            conflict = "DO NOTHING" if create_only else "DO UPDATE SET payload = excluded.payload"
            connection.execute(
                "INSERT INTO decision_analyses (decision_id, payload) VALUES (?, ?) "
                f"ON CONFLICT(decision_id) {conflict}",
                (str(analysis.decision_id), analysis.model_dump_json()),
            )
            row = connection.execute(
                "SELECT payload FROM decision_analyses WHERE decision_id = ?",
                (str(analysis.decision_id),),
            ).fetchone()
        return Analysis.model_validate_json(row["payload"])

    def create(self, draft: DecisionCreate) -> Decision:
        now = datetime.now(UTC)
        decision = Decision(id=uuid4(), created_at=now, updated_at=now, **draft.model_dump())
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO decisions
                (id, situation, domain, stakes, time_pressure, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(decision.id), decision.situation, decision.domain, decision.stakes,
                 decision.time_pressure, now.isoformat(), now.isoformat()),
            )
        return decision

    def list(self) -> list[Decision]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM decisions ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [Decision.model_validate(dict(row)) for row in rows]

    def get(self, decision_id: UUID) -> Decision | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM decisions WHERE id = ?", (str(decision_id),)
            ).fetchone()
        return Decision.model_validate(dict(row)) if row else None
