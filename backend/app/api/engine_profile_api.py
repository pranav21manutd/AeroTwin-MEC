from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict
from app.engine_profile_store import engine_profiles

router = APIRouter(prefix="/api/engine", tags=["Engine configuration"])


class EngineSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    engine_id: str


@router.get("/profiles")
async def list_profiles():
    return engine_profiles.catalog()


@router.get("/profile/{engine_id}/yaml", response_class=PlainTextResponse)
async def get_profile_yaml(engine_id: str):
    try:
        return PlainTextResponse(engine_profiles.raw_yaml(engine_id), media_type="text/yaml",
                                 headers={"Cache-Control": "no-store"})
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown engine profile")


@router.post("/select")
async def select_profile(selection: EngineSelection):
    try:
        metadata = engine_profiles.select(selection.engine_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown engine profile")
    return {"active_engine_id": metadata["engine_id"], "engine_meta": metadata,
            "switch_latency_ms": metadata["switch_latency_ms"]}
