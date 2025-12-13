"""
Tests for integration services (Slack, Notion, Email)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.services.integrations.slack_service import SlackService
from src.services.integrations.notion_service import NotionService


class TestSlackService:
    """Tests for Slack integration"""
    
    @pytest.fixture
    def slack_service(self):
        """Create Slack service with mocked client"""
        with patch('src.services.integrations.slack_service.WebClient') as mock_client:
            service = SlackService()
            service.client = Mock()
            return service
    
    @pytest.mark.asyncio
    async def test_send_competitor_alert(self, slack_service):
        """Test sending competitor update alert"""
        slack_service.client.chat_postMessage.return_value = {'ts': '1234567890'}
        
        update = {
            'id': 1,
            'title': 'Competitor X Price Change',
            'update_type': 'pricing',
            'impact_score': 8,
            'severity': 'high',
            'summary': 'Competitor increased prices by 20%',
            'source_url': 'https://competitor.com/pricing'
        }
        
        result = await slack_service.send_competitor_alert(update)
        
        assert result is True
        slack_service.client.chat_postMessage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_competitor_alert_failure(self, slack_service):
        """Test handling Slack API error"""
        from slack_sdk.errors import SlackApiError
        slack_service.client.chat_postMessage.side_effect = SlackApiError(
            message="channel_not_found",
            response={'error': 'channel_not_found'}
        )
        
        update = {
            'id': 1,
            'title': 'Test Update',
            'update_type': 'pricing',
            'impact_score': 5,
            'severity': 'medium',
            'summary': 'Test summary'
        }
        
        result = await slack_service.send_competitor_alert(update)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_incident_alert(self, slack_service):
        """Test sending incident alert"""
        slack_service.client.chat_postMessage.return_value = {'ts': '1234567890'}
        
        incident = {
            'title': 'Database Connection Error',
            'severity': 'critical',
            'status': 'investigating',
            'root_cause': 'Connection pool exhausted'
        }
        
        result = await slack_service.send_incident_alert(incident)
        
        assert result is True
        slack_service.client.chat_postMessage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_weekly_digest(self, slack_service):
        """Test sending weekly digest"""
        slack_service.client.chat_postMessage.return_value = {'ts': '1234567890'}
        
        digest = {
            'summary': 'Key competitive intelligence highlights this week',
            'total_updates': 25,
            'high_priority_count': 5,
            'top_updates': [
                {'title': 'Competitor A new feature', 'impact_score': 9},
                {'title': 'Competitor B price drop', 'impact_score': 8}
            ]
        }
        
        result = await slack_service.send_weekly_digest(digest)
        
        assert result is True


class TestNotionService:
    """Tests for Notion integration"""
    
    @pytest.fixture
    def notion_service(self):
        """Create Notion service with mocked client"""
        with patch('src.services.integrations.notion_service.Client') as mock_client:
            service = NotionService()
            service.client = Mock()
            return service
    
    @pytest.mark.asyncio
    async def test_create_battlecard_page(self, notion_service):
        """Test creating new battlecard page"""
        notion_service.client.pages.create.return_value = {
            'id': 'page-id-123',
            'url': 'https://notion.so/page-id-123'
        }
        
        battlecard = {
            'title': 'Competitor X Battlecard',
            'competitor_name': 'Competitor X',
            'is_published': True,
            'overview': 'Key competitor in enterprise space',
            'strengths': ['Strong brand', 'Large customer base'],
            'weaknesses': ['Slow innovation', 'Poor support'],
            'kill_points': ['We have better pricing', 'Faster implementation']
        }
        
        result = await notion_service.create_battlecard_page(battlecard)
        
        assert 'page_id' in result
        assert 'url' in result
        notion_service.client.pages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_battlecard_page(self, notion_service):
        """Test updating existing battlecard page"""
        notion_service.client.pages.update.return_value = {
            'id': 'existing-page-id',
            'url': 'https://notion.so/existing-page-id'
        }
        
        battlecard = {
            'title': 'Updated Battlecard',
            'competitor_name': 'Competitor X',
            'is_published': True,
            'notion_page_id': 'existing-page-id',
            'overview': 'Updated overview'
        }
        
        result = await notion_service.create_battlecard_page(battlecard)
        
        assert 'page_id' in result
        notion_service.client.pages.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_battlecard_page(self, notion_service):
        """Test retrieving battlecard page"""
        notion_service.client.pages.retrieve.return_value = {
            'id': 'page-id-123',
            'properties': {'Name': {'title': [{'text': {'content': 'Test Battlecard'}}]}}
        }
        
        result = await notion_service.get_battlecard_page('page-id-123')
        
        assert 'id' in result
        notion_service.client.pages.retrieve.assert_called_once_with(page_id='page-id-123')
    
    @pytest.mark.asyncio
    async def test_list_battlecards(self, notion_service):
        """Test listing all battlecards"""
        notion_service.client.databases.query.return_value = {
            'results': [
                {'id': 'page-1', 'properties': {}},
                {'id': 'page-2', 'properties': {}}
            ]
        }
        
        result = await notion_service.list_battlecards()
        
        assert len(result) == 2
        notion_service.client.databases.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_battlecard_page_error(self, notion_service):
        """Test handling Notion API error"""
        notion_service.client.pages.create.side_effect = Exception("API Error")
        
        battlecard = {
            'title': 'Test Battlecard',
            'competitor_name': 'Test',
            'is_published': False
        }
        
        result = await notion_service.create_battlecard_page(battlecard)
        
        assert result == {}
