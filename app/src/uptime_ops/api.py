from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from uptime_ops.db import get_db, init_db
from uptime_ops.metrics import render
from uptime_ops.models import Check, Target

DASHBOARD = Path(__file__).parent / "templates" / "dashboard.html"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="uptime-ops", version="0.1.0", lifespan=lifespan)


class TargetIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: HttpUrl


class TargetOut(BaseModel):
    id: int
    name: str
    url: str
    last_status: str
    last_latency_ms: float | None
    last_status_code: int | None
    consecutive_failures: int
    alerted: bool

    model_config = {"from_attributes": True}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    body, content_type = render()
    return Response(content=body, media_type=content_type)


@app.post("/targets", response_model=TargetOut, status_code=201)
def create_target(payload: TargetIn, db: Session = Depends(get_db)) -> Target:
    url = str(payload.url)
    if db.query(Target).filter(Target.url == url).first():
        raise HTTPException(status_code=409, detail="URL already monitored")
    target = Target(name=payload.name, url=url)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@app.get("/targets", response_model=list[TargetOut])
def list_targets(db: Session = Depends(get_db)) -> list[Target]:
    return db.query(Target).order_by(Target.id.desc()).all()


@app.get("/targets/{target_id}", response_model=TargetOut)
def get_target(target_id: int, db: Session = Depends(get_db)) -> Target:
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="not found")
    return target


@app.get("/targets/{target_id}/checks")
def list_checks(target_id: int, db: Session = Depends(get_db), limit: int = 50) -> list[dict]:
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="not found")
    rows = (
        db.query(Check)
        .filter(Check.target_id == target_id)
        .order_by(Check.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "up": row.up,
            "status_code": row.status_code,
            "latency_ms": row.latency_ms,
            "error": row.error,
            "checked_at": row.checked_at.isoformat() if row.checked_at else None,
        }
        for row in rows
    ]


@app.delete("/targets/{target_id}", status_code=204)
def delete_target(target_id: int, db: Session = Depends(get_db)) -> None:
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(target)
    db.commit()
