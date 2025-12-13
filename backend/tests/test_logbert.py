"""
Tests for LogBERT anomaly detection service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import torch
from src.services.ai.logbert import LogAnomalyDetector, RootCauseAnalyzer


class TestLogAnomalyDetector:
    """Tests for LogBERT anomaly detection"""
    
    @pytest.fixture
    def detector(self):
        """Create detector with mocked model"""
        with patch('src.services.ai.logbert.BertTokenizer'):
            with patch('src.services.ai.logbert.BertModel'):
                detector = LogAnomalyDetector()
                detector.model = Mock()
                detector.tokenizer = Mock()
                detector.tokenizer.encode_plus.return_value = {
                    'input_ids': torch.tensor([[1, 2, 3]]),
                    'attention_mask': torch.tensor([[1, 1, 1]])
                }
                return detector
    
    def test_parse_log(self, detector):
        """Test log message parsing"""
        log_message = "2023-10-15 10:30:45 ERROR Database connection failed: timeout"
        
        result = detector.parse_log(log_message)
        
        assert 'timestamp' in result or 'message' in result
        assert 'level' in result or 'raw' in result
    
    def test_parse_log_structured(self, detector):
        """Test parsing structured log"""
        log_message = '{"timestamp": "2023-10-15", "level": "ERROR", "message": "Failed"}'
        
        result = detector.parse_log(log_message)
        
        assert 'raw' in result or 'message' in result
    
    @pytest.mark.asyncio
    async def test_detect_anomaly_normal(self, detector):
        """Test detecting normal log"""
        detector.model.return_value = Mock(
            logits=torch.tensor([[0.9, 0.1]])  # High normal prob
        )
        
        log_message = "INFO Application started successfully"
        
        result = await detector.detect_anomaly(log_message)
        
        assert 'is_anomaly' in result
        assert 'score' in result
    
    @pytest.mark.asyncio
    async def test_detect_anomaly_abnormal(self, detector):
        """Test detecting anomalous log"""
        detector.model.return_value = Mock(
            logits=torch.tensor([[0.1, 0.9]])  # High anomaly prob
        )
        
        log_message = "CRITICAL Memory allocation failed: out of memory"
        
        result = await detector.detect_anomaly(log_message)
        
        assert 'is_anomaly' in result
        assert 'score' in result
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_batch(self, detector):
        """Test batch anomaly detection"""
        detector.model.return_value = Mock(
            logits=torch.tensor([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3]])
        )
        
        logs = [
            "INFO Request processed",
            "ERROR Database timeout",
            "WARN Slow query detected"
        ]
        
        results = await detector.detect_anomalies_batch(logs)
        
        assert len(results) == 3
    
    def test_analyze_log_sequence(self, detector):
        """Test log sequence analysis"""
        logs = [
            "INFO Starting service",
            "ERROR Connection refused",
            "ERROR Retry failed",
            "CRITICAL Service down"
        ]
        
        result = detector.analyze_log_sequence(logs)
        
        assert 'anomaly_count' in result
        assert 'severity' in result
        assert 'pattern' in result or 'summary' in result
    
    def test_calculate_severity_critical(self, detector):
        """Test critical severity calculation"""
        result = detector._calculate_severity(
            anomaly_count=10,
            error_count=8,
            avg_score=0.95
        )
        
        assert result == 'critical'
    
    def test_calculate_severity_high(self, detector):
        """Test high severity calculation"""
        result = detector._calculate_severity(
            anomaly_count=5,
            error_count=3,
            avg_score=0.75
        )
        
        assert result in ['critical', 'high']
    
    def test_calculate_severity_low(self, detector):
        """Test low severity calculation"""
        result = detector._calculate_severity(
            anomaly_count=1,
            error_count=0,
            avg_score=0.3
        )
        
        assert result in ['low', 'medium']


class TestRootCauseAnalyzer:
    """Tests for AI-powered root cause analysis"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked AI processor"""
        with patch('src.services.ai.logbert.AIProcessor'):
            analyzer = RootCauseAnalyzer()
            analyzer.ai_processor = Mock()
            return analyzer
    
    @pytest.mark.asyncio
    async def test_analyze_incident(self, analyzer):
        """Test incident root cause analysis"""
        from unittest.mock import AsyncMock
        analyzer.ai_processor._call_gemini = AsyncMock(return_value='''
        {
            "root_cause": "Database connection pool exhausted",
            "contributing_factors": ["High traffic", "Long running queries"],
            "recommendations": ["Increase pool size", "Add query timeout"],
            "confidence": 0.85
        }
        ''')
        
        anomalous_logs = [
            {'message': 'Connection timeout', 'timestamp': '10:30:00'},
            {'message': 'Pool exhausted', 'timestamp': '10:30:05'},
            {'message': 'Request failed', 'timestamp': '10:30:10'}
        ]
        
        context = {'service': 'api-server', 'environment': 'production'}
        
        result = await analyzer.analyze_incident(anomalous_logs, context)
        
        assert 'root_cause' in result or 'analysis' in result
    
    def test_format_logs(self, analyzer):
        """Test log formatting for AI prompt"""
        logs = [
            {'message': 'Error 1', 'timestamp': '10:00:00', 'level': 'ERROR'},
            {'message': 'Error 2', 'timestamp': '10:00:05', 'level': 'ERROR'}
        ]
        
        result = analyzer._format_logs(logs)
        
        assert 'Error 1' in result
        assert 'Error 2' in result
