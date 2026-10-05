from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.decisions import router as decisions_router
from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.providers.reasoning import OpenAIReasoning
from app.repositories.decisions import DecisionRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    repository = DecisionRepository(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository.initialize()
        app.state.decisions = repository
        app.state.reasoning = OpenAIReasoning(settings.openai_api_key, settings.openai_model) if settings.openai_api_key else None
        app.state.ai_model = settings.openai_model
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.5.0",
        description="Decision Engine and Mind Model API",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(decisions_router, prefix="/api/v1")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": settings.app_name, "status": "development", "milestone": "M5"}

    return app


app = create_app()
