"""
Competitor management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.competitor import Competitor, CompetitorUpdate
from src.services.scrapers.web_scraper import PricingScraper, CareersScraper, ContentScraper
from src.services.ai.processor import AIProcessor

router = APIRouter()


class CompetitorCreate(BaseModel):
    name: str
    domain: str
    description: str = ""
    industry: str = ""
    pricing_url: str = ""
    careers_url: str = ""
    blog_url: str = ""


class CompetitorResponse(BaseModel):
    id: int
    name: str
    domain: str
    description: str
    industry: str
    is_active: bool
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CompetitorResponse)
async def create_competitor(
    competitor: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new competitor to monitor"""
    new_competitor = Competitor(**competitor.model_dump())
    db.add(new_competitor)
    await db.commit()
    await db.refresh(new_competitor)
    
    return new_competitor


@router.get("/", response_model=List[CompetitorResponse])
async def list_competitors(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all competitors"""
    result = await db.execute(select(Competitor).where(Competitor.is_active == True))
    competitors = result.scalars().all()
    return competitors


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get competitor details"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    return competitor


@router.post("/{competitor_id}/scrape")
async def trigger_scrape(
    competitor_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Trigger manual scrape for competitor"""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Add scraping task to background
    background_tasks.add_task(scrape_competitor_data, competitor_id, db)
    
    return {"message": "Scraping initiated", "competitor_id": competitor_id}


async def scrape_competitor_data(competitor_id: int, db: AsyncSession):
    """Background task to scrape competitor data"""
    from loguru import logger
    
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        return
    
    logger.info(f"Starting scrape for {competitor.name}")
    
    # Initialize scrapers
    pricing_scraper = PricingScraper()
    careers_scraper = CareersScraper()
    content_scraper = ContentScraper()
    ai_processor = AIProcessor()
    
    # Scrape pricing
    if competitor.pricing_url:
        pricing_data = pricing_scraper.scrape_pricing(competitor.pricing_url)
        if pricing_data.get('plans'):
            # Create update record
            update = CompetitorUpdate(
                competitor_id=competitor_id,
                update_type='pricing',
                category='pricing',
                title=f"Pricing data scraped for {competitor.name}",
                summary=f"Found {len(pricing_data['plans'])} pricing plans",
                source_url=competitor.pricing_url,
                raw_data=pricing_data,
                impact_score=5.0
            )
            db.add(update)
    
    # Scrape careers
    if competitor.careers_url:
        careers_data = careers_scraper.scrape_careers(competitor.careers_url)
        if careers_data.get('job_postings'):
            analysis = await ai_processor.analyze_hiring_trends(careers_data)
            
            update = CompetitorUpdate(
                competitor_id=competitor_id,
                update_type='hiring',
                category='strategy',
                title=f"Hiring update for {competitor.name}",
                summary=analysis.get('strategic_direction', 'Hiring data collected'),
                source_url=competitor.careers_url,
                raw_data=careers_data,
                impact_score=analysis.get('impact_score', 5.0)
            )
            db.add(update)
    
    # Scrape blog
    if competitor.blog_url:
        blog_data = content_scraper.scrape_blog(competitor.blog_url)
        if blog_data.get('articles'):
            for article in blog_data['articles'][:3]:  # Process top 3 articles
                analysis = await ai_processor.summarize_content_change(article)
                
                update = CompetitorUpdate(
                    competitor_id=competitor_id,
                    update_type='content',
                    category=analysis.get('category', 'thought_leadership'),
                    title=article.get('title', 'Content update'),
                    summary=analysis.get('takeaway', ''),
                    source_url=article.get('link', competitor.blog_url),
                    raw_data=article,
                    impact_score=analysis.get('impact_score', 3.0)
                )
                db.add(update)
    
    await db.commit()
    logger.info(f"Completed scrape for {competitor.name}")
