"""
Battlecard management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.battlecard import Battlecard
from loguru import logger

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


class BattlecardCreate(BaseModel):
    """Schema for creating a battlecard"""
    competitor_id: int
    title: str
    overview: Optional[str] = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    objection_handling: List[dict] = []
    kill_points: List[str] = []


class BattlecardUpdate(BaseModel):
    """Schema for updating a battlecard"""
    title: Optional[str] = None
    overview: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    objection_handling: Optional[List[dict]] = None
    kill_points: Optional[List[str]] = None
    is_published: Optional[bool] = None


@router.get("/", response_model=List[BattlecardResponse])
async def list_battlecards(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all battlecards"""
    result = await db.execute(select(Battlecard).where(Battlecard.is_published == True))
    battlecards = result.scalars().all()
    return battlecards


@router.post("/", response_model=BattlecardResponse)
async def create_battlecard(
    battlecard_data: BattlecardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new battlecard"""
    battlecard = Battlecard(
        competitor_id=battlecard_data.competitor_id,
        title=battlecard_data.title,
        overview=battlecard_data.overview,
        strengths=battlecard_data.strengths,
        weaknesses=battlecard_data.weaknesses,
        objection_handling=battlecard_data.objection_handling,
        kill_points=battlecard_data.kill_points,
        is_published=False
    )
    
    db.add(battlecard)
    await db.commit()
    await db.refresh(battlecard)
    
    return battlecard


@router.put("/{battlecard_id}", response_model=BattlecardResponse)
async def update_battlecard(
    battlecard_id: int,
    battlecard_update: BattlecardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a battlecard"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
        
    update_data = battlecard_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(battlecard, field, value)
        
    await db.commit()
    await db.refresh(battlecard)
    
    return battlecard


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


@router.get("/{battlecard_id}/pdf")
async def download_battlecard_pdf(
    battlecard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download battlecard as PDF"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    try:
        from src.services.battlecards.pdf_generator import get_pdf_generator
        
        # Convert ORM model to dict for PDF generation
        battlecard_dict = {
            'title': battlecard.title,
            'competitor_name': battlecard.title,
            'overview': battlecard.overview,
            'strengths': battlecard.strengths or [],
            'weaknesses': battlecard.weaknesses or [],
            'kill_points': battlecard.kill_points or [],
            'objection_handlers': battlecard.objection_handling or [],
            'confidence_score': 'N/A',
            'updated_at': str(battlecard.updated_at) if hasattr(battlecard, 'updated_at') else 'N/A'
        }
        
        pdf_generator = get_pdf_generator()
        pdf_buffer = pdf_generator.generate_battlecard_pdf(battlecard_dict)
        
        filename = f"battlecard_{battlecard.title.replace(' ', '_').lower()}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ImportError as e:
        logger.error(f"PDF generation not available: {e}")
        raise HTTPException(
            status_code=500, 
            detail="PDF generation not available. Please install reportlab: pip install reportlab"
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


@router.get("/{battlecard_id}/personalize")
async def personalize_battlecard(
    battlecard_id: int,
    industry: str = Query(default="general", description="Industry for personalization"),
    use_case: Optional[str] = Query(default=None, description="Specific use case"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get personalized battlecard content for specific industry/use case"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    # Industry-specific personalization templates
    industry_context = {
        "healthcare": {
            "compliance_note": "HIPAA-compliant solution",
            "key_concerns": ["Data security", "Patient privacy", "Regulatory compliance"],
            "value_prop": "Healthcare-focused security and compliance"
        },
        "finance": {
            "compliance_note": "SOC 2 Type II certified",
            "key_concerns": ["Data encryption", "Audit trails", "Regulatory requirements"],
            "value_prop": "Enterprise-grade security for financial institutions"
        },
        "retail": {
            "compliance_note": "PCI DSS compliant",
            "key_concerns": ["Scalability", "Peak traffic handling", "Integration capabilities"],
            "value_prop": "Scalable solution for high-volume retail operations"
        },
        "technology": {
            "compliance_note": "Developer-friendly with extensive APIs",
            "key_concerns": ["API capabilities", "Integration flexibility", "Developer experience"],
            "value_prop": "Built for developers with comprehensive API support"
        },
        "general": {
            "compliance_note": "Enterprise-grade security",
            "key_concerns": ["Cost efficiency", "Ease of use", "Support quality"],
            "value_prop": "Comprehensive solution for all business needs"
        }
    }
    
    context = industry_context.get(industry.lower(), industry_context["general"])
    
    # Build personalized response
    personalized = {
        "id": battlecard.id,
        "title": battlecard.title,
        "industry": industry,
        "use_case": use_case,
        "overview": battlecard.overview,
        "strengths": battlecard.strengths or [],
        "weaknesses": battlecard.weaknesses or [],
        "kill_points": battlecard.kill_points or [],
        "objection_handling": battlecard.objection_handling or [],
        "personalization": {
            "compliance_note": context["compliance_note"],
            "key_concerns": context["key_concerns"],
            "industry_value_prop": context["value_prop"],
            "recommended_talking_points": [
                f"Address {concern} with our specialized features"
                for concern in context["key_concerns"]
            ]
        }
    }
    
    return personalized


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
    """Publish battlecard to Notion"""
    result = await db.execute(select(Battlecard).where(Battlecard.id == battlecard_id))
    battlecard = result.scalar_one_or_none()
    
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard not found")
    
    # Publish to Notion if configured
    try:
        from src.services.integrations.notion_service import NotionService
        notion = NotionService()
        
        battlecard_dict = {
            'title': battlecard.title,
            'competitor_name': battlecard.title,
            'is_published': True,
            'overview': battlecard.overview,
            'strengths': battlecard.strengths or [],
            'weaknesses': battlecard.weaknesses or [],
            'kill_points': battlecard.kill_points or []
        }
        
        result = await notion.create_battlecard_page(battlecard_dict)
        
        if result.get('page_id'):
            battlecard.notion_page_id = result['page_id']
    except Exception as e:
        logger.warning(f"Notion publish failed (continuing anyway): {e}")
    
    battlecard.is_published = True
    await db.commit()
    
    return {"message": "Battlecard published successfully"}

