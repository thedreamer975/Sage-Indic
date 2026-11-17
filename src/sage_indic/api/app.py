"""FastAPI application exposing the SAGE-Indic query pipeline."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from sage_indic import __version__
from sage_indic.composition.examples import get_examples
from sage_indic.config import find_project_root
from sage_indic.pipeline.service import SageQueryService

logger = logging.getLogger("sage_indic.api")


class QueryRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
        description="Telugu, Romanized Telugu, or code-mixed query",
    )
    use_llm: bool | None = Field(
        default=None,
        description=(
            "True enables the optional LLM paraphrase layer; false forces "
            "deterministic composition."
        ),
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Number of evidence passages to retrieve",
    )

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


def create_app(service: SageQueryService | None = None) -> FastAPI:
    """Create the API application. Tests may inject a pre-built service."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service or SageQueryService()
        logger.info(
            "SAGE-Indic service ready (corpus=%s chunks)",
            len(app.state.service.corpus.chunks),
        )
        yield

    app = FastAPI(
        title="SAGE-Indic API",
        version=__version__,
        description=(
            "Telugu-first evidence-grounded NLP demo. Responses separate retrieved evidence, "
            "claim verification, citations, and optional LLM generation."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def get_service(request: Request) -> SageQueryService:
        return request.app.state.service

    @app.get("/api/health")
    def health(request: Request) -> dict[str, Any]:
        active = get_service(request)
        return {
            "status": "ok" if active.corpus.chunks else "degraded",
            "service": "SAGE-Indic",
            "version": __version__,
            "corpus_loaded": bool(active.corpus.chunks),
        }

    @app.get("/api/status")
    def status(request: Request) -> dict[str, Any]:
        return get_service(request).status()

    @app.get("/api/examples")
    def examples() -> dict[str, Any]:
        return {
            "examples": get_examples(),
            "note": "Examples are prompts only; answers are generated live from the corpus.",
        }

    @app.get("/api/corpus")
    def corpus(request: Request) -> dict[str, Any]:
        active = get_service(request)
        return {
            "corpus_version": active.corpus.version,
            "document_count": len(active.corpus.documents),
            "chunk_count": len(active.corpus.chunks),
            "documents": active.corpus_documents(),
        }

    @app.post("/api/query")
    def query(payload: QueryRequest, request: Request) -> dict[str, Any]:
        active = get_service(request)
        try:
            response = active.query(
                payload.query,
                use_llm=payload.use_llm,
                top_k=payload.top_k,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception("Unhandled query pipeline error")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "query_pipeline_error",
                    "message": "The query pipeline failed. Check the backend log for details.",
                    "type": type(exc).__name__,
                },
            ) from exc
        return response.to_dict()

    @app.exception_handler(404)
    async def not_found(request: Request, exc: HTTPException) -> JSONResponse:
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "detail": str(exc.detail)},
            )
        return JSONResponse(status_code=404, content={"error": "not_found"})

    frontend_dist = Path(find_project_root()) / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


app = create_app()
