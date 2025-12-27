"""
Slack integration service

Enhanced with:
- Circuit breaker for fault tolerance
- Graceful degradation when Slack is down
- Request context for logging
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, List, Optional
from loguru import logger
from src.core.config import settings
from src.core.circuit_breaker import with_circuit_breaker, CircuitBreakerOpenError, CIRCUIT_BREAKERS
from src.core.request_context import log_info, log_error, log_warning


class SlackService:
    """
    Slack notification and bot service.
    
    Protected by circuit breaker to prevent cascading failures
    when Slack API is unavailable.
    """
    
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN) if settings.SLACK_BOT_TOKEN else None
        self.channel_id = settings.SLACK_CHANNEL_ID
        self._enabled = bool(settings.SLACK_BOT_TOKEN and settings.SLACK_CHANNEL_ID)
        
        if not self._enabled:
            logger.warning("Slack integration disabled - missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID")
    
    def is_enabled(self) -> bool:
        """Check if Slack integration is properly configured"""
        return self._enabled
    
    def is_healthy(self) -> bool:
        """Check if Slack circuit breaker is closed (healthy)"""
        breaker = CIRCUIT_BREAKERS.get("slack_api")
        if breaker:
            return breaker.state.value == "closed"
        return True
    
    @with_circuit_breaker("slack_api")
    async def send_competitor_alert(self, update: Dict) -> bool:
        """
        Send competitor update alert to Slack.
        
        Protected by circuit breaker - will fail fast if Slack is down.
        """
        if not self._enabled:
            log_warning("Slack not configured, skipping alert", update_id=update.get('id'))
            return False
        
        try:
            # Format message
            severity_emoji = {
                'critical': '🚨',
                'high': '⚠️',
                'medium': '📊',
                'low': 'ℹ️'
            }
            
            emoji = severity_emoji.get(update.get('severity', 'low'), 'ℹ️')
            
            message = {
                "channel": self.channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} Competitor Update: {update['title']}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Type:*\n{update['update_type']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Impact Score:*\n{update['impact_score']}/10"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Summary:*\n{update['summary']}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Details"
                                },
                                "url": update.get('source_url', '#')
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "👍 Verified"
                                },
                                "value": f"verify_{update['id']}"
                            }
                        ]
                    }
                ]
            }
            
            response = self.client.chat_postMessage(**message)
            log_info(f"Slack alert sent", ts=response['ts'], update_type=update['update_type'])
            return True
            
        except SlackApiError as e:
            log_error(f"Slack API error: {e.response['error']}")
            raise  # Let circuit breaker track this
    
    @with_circuit_breaker("slack_api")
    async def send_incident_alert(self, incident: Dict) -> bool:
        """Send system incident alert to Slack"""
        if not self._enabled:
            return False
        
        try:
            message = {
                "channel": self.channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🔴 System Incident: {incident['title']}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:*\n{incident['severity'].upper()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{incident['status']}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Root Cause:*\n{incident.get('root_cause', 'Investigating...')}"
                        }
                    }
                ]
            }
            
            response = self.client.chat_postMessage(**message)
            log_info(f"Incident alert sent", ts=response['ts'], severity=incident['severity'])
            return True
            
        except SlackApiError as e:
            log_error(f"Slack API error: {e.response['error']}")
            raise
    
    @with_circuit_breaker("slack_api")
    async def send_weekly_digest(self, digest: Dict) -> bool:
        """Send weekly summary digest"""
        if not self._enabled:
            return False
        
        try:
            message = {
                "channel": self.channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📈 Weekly Competitive Intelligence Digest"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Key Highlights:*\n{digest['summary']}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Updates:*\n{digest['total_updates']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*High Priority:*\n{digest['high_priority_count']}"
                            }
                        ]
                    }
                ]
            }
            
            # Add top updates
            if digest.get('top_updates'):
                for update in digest['top_updates'][:5]:
                    message['blocks'].append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• *{update['title']}* - Impact: {update['impact_score']}/10"
                        }
                    })
            
            response = self.client.chat_postMessage(**message)
            log_info(f"Weekly digest sent", ts=response['ts'], total_updates=digest['total_updates'])
            return True
            
        except SlackApiError as e:
            log_error(f"Slack API error: {e.response['error']}")
            raise
    
    @with_circuit_breaker("slack_api")
    async def send_message(self, channel: str, text: str, blocks: Optional[List] = None) -> Optional[Dict]:
        """
        Send a generic message to Slack.
        
        Args:
            channel: Channel ID to send to
            text: Fallback text
            blocks: Optional Block Kit blocks
            
        Returns:
            Slack API response or None if failed
        """
        if not self._enabled:
            return None
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            log_error(f"Slack API error: {e.response['error']}")
            raise
    
    @with_circuit_breaker("slack_api")
    async def send_interactive_message(
        self,
        channel: str,
        blocks: List,
        text: str = "Interactive message"
    ) -> Optional[Dict]:
        """
        Send interactive message with buttons/inputs.
        
        Args:
            channel: Channel ID
            blocks: Block Kit blocks with actions
            text: Fallback text
            
        Returns:
            Slack API response
        """
        if not self._enabled:
            return None
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            log_error(f"Slack API error: {e.response['error']}")
            raise
    
    async def test_connection(self) -> Dict:
        """
        Test Slack connection and return status.
        
        Returns:
            Dict with connection status and details
        """
        if not self._enabled:
            return {
                "connected": False,
                "error": "Slack not configured - missing credentials",
                "circuit_breaker": "n/a"
            }
        
        try:
            response = self.client.auth_test()
            return {
                "connected": True,
                "team": response.get("team"),
                "user": response.get("user"),
                "channel_configured": bool(self.channel_id),
                "circuit_breaker": "healthy" if self.is_healthy() else "open"
            }
        except SlackApiError as e:
            return {
                "connected": False,
                "error": e.response['error'],
                "circuit_breaker": "healthy" if self.is_healthy() else "open"
            }


# Singleton instance
_slack_instance: Optional[SlackService] = None


def get_slack_service() -> SlackService:
    """Get or create Slack service instance"""
    global _slack_instance
    if _slack_instance is None:
        _slack_instance = SlackService()
    return _slack_instance
