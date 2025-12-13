"""
Tests for LSTM and Autoencoder Anomaly Detection Models
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.services.ai.anomaly_models import (
    LSTMAnomalyDetector,
    LogAutoencoder,
    AutoencoderAnomalyDetector,
    EnsembleAnomalyDetector,
    AnomalyResult
)


class TestAnomalyResult:
    """Test AnomalyResult dataclass"""
    
    def test_anomaly_result_creation(self):
        """Test creating an AnomalyResult"""
        from datetime import datetime
        
        result = AnomalyResult(
            is_anomaly=True,
            confidence=0.85,
            model_source="lstm",
            details={"score": 0.9},
            timestamp=datetime.utcnow()
        )
        
        assert result.is_anomaly is True
        assert result.confidence == 0.85
        assert result.model_source == "lstm"
    
    def test_anomaly_result_to_dict(self):
        """Test serialization"""
        from datetime import datetime
        
        result = AnomalyResult(
            is_anomaly=False,
            confidence=0.3,
            model_source="autoencoder",
            details={},
            timestamp=datetime.utcnow()
        )
        
        data = result.to_dict()
        assert 'timestamp' in data
        assert data['is_anomaly'] is False


class TestLSTMAnomalyDetector:
    """Test LSTM-based anomaly detection"""
    
    @pytest.fixture
    def detector(self):
        return LSTMAnomalyDetector(vocab_size=1000, embedding_dim=64, hidden_dim=128)
    
    def test_tokenization(self, detector):
        """Test log tokenization"""
        tokens = detector._tokenize("ERROR: Connection failed at 10:30:00")
        
        assert 'error' in tokens
        assert 'connection' in tokens
        assert 'failed' in tokens
    
    def test_build_vocab(self, detector):
        """Test vocabulary building"""
        logs = [
            "INFO: Server started successfully",
            "ERROR: Database connection failed",
            "WARNING: High memory usage detected"
        ]
        
        detector.build_vocab(logs)
        
        assert detector.vocab_built is True
        assert len(detector.word2idx) > 2  # More than PAD and UNK
        assert 'error' in detector.word2idx or 'info' in detector.word2idx
    
    def test_rule_based_score_errors(self, detector):
        """Test rule-based scoring when vocab not built"""
        logs = [
            "ERROR: Critical failure",
            "EXCEPTION: NullPointerException"
        ]
        
        score = detector._rule_based_score(logs)
        
        assert score > 0  # Should detect error keywords
        assert score <= 1.0
    
    def test_rule_based_score_normal(self, detector):
        """Test rule-based scoring for normal logs"""
        logs = [
            "INFO: Request processed successfully",
            "DEBUG: Cache hit"
        ]
        
        score = detector._rule_based_score(logs)
        
        assert score == 0  # No error keywords


class TestLogAutoencoder:
    """Test autoencoder model"""
    
    @pytest.fixture
    def autoencoder(self):
        return LogAutoencoder(input_dim=256, hidden_dims=[128, 64], latent_dim=16)
    
    def test_extract_features(self, autoencoder):
        """Test feature extraction from logs"""
        log = "ERROR: Connection timeout at 192.168.1.1"
        
        features = autoencoder.extract_features(log)
        
        assert features.shape == (256,)
        assert features.max() <= 1.0
        assert features.min() >= 0.0
        # Should detect error pattern
        assert features.sum() > 0
    
    def test_extract_features_status_codes(self, autoencoder):
        """Test feature extraction detects status codes"""
        log_500 = "HTTP 500 Internal Server Error"
        log_200 = "HTTP 200 OK"
        
        features_500 = autoencoder.extract_features(log_500)
        features_200 = autoencoder.extract_features(log_200)
        
        # Both should have non-zero features
        assert features_500.sum() > 0
        assert features_200.sum() > 0
    
    def test_forward_pass(self, autoencoder):
        """Test autoencoder forward pass"""
        import torch
        
        batch = torch.randn(4, 256)
        reconstruction, latent = autoencoder(batch)
        
        assert reconstruction.shape == (4, 256)
        assert latent.shape == (4, 16)


class TestAutoencoderAnomalyDetector:
    """Test high-level autoencoder detector service"""
    
    @pytest.fixture
    def detector(self):
        return AutoencoderAnomalyDetector(threshold=0.5)
    
    def test_detect_normal_logs(self, detector):
        """Test detection on normal-looking logs"""
        logs = [
            "INFO: User logged in successfully",
            "DEBUG: Cache refreshed"
        ]
        
        results = detector.detect(logs)
        
        assert len(results) == 2
        assert all(isinstance(r, AnomalyResult) for r in results)
    
    def test_detect_error_logs(self, detector):
        """Test detection on error logs"""
        logs = [
            "CRITICAL: System crash detected",
            "FATAL: Out of memory exception"
        ]
        
        results = detector.detect(logs)
        
        assert len(results) == 2
        # Error keywords should trigger anomaly
        assert any(r.is_anomaly for r in results)
    
    def test_has_error_keywords(self, detector):
        """Test error keyword detection"""
        assert detector._has_error_keywords("ERROR: Something failed") is True
        assert detector._has_error_keywords("EXCEPTION thrown") is True
        assert detector._has_error_keywords("INFO: All good") is False


class TestEnsembleAnomalyDetector:
    """Test ensemble detector combining multiple models"""
    
    @pytest.fixture
    def detector(self):
        return EnsembleAnomalyDetector(
            use_logbert=False,  # Skip LogBERT for unit tests
            use_lstm=True,
            use_autoencoder=True,
            voting_threshold=0.5
        )
    
    def test_detect_anomalies_empty(self, detector):
        """Test with empty log list"""
        results = detector.detect_anomalies([])
        
        assert results['anomalies'] == [] or results.get('total_logs', 0) == 0
    
    def test_detect_anomalies_normal(self, detector):
        """Test with normal logs"""
        logs = [
            "INFO: Application started",
            "INFO: Request processed in 50ms",
            "DEBUG: Cache hit ratio: 95%"
        ]
        
        results = detector.detect_anomalies(logs)
        
        assert 'ensemble_score' in results
        assert 'model_scores' in results
        assert results['total_logs'] == 3
    
    def test_detect_anomalies_errors(self, detector):
        """Test with error logs"""
        logs = [
            "ERROR: Database connection failed",
            "ERROR: Retry attempt 3 of 5",
            "CRITICAL: Service unavailable"
        ]
        
        results = detector.detect_anomalies(logs)
        
        assert results['anomaly_count'] > 0
        assert len(results['anomalous_indices']) > 0
    
    def test_calculate_severity(self, detector):
        """Test severity calculation"""
        # Low severity
        assert detector._calculate_severity(0.2, 1, 100) == 'low'
        
        # Medium severity
        assert detector._calculate_severity(0.4, 10, 100) == 'medium'
        
        # High severity
        assert detector._calculate_severity(0.6, 20, 100) == 'high'
        
        # Critical severity
        assert detector._calculate_severity(0.9, 40, 100) == 'critical'
    
    def test_model_scores_populated(self, detector):
        """Test that model scores are populated"""
        logs = ["INFO: Test log message"]
        
        results = detector.detect_anomalies(logs)
        
        assert 'model_scores' in results
        # At least one model should have scored
        assert len(results['model_scores']) >= 1


class TestIntegration:
    """Integration tests for anomaly detection pipeline"""
    
    def test_full_pipeline(self):
        """Test full analysis pipeline"""
        detector = EnsembleAnomalyDetector(
            use_logbert=False,
            use_lstm=True,
            use_autoencoder=True
        )
        
        # Mixed logs with some anomalies
        logs = [
            "INFO: Application startup complete",
            "INFO: Connected to database",
            "ERROR: Request timeout after 30s",
            "WARNING: High CPU usage: 95%",
            "CRITICAL: Disk space below 5%",
            "INFO: User session created",
            "ERROR: Authentication failed for user 'admin'"
        ]
        
        results = detector.detect_anomalies(logs)
        
        assert results['total_logs'] == 7
        assert results['anomaly_count'] >= 3  # At least ERROR/CRITICAL lines
        assert results['severity'] in ['low', 'medium', 'high', 'critical']
