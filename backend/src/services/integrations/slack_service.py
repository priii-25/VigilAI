"""
Slack integration service
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, List
from loguru import logger
from src.core.config import settings


class SlackService:
    """Slack notification and bot service"""
    
    def __init__(self):
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        self.channel_id = settings.SLACK_CHANNEL_ID
    
    async def send_competitor_alert(self, update: Dict) -> bool:
        """Send competitor update alert to Slack"""
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
            logger.info(f"Slack alert sent: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
    
    async def send_incident_alert(self, incident: Dict) -> bool:
        """Send system incident alert to Slack"""
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
            logger.info(f"Incident alert sent: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
    
    async def send_weekly_digest(self, digest: Dict) -> bool:
        """Send weekly summary digest"""
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
            logger.info(f"Weekly digest sent: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
