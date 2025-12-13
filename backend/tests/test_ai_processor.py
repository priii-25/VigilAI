"""
Tests for AI processing service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.ai.processor import AIProcessor


class TestAIProcessor:
    """Tests for AI-powered data processing"""
    
    @pytest.fixture
    def processor(self):
        """Create AI processor instance"""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                return AIProcessor()
    
    @pytest.mark.asyncio
    async def test_analyze_pricing_change(self, processor):
        """Test pricing change analysis"""
        with patch.object(processor, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = '''
            {
                "summary": "Competitor increased pricing by 20%",
                "impact_score": 8.0,
                "recommended_action": "Emphasize our stable pricing",
                "talking_points": ["We offer better value", "No hidden fees"]
            }
            '''
            
            old_data = {'plans': [{'name': 'Basic', 'price': '$29'}]}
            new_data = {'plans': [{'name': 'Basic', 'price': '$35'}]}
            
            result = await processor.analyze_pricing_change(old_data, new_data)
            
            assert 'summary' in result
            assert 'impact_score' in result
            mock_gemini.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_hiring_trends(self, processor):
        """Test hiring trends analysis"""
        with patch.object(processor, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = '''
            {
                "strategic_direction": "Moving into AI/ML space",
                "new_capabilities": ["Machine Learning", "Data Science"],
                "impact_score": 7.0,
                "recommendations": ["Monitor their AI product launches"]
            }
            '''
            
            careers_data = {
                'job_postings': [
                    {'title': 'ML Engineer', 'department': 'AI'},
                    {'title': 'Data Scientist', 'department': 'AI'}
                ],
                'hiring_trends': {
                    'total_openings': 15,
                    'departments': {'AI': 10, 'Engineering': 5}
                }
            }
            
            result = await processor.analyze_hiring_trends(careers_data)
            
            assert 'strategic_direction' in result
            mock_gemini.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_battlecard_section(self, processor):
        """Test battlecard section generation"""
        with patch.object(processor, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = "Strong enterprise features, reliable uptime, good support"
            
            result = await processor.generate_battlecard_section(
                competitor_name="Competitor X",
                section_type="strengths",
                data={'customers': 1000, 'uptime': '99.9%'}
            )
            
            assert len(result) > 0
            mock_gemini.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_content_change(self, processor):
        """Test content change summarization"""
        with patch.object(processor, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = '''
            {
                "takeaway": "Competitor launching new enterprise tier",
                "implication": "May compete for our enterprise customers",
                "impact_score": 6.0,
                "category": "product_launch"
            }
            '''
            
            article_data = {
                'title': 'Enterprise Launch',
                'summary': 'New enterprise features announced',
                'date': '2023-10-15'
            }
            
            result = await processor.summarize_content_change(article_data)
            
            assert 'takeaway' in result
            assert 'category' in result
    
    @pytest.mark.asyncio
    async def test_detect_noise_small_tracking_change(self, processor):
        """Test noise detection for tracking code changes"""
        html_diff = '<script>gtm.push({"event": "pageview"})</script>'
        
        result = await processor.detect_noise(html_diff)
        
        # Small changes with tracking code should be noise
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_noise_substantive_change(self, processor):
        """Test noise detection for substantive changes"""
        with patch.object(processor, '_call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = "SUBSTANTIVE"
            
            html_diff = '''
            <div class="pricing">
                <h1>New Pricing</h1>
                <p>We are updating our pricing structure starting from...</p>
            ''' * 100  # Make it large enough to trigger AI check
            
            result = await processor.detect_noise(html_diff)
            
            assert result is False
    
    def test_format_pricing(self, processor):
        """Test pricing data formatting"""
        data = {
            'plans': [
                {'name': 'Basic', 'price': '$29/mo'},
                {'name': 'Pro', 'price': '$99/mo'}
            ]
        }
        
        result = processor._format_pricing(data)
        
        assert 'Basic' in result
        assert '$29/mo' in result
    
    def test_format_pricing_empty(self, processor):
        """Test formatting with no pricing data"""
        data = {'plans': []}
        
        result = processor._format_pricing(data)
        
        assert result == "No pricing data available"
    
    def test_format_jobs(self, processor):
        """Test job postings formatting"""
        jobs = [
            {'title': 'Engineer', 'department': 'Engineering', 'location': 'NYC'},
            {'title': 'Designer', 'department': 'Design', 'location': 'Remote'}
        ]
        
        result = processor._format_jobs(jobs)
        
        assert 'Engineer' in result
        assert 'Engineering' in result
    
    def test_parse_json_response_valid(self, processor):
        """Test JSON parsing from AI response"""
        response = 'Here is the analysis: {"score": 8, "summary": "test"}'
        
        result = processor._parse_json_response(response)
        
        assert 'score' in result
        assert result['score'] == 8
    
    def test_parse_json_response_invalid(self, processor):
        """Test JSON parsing with invalid response"""
        response = 'No JSON here, just plain text'
        
        result = processor._parse_json_response(response)
        
        # Should return default analysis
        assert 'summary' in result
        assert result['summary'] == 'Analysis pending'
    
    def test_default_analysis(self, processor):
        """Test default analysis response"""
        result = processor._default_analysis()
        
        assert result['summary'] == 'Analysis pending'
        assert result['impact_score'] == 5.0
        assert 'recommended_action' in result
