"""
Celery tasks for background processing
"""
from src.services.celery_app import celery_app
from loguru import logger


@celery_app.task(name="scrape_all_competitors")
def scrape_all_competitors():
    """Periodic task to scrape all active competitors"""
    from src.core.database import AsyncSessionLocal
    from src.models.competitor import Competitor
    from sqlalchemy import select
    import asyncio
    
    async def _scrape():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Competitor).where(Competitor.is_active == True))
            competitors = result.scalars().all()
            
            logger.info(f"Starting scrape for {len(competitors)} competitors")
            
            for competitor in competitors:
                from src.api.v1.endpoints.competitors import scrape_competitor_data
                await scrape_competitor_data(competitor.id, db)
    
    asyncio.run(_scrape())
    logger.info("Completed scraping all competitors")


@celery_app.task(name="generate_weekly_digest")
def generate_weekly_digest():
    """Generate and send weekly competitive intelligence digest"""
    from src.core.database import AsyncSessionLocal
    from src.models.competitor import CompetitorUpdate
    from src.services.integrations.slack_service import SlackService
    from sqlalchemy import select
    from datetime import datetime, timedelta
    import asyncio
    
    async def _generate():
        async with AsyncSessionLocal() as db:
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            result = await db.execute(
                select(CompetitorUpdate)
                .where(CompetitorUpdate.created_at >= week_ago)
                .order_by(CompetitorUpdate.impact_score.desc())
            )
            updates = result.scalars().all()
            
            high_priority = [u for u in updates if u.impact_score >= 7.0]
            
            digest = {
                'summary': f"This week: {len(updates)} competitor updates tracked",
                'total_updates': len(updates),
                'high_priority_count': len(high_priority),
                'top_updates': [
                    {
                        'title': u.title,
                        'impact_score': u.impact_score
                    } for u in updates[:10]
                ]
            }
            
            slack_service = SlackService()
            await slack_service.send_weekly_digest(digest)
    
    asyncio.run(_generate())
    logger.info("Weekly digest generated and sent")


@celery_app.task(name="monitor_system_logs")
def monitor_system_logs():
    """Monitor and analyze system logs for anomalies"""
    from src.services.ai.logbert import LogAnomalyDetector
    import os
    
    detector = LogAnomalyDetector()
    
    # Read recent logs
    log_file = "logs/vigilai_*.log"
    try:
        # Read last 100 lines from log file
        # Implementation would read actual log files
        logs = []
        
        if logs:
            analysis = detector.analyze_log_sequence(logs)
            
            if analysis['severity'] in ['critical', 'high']:
                logger.warning(f"Detected {analysis['anomaly_count']} anomalies with {analysis['severity']} severity")
        
    except Exception as e:
        logger.error(f"Error monitoring logs: {str(e)}")


# Periodic task schedule
celery_app.conf.beat_schedule = {
    'scrape-competitors-every-4-hours': {
        'task': 'scrape_all_competitors',
        'schedule': 4 * 60 * 60,  # 4 hours
    },
    'weekly-digest': {
        'task': 'generate_weekly_digest',
        'schedule': 7 * 24 * 60 * 60,  # 7 days
    },
    'monitor-logs-every-15-minutes': {
        'task': 'monitor_system_logs',
        'schedule': 15 * 60,  # 15 minutes
    },
}
