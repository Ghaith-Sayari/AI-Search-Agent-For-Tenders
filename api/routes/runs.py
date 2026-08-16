"""Run management API routes."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.schemas.runs import CreateRunRequest, PipelineRun
from api.services.run_service import create_run, execute_run, get_run, list_runs

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get("", response_model=list[PipelineRun])
async def get_runs() -> list[PipelineRun]:
    return list_runs()


@router.get("/{run_id}", response_model=PipelineRun)
async def get_run_by_id(run_id: str) -> PipelineRun:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run


@router.post("", response_model=PipelineRun)
async def post_run(
    payload: CreateRunRequest,
    background_tasks: BackgroundTasks,
) -> PipelineRun:
    run = create_run(payload)
    background_tasks.add_task(execute_run, run.id, payload)
    return run
