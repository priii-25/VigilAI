"""
Notion integration service for battlecard management
"""
from notion_client import Client
from typing import Dict, List
from loguru import logger
from src.core.config import settings


class NotionService:
    """Notion integration for battlecard publishing"""
    
    def __init__(self):
        self.client = Client(auth=settings.NOTION_API_KEY)
        self.database_id = settings.NOTION_DATABASE_ID
    
    async def create_battlecard_page(self, battlecard: Dict) -> Dict:
        """Create or update battlecard page in Notion"""
        try:
            # Prepare page properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": battlecard['title']
                            }
                        }
                    ]
                },
                "Competitor": {
                    "rich_text": [
                        {
                            "text": {
                                "content": battlecard.get('competitor_name', '')
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": "Published" if battlecard.get('is_published') else "Draft"
                    }
                }
            }
            
            # Prepare page content
            children = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "Overview"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": battlecard.get('overview', '')}}]
                    }
                }
            ]
            
            # Add strengths
            if battlecard.get('strengths'):
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Strengths"}}]
                    }
                })
                
                for strength in battlecard['strengths']:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": strength}}]
                        }
                    })
            
            # Add weaknesses
            if battlecard.get('weaknesses'):
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Weaknesses"}}]
                    }
                })
                
                for weakness in battlecard['weaknesses']:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": weakness}}]
                        }
                    })
            
            # Add kill points
            if battlecard.get('kill_points'):
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Kill Points - Why We Win"}}]
                    }
                })
                
                for point in battlecard['kill_points']:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": point}}]
                        }
                    })
            
            # Create or update page
            if battlecard.get('notion_page_id'):
                # Update existing page
                response = self.client.pages.update(
                    page_id=battlecard['notion_page_id'],
                    properties=properties
                )
                logger.info(f"Updated Notion page: {response['id']}")
            else:
                # Create new page
                response = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                    children=children
                )
                logger.info(f"Created Notion page: {response['id']}")
            
            return {
                "page_id": response['id'],
                "url": response['url']
            }
            
        except Exception as e:
            logger.error(f"Notion API error: {str(e)}")
            return {}
    
    async def get_battlecard_page(self, page_id: str) -> Dict:
        """Retrieve battlecard page from Notion"""
        try:
            response = self.client.pages.retrieve(page_id=page_id)
            return response
        except Exception as e:
            logger.error(f"Error retrieving Notion page: {str(e)}")
            return {}
    
    async def list_battlecards(self) -> List[Dict]:
        """List all battlecard pages"""
        try:
            response = self.client.databases.query(database_id=self.database_id)
            return response.get('results', [])
        except Exception as e:
            logger.error(f"Error listing Notion pages: {str(e)}")
            return []
