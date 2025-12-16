"""
Competitor management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
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


class CompetitorUpdateResponse(BaseModel):
    id: int
    competitor_id: int
    update_type: str
    category: Optional[str]
    title: str
    summary: Optional[str]
    impact_score: float
    source_url: Optional[str]
    created_at: object  # Using object to handle datetime serialization automatically
    
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


    return competitor


@router.get("/{competitor_id}/updates", response_model=List[CompetitorUpdateResponse])
async def list_competitor_updates(
    competitor_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get updates for a competitor"""
    # Verify competitor exists
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Competitor not found")
        
    # Get updates
    result = await db.execute(
        select(CompetitorUpdate)
        .where(CompetitorUpdate.competitor_id == competitor_id)
        .order_by(CompetitorUpdate.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


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


from src.services.integrations.google_news_service import get_news_service
from src.services.social.social_monitor import SocialMediaMonitor
from src.services.seo.seo_tracker import SEOTracker
from src.services.integrations.job_boards import JobBoardAggregator
from src.services.integrations.reviews import ReviewMonitor
from src.services.integrations.slack_service import SlackService # Import Slack
from src.core.config import settings # Check settings

async def scrape_competitor_data(competitor_id: int, db: AsyncSession):
    """Background task to scrape competitor data"""
    from loguru import logger
    
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    
    if not competitor:
        return
    
    logger.info(f"Starting scrape for {competitor.name}")
    
    # Initialize scrapers & integrations
    ai_processor = AIProcessor()
    slack_service = SlackService()
    
    # helper for alerting
    async def save_and_alert(update_obj: CompetitorUpdate):
        db.add(update_obj)
        # Alert if high impact or critical category
        if update_obj.impact_score >= 7.0 or update_obj.category in ['acquisition', 'funding', 'pricing']:
            await slack_service.send_competitor_alert(
                {
                    'id': str(competitor_id),
                    'title': update_obj.title,
                    'summary': update_obj.summary,
                    'update_type': update_obj.update_type,
                    'impact_score': update_obj.impact_score,
                    'source_url': update_obj.source_url,
                    'severity': 'critical' if update_obj.impact_score >= 8 else 'high'
                }
            )

    # 1. Web Scrapers (Core)
    try:
        if competitor.pricing_url:
            pricing_scraper = PricingScraper()
            pricing_data = pricing_scraper.scrape_pricing(competitor.pricing_url)
            if pricing_data.get('plans'):
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
                await save_and_alert(update)

        if competitor.careers_url:
            careers_scraper = CareersScraper()
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
                await save_and_alert(update)

        if competitor.blog_url:
            content_scraper = ContentScraper()
            blog_data = content_scraper.scrape_blog(competitor.blog_url)
            if blog_data.get('articles'):
                for article in blog_data['articles'][:3]:
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
                    await save_and_alert(update)
    except Exception as e:
        logger.error(f"Error in web scraping for {competitor.name}: {e}")

    # 2. News Monitoring
    try:
        news_service = get_news_service()
        # Perplexity removed, using free Google News aggregator
        news_results = news_service.get_comprehensive_news(competitor.name)
        
        if news_results.get('articles'):
            for article in news_results['articles'][:3]: # Top 3 news
                # Cheap impact score heuristic based on category
                impact = 7.0 if article.get('category') in ['funding', 'product', 'acquisition'] else 4.0
                update = CompetitorUpdate(
                    competitor_id=competitor_id,
                    update_type='news',
                    category=article.get('category', 'general'),
                    title=article.get('title', 'News Update'),
                    summary=article.get('snippet', 'News detected'),
                    source_url=article.get('url'),
                    raw_data=article,
                    impact_score=impact
                )
                await save_and_alert(update)
    except Exception as e:
        logger.error(f"Error in news monitoring for {competitor.name}: {e}")

    # 3. Social Media Monitoring (Twitter/LinkedIn)
    try:
        social_monitor = SocialMediaMonitor()
        # Find handles from extra_data or heuristic
        twitter_handle = competitor.extra_data.get('twitter_handle') if competitor.extra_data else None
        
        if twitter_handle:
            social_data = social_monitor.monitor_competitor(competitor.name, twitter_handle=twitter_handle)
            # Log high engagement posts as updates
            for post in social_data.get('high_engagement_posts', [])[:2]:
                update = CompetitorUpdate(
                    competitor_id=competitor_id,
                    update_type='social',
                    category=post.get('post_type', 'general'),
                    title=f"High engagement on {post.get('platform', 'Social')}",
                    summary=post.get('content', '')[:200],
                    source_url=post.get('url'),
                    raw_data=post,
                    impact_score=6.0
                )
                db.add(update)
    except Exception as e:
        logger.error(f"Error in social monitoring for {competitor.name}: {e}")

    # 4. Job Board APIs (Greenhouse/Lever)
    try:
        job_aggregator = JobBoardAggregator()
        # Heuristic: use domain slug as potential board token (e.g. stripe.com -> stripe)
        company_slug = competitor.domain.split('.')[0] 
        jobs = job_aggregator.fetch_company_jobs(company_slug)
        
        if jobs:
             # Just log a summary update for now
             update = CompetitorUpdate(
                competitor_id=competitor_id,
                update_type='hiring',
                category='growth',
                title=f"Active Job Listings ({len(jobs)})",
                summary=f"Found {len(jobs)} active roles strategies include {jobs[0].get('department')} emphasis.",
                source_url=jobs[0].get('url'), # Link to first job
                raw_data={'total_jobs': len(jobs), 'sample': jobs[:5]},
                impact_score=5.0
            )
             db.add(update)
    except Exception as e:
        logger.error(f"Error in job board monitoring for {competitor.name}: {e}")

    # 5. Reviews (G2/Gartner)
    try:
        review_monitor = ReviewMonitor()
        review_data = review_monitor.monitor_competitor(competitor.name)
        if review_data.get('reviews'):
            for review in review_data['reviews'][:2]:
                 update = CompetitorUpdate(
                    competitor_id=competitor_id,
                    update_type='reviews',
                    category='market_sentiment',
                    title=review.get('title'),
                    summary=review.get('summary'),
                    source_url=review.get('url'),
                    raw_data=review,
                    impact_score=6.0
                )
                 db.add(update)
    except Exception as e:
        logger.error(f"Error in review monitoring for {competitor.name}: {e}")

    # 6. SEO Tracking
    try:
        seo_tracker = SEOTracker()
        # Track domain for generic terms
        keywords = [f"{competitor.name} pricing", f"{competitor.name} alternatives", competitor.industry]
        rankings = seo_tracker.track_keyword_rankings(keywords, [competitor.domain])
        
        if rankings:
            top_rank = next((r for r in rankings if r.position and r.position <= 3), None)
            if top_rank:
                 update = CompetitorUpdate(
                    competitor_id=competitor_id,
                    update_type='seo',
                    category='market_visibility',
                    title=f"Top ranking for '{top_rank.keyword}'",
                    summary=f"Ranks #{top_rank.position} for high value keyword.",
                    source_url=top_rank.url,
                    raw_data=top_rank.to_dict(),
                    impact_score=4.0
                )
                 db.add(update)
    except Exception as e:
        logger.error(f"Error in SEO tracking for {competitor.name}: {e}")
    
    await db.commit()
    logger.info(f"Completed full scraping cycle for {competitor.name}")
