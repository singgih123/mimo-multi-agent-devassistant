"""FastAPI server exposing the multi-agent pipeline as a REST API."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mimo_agents.agents.orchestrator import OrchestratorAgent
from mimo_agents.agents.reviewer import ReviewerAgent
from mimo_agents.core.client import MiMoClient
from mimo_agents.core.config import Settings
from mimo_agents.core.models import DevTask

_client: MiMoClient | None = None
_orchestrator: OrchestratorAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _client, _orchestrator
    settings = Settings.from_env()
    errors = settings.validate()
    if errors:
        raise RuntimeError(f"Configuration errors: {'; '.join(errors)}")
    _client = MiMoClient(settings)
    _orchestrator = OrchestratorAgent(_client)
    yield
    _client = None
    _orchestrator = None


app = FastAPI(
    title="MiMo Multi-Agent DevAssistant API",
    description="REST API for the multi-agent AI development pipeline powered by Xiaomi MiMo V2.5",
    version="0.1.0",
    lifespan=lifespan,
)


class PipelineRequest(BaseModel):
    title: str = Field(default="Dev Task", description="Task title")
    description: str = Field(..., description="Task description")
    language: str = Field(default="python", description="Programming language")
    source_code: str = Field(default="", description="Existing source code")


class ReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review")
    language: str = Field(default="python", description="Programming language")
    description: str = Field(default="", description="Additional context")


class PipelineResponse(BaseModel):
    task_id: str
    status: str
    output: str
    artifacts: dict[str, str]
    total_tokens: int
    duration_ms: int


class UsageResponse(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class HealthResponse(BaseModel):
    status: str
    version: str
    models: dict[str, str]


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = Settings.from_env()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        models={
            "reasoning": settings.reasoning_model.model_id,
            "multimodal": settings.multimodal_model.model_id,
            "tts": settings.tts_model.model_id,
        },
    )


@app.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    task = DevTask(
        title=req.title,
        description=req.description,
        language=req.language,
        source_code=req.source_code,
    )

    result = _orchestrator.process(task)

    return PipelineResponse(
        task_id=result.task_id,
        status=result.status.value,
        output=result.output,
        artifacts=result.artifacts,
        total_tokens=result.token_usage.total_tokens,
        duration_ms=result.duration_ms,
    )


@app.post("/review", response_model=PipelineResponse)
async def review_code(req: ReviewRequest) -> PipelineResponse:
    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    task = DevTask(
        title="Code Review",
        description=req.description or "Review the code for quality and best practices.",
        language=req.language,
        source_code=req.code,
    )

    reviewer = ReviewerAgent(_client)
    result = reviewer.process(task, context={"generated_code": req.code})

    return PipelineResponse(
        task_id=result.task_id,
        status=result.status.value,
        output=result.output,
        artifacts=result.artifacts,
        total_tokens=result.token_usage.total_tokens,
        duration_ms=result.duration_ms,
    )


@app.get("/usage", response_model=UsageResponse)
async def get_usage() -> UsageResponse:
    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    usage = _client.get_total_usage()
    return UsageResponse(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )
