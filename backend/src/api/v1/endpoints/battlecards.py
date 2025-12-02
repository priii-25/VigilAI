"""
Battlecard management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.battlecard import Battlecard

router = APIRouter()


class BattlecardResponse(BaseModel):
    id: int
    competitor_id: int
    title: str
    overview: str
    strengths: List[str]
    weaknesses: List[str]
    objection_handling: List[dict]
    kill_points: List[str]
    is_published: bool
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[BattlecardResponse])
async def list_battlecards(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all battlecards"""
    result = await db.execute(select(Battlecard).where(Battlecard.is_published == True))
    battlecards = result.scalars().all()
    return battlecards


@router.get("/{battlecard_id}", response_model=BattlecardResponse)
async def get_battlecard(
    battlecard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get battlecard details"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    return battlecard


@router.get("/competitor/{competitor_id}", response_model=BattlecardResponse)
async def get_battlecard_by_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get battlecard for specific competitor"""
    result = await db.execute(
        select(Battlecard)
        .where(Battlecard.competitor_id == competitor_id)
        .where(Battlecard.is_published == True)
        .order_by(Battlecard.version.desc())
    )
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found for this competitor")
    
    return battlecard


@router.post("/{battlecard_id}/publish")
async def publish_battlecard(
    battlecard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publish battlecard"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    battlecard.is_published = True
    await db.commit()
    
    return {"message": "Battlecard published successfully"}
