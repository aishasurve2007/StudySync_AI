"""Productivity score endpoint (spec §8)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.focus import ProductivityScore
from app.services.productivity import compute_productivity

router = APIRouter(prefix="/productivity", tags=["productivity"])


@router.get("/score", response_model=ProductivityScore)
def get_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductivityScore:
    return ProductivityScore(**compute_productivity(db, current_user))
