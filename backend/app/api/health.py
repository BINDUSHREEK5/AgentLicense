"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.models import HealthCheck
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""

    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthCheck(
        status="ok",
        environment=settings.app_env,
        database=db_ok,
        algorand=settings.x402_configured,
        demo_mode=not settings.x402_configured,
    )