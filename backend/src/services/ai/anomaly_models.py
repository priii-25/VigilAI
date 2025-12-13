"""
LSTM and Autoencoder-based Anomaly Detection Models
Complements LogBERT for comprehensive AIOps observability.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result from anomaly detection."""
    is_anomaly: bool
    confidence: float
    model_source: str
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class LSTMAnomalyDetector(nn.Module):
    """
    LSTM-based sequence anomaly detection for log patterns.
    Detects anomalies by learning normal log sequence patterns.
    """
    
    def __init__(
        self,
        vocab_size: int = 10000,
        embedding_dim: int = 128,
        hidden_dim: int = 256,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super(LSTMAnomalyDetector, self).__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Output layer for next token prediction
        self.fc = nn.Linear(hidden_dim * 2, vocab_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Tokenizer (simple word-based)
        self.word2idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx2word = {0: '<PAD>', 1: '<UNK>'}
        self.vocab_built = False
    
    def build_vocab(self, logs: List[str], max_vocab: int = 10000):
        """Build vocabulary from log messages."""
        word_counts = Counter()
        for log in logs:
            tokens = self._tokenize(log)
            word_counts.update(tokens)
        
        # Take most common words
        for word, _ in word_counts.most_common(max_vocab - 2):
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word
        
        self.vocab_built = True
        logger.info(f"Built vocabulary with {len(self.word2idx)} tokens")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization suitable for log messages."""
        # Normalize and split on whitespace and special chars
        text = text.lower()
        tokens = re.findall(r'[a-z]+|[0-9]+|[^\s\w]', text)
        return tokens
    
    def encode_sequence(self, log_sequence: List[str], max_len: int = 100) -> torch.Tensor:
        """Encode log sequence to tensor."""
        all_tokens = []
        for log in log_sequence:
            tokens = self._tokenize(log)
            all_tokens.extend(tokens)
        
        # Convert to indices
        indices = [self.word2idx.get(t, 1) for t in all_tokens[:max_len]]
        
        # Pad sequence
        if len(indices) < max_len:
            indices.extend([0] * (max_len - len(indices)))
        
        return torch.tensor(indices, dtype=torch.long).unsqueeze(0)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass."""
        embedded = self.dropout(self.embedding(x))
        lstm_out, (hidden, cell) = self.lstm(embedded)
        output = self.fc(lstm_out)
        return output, lstm_out
    
    def compute_anomaly_score(self, log_sequence: List[str]) -> float:
        """
        Compute anomaly score for a log sequence.
        Higher score = more anomalous.
        """
        if not self.vocab_built:
            logger.warning("Vocabulary not built, using default scoring")
            return self._rule_based_score(log_sequence)
        
        self.eval()
        with torch.no_grad():
            x = self.encode_sequence(log_sequence)
            predictions, _ = self.forward(x)
            
            # Calculate prediction loss as anomaly score
            # Shift for next-token prediction
            target = x[:, 1:]
            pred = predictions[:, :-1, :]
            
            loss_fn = nn.CrossEntropyLoss(reduction='mean', ignore_index=0)
            loss = loss_fn(pred.reshape(-1, self.vocab_size), target.reshape(-1))
            
            return float(loss.item())
    
    def _rule_based_score(self, log_sequence: List[str]) -> float:
        """Fallback rule-based scoring when model not trained."""
        score = 0.0
        
        error_keywords = ['error', 'exception', 'fail', 'critical', 'fatal', 'timeout']
        warning_keywords = ['warn', 'warning', 'retry', 'slow']
        
        for log in log_sequence:
            log_lower = log.lower()
            if any(kw in log_lower for kw in error_keywords):
                score += 0.3
            elif any(kw in log_lower for kw in warning_keywords):
                score += 0.1
        
        return min(score, 1.0)


class LogAutoencoder(nn.Module):
    """
    Autoencoder for unsupervised log anomaly detection.
    Learns to reconstruct normal log patterns; anomalies have high reconstruction error.
    """
    
    def __init__(
        self,
        input_dim: int = 512,
        hidden_dims: List[int] = [256, 128, 64],
        latent_dim: int = 32,
        dropout: float = 0.2
    ):
        super(LogAutoencoder, self).__init__()
        
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        
        # Encoder
        encoder_layers = []
        prev_dim = input_dim
        for dim in hidden_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, dim),
                nn.BatchNorm1d(dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = dim
        encoder_layers.append(nn.Linear(prev_dim, latent_dim))
        self.encoder = nn.Sequential(*encoder_layers)
        
        # Decoder
        decoder_layers = []
        prev_dim = latent_dim
        for dim in reversed(hidden_dims):
            decoder_layers.extend([
                nn.Linear(prev_dim, dim),
                nn.BatchNorm1d(dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = dim
        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        decoder_layers.append(nn.Sigmoid())
        self.decoder = nn.Sequential(*decoder_layers)
        
        # Feature extractor for log text
        self.feature_weights = None
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning reconstruction and latent representation."""
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return reconstruction, latent
    
    def extract_features(self, log_message: str) -> np.ndarray:
        """
        Extract features from log message for autoencoder input.
        Uses TF-IDF-like weighting based on learned patterns.
        """
        # Simple bag-of-words with common log patterns
        feature_patterns = [
            # Error patterns
            r'error', r'exception', r'fail', r'critical', r'fatal',
            # Warning patterns
            r'warn', r'timeout', r'retry', r'slow',
            # Info patterns
            r'success', r'complete', r'start', r'stop', r'init',
            # Numeric patterns
            r'\d+', r'\d+\.\d+', r'\d+%',
            # Status codes
            r'200', r'201', r'400', r'401', r'403', r'404', r'500', r'502', r'503',
            # Time patterns
            r'\d{2}:\d{2}:\d{2}', r'\d{4}-\d{2}-\d{2}',
            # IP patterns
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            # Common log levels
            r'DEBUG', r'INFO', r'WARN', r'ERROR', r'CRITICAL',
        ]
        
        features = np.zeros(self.input_dim, dtype=np.float32)
        log_lower = log_message.lower()
        
        for i, pattern in enumerate(feature_patterns[:self.input_dim]):
            if re.search(pattern, log_message, re.IGNORECASE):
                features[i] = 1.0
        
        # Add word-level features for remaining dimensions
        words = re.findall(r'\w+', log_lower)
        for j, word in enumerate(words[:self.input_dim - len(feature_patterns)]):
            idx = len(feature_patterns) + hash(word) % (self.input_dim - len(feature_patterns))
            features[idx] = 1.0
        
        return features
    
    def compute_reconstruction_error(self, log_messages: List[str]) -> float:
        """
        Compute average reconstruction error for log messages.
        Higher error indicates potential anomaly.
        """
        if not log_messages:
            return 0.0
        
        self.eval()
        with torch.no_grad():
            # Extract features
            features = np.array([self.extract_features(log) for log in log_messages])
            x = torch.tensor(features, dtype=torch.float32)
            
            # Get reconstruction
            reconstruction, _ = self.forward(x)
            
            # Compute MSE
            mse = nn.MSELoss(reduction='mean')
            error = mse(reconstruction, x)
            
            return float(error.item())


class AutoencoderAnomalyDetector:
    """
    High-level anomaly detection service using autoencoder.
    Provides training, inference, and threshold-based detection.
    """
    
    def __init__(self, threshold: float = 0.5):
        self.model = LogAutoencoder()
        self.threshold = threshold
        self.is_trained = False
        self.mean_error = 0.0
        self.std_error = 0.1
    
    def train(self, normal_logs: List[str], epochs: int = 50, lr: float = 0.001):
        """
        Train autoencoder on normal log data.
        
        Args:
            normal_logs: List of normal log messages for training
            epochs: Number of training epochs
            lr: Learning rate
        """
        if len(normal_logs) < 10:
            logger.warning("Insufficient data for training, using rule-based detection")
            return
        
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        # Prepare data
        features = np.array([self.model.extract_features(log) for log in normal_logs])
        dataset = torch.tensor(features, dtype=torch.float32)
        
        logger.info(f"Training autoencoder on {len(normal_logs)} log samples")
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            reconstruction, _ = self.model(dataset)
            loss = criterion(reconstruction, dataset)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                logger.debug(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item():.4f}")
        
        # Calculate baseline error statistics
        self.model.eval()
        with torch.no_grad():
            recon, _ = self.model(dataset)
            errors = torch.mean((recon - dataset) ** 2, dim=1)
            self.mean_error = float(errors.mean())
            self.std_error = float(errors.std())
        
        self.is_trained = True
        logger.info(f"Training complete. Mean error: {self.mean_error:.4f}, Std: {self.std_error:.4f}")
    
    def detect(self, log_messages: List[str]) -> List[AnomalyResult]:
        """
        Detect anomalies in log messages.
        
        Args:
            log_messages: List of log messages to analyze
            
        Returns:
            List of AnomalyResult for each message
        """
        results = []
        
        for log in log_messages:
            error = self.model.compute_reconstruction_error([log])
            
            # Calculate z-score
            if self.std_error > 0:
                z_score = (error - self.mean_error) / self.std_error
            else:
                z_score = error
            
            # Determine if anomaly
            is_anomaly = z_score > self.threshold or self._has_error_keywords(log)
            confidence = min(abs(z_score) / 3.0, 1.0)  # Normalize to 0-1
            
            results.append(AnomalyResult(
                is_anomaly=is_anomaly,
                confidence=confidence,
                model_source='autoencoder',
                details={
                    'reconstruction_error': error,
                    'z_score': z_score,
                    'threshold': self.threshold
                },
                timestamp=datetime.utcnow()
            ))
        
        return results
    
    def _has_error_keywords(self, log: str) -> bool:
        """Check for obvious error keywords."""
        error_patterns = ['error', 'exception', 'critical', 'fatal', 'fail']
        log_lower = log.lower()
        return any(p in log_lower for p in error_patterns)


class EnsembleAnomalyDetector:
    """
    Ensemble detector combining LogBERT, LSTM, and Autoencoder.
    Provides robust anomaly detection through model voting.
    """
    
    def __init__(
        self,
        use_logbert: bool = True,
        use_lstm: bool = True,
        use_autoencoder: bool = True,
        voting_threshold: float = 0.5
    ):
        self.use_logbert = use_logbert
        self.use_lstm = use_lstm
        self.use_autoencoder = use_autoencoder
        self.voting_threshold = voting_threshold
        
        # Initialize models
        self.lstm_detector = LSTMAnomalyDetector() if use_lstm else None
        self.autoencoder_detector = AutoencoderAnomalyDetector() if use_autoencoder else None
        self.logbert_detector = None  # Will be loaded if available
        
        if use_logbert:
            try:
                from src.services.ai.logbert import LogAnomalyDetector
                self.logbert_detector = LogAnomalyDetector()
            except Exception as e:
                logger.warning(f"Could not load LogBERT: {str(e)}")
                self.use_logbert = False
    
    def train(self, normal_logs: List[str]):
        """Train all models on normal log data."""
        if self.lstm_detector:
            self.lstm_detector.build_vocab(normal_logs)
            logger.info("LSTM vocabulary built")
        
        if self.autoencoder_detector:
            self.autoencoder_detector.train(normal_logs)
            logger.info("Autoencoder trained")
    
    def detect_anomalies(self, log_messages: List[str]) -> Dict[str, Any]:
        """
        Detect anomalies using ensemble voting.
        
        Args:
            log_messages: List of log messages to analyze
            
        Returns:
            Dict with ensemble results and per-model scores
        """
        if not log_messages:
            return {'anomalies': [], 'summary': 'No logs provided'}
        
        results = []
        model_scores = {}
        
        # LSTM scoring
        if self.lstm_detector:
            lstm_score = self.lstm_detector.compute_anomaly_score(log_messages)
            model_scores['lstm'] = lstm_score
        
        # Autoencoder scoring
        if self.autoencoder_detector:
            ae_results = self.autoencoder_detector.detect(log_messages)
            ae_score = sum(1 for r in ae_results if r.is_anomaly) / len(ae_results)
            model_scores['autoencoder'] = ae_score
        
        # LogBERT scoring
        if self.logbert_detector:
            try:
                logbert_results = self.logbert_detector.detect_anomalies_batch(log_messages)
                logbert_score = sum(1 for r in logbert_results if r['is_anomaly']) / len(logbert_results)
                model_scores['logbert'] = logbert_score
            except Exception as e:
                logger.warning(f"LogBERT detection failed: {str(e)}")
        
        # Ensemble decision
        avg_score = np.mean(list(model_scores.values())) if model_scores else 0.0
        is_critical = avg_score > self.voting_threshold
        
        # Identify anomalous lines
        anomalous_indices = []
        for i, log in enumerate(log_messages):
            log_lower = log.lower()
            if any(kw in log_lower for kw in ['error', 'exception', 'critical', 'fatal']):
                anomalous_indices.append(i)
        
        return {
            'is_critical': is_critical,
            'ensemble_score': float(avg_score),
            'model_scores': model_scores,
            'anomalous_indices': anomalous_indices,
            'total_logs': len(log_messages),
            'anomaly_count': len(anomalous_indices),
            'severity': self._calculate_severity(avg_score, len(anomalous_indices), len(log_messages)),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_severity(self, score: float, anomaly_count: int, total: int) -> str:
        """Calculate severity level."""
        ratio = anomaly_count / total if total > 0 else 0
        
        if score > 0.8 or ratio > 0.3:
            return 'critical'
        elif score > 0.5 or ratio > 0.15:
            return 'high'
        elif score > 0.3 or ratio > 0.05:
            return 'medium'
        else:
            return 'low'


# Convenience functions for pipeline integration
def create_ensemble_detector() -> EnsembleAnomalyDetector:
    """Create and return ensemble anomaly detector."""
    return EnsembleAnomalyDetector()


async def analyze_logs_with_ensemble(
    log_messages: List[str],
    detector: Optional[EnsembleAnomalyDetector] = None
) -> Dict[str, Any]:
    """
    Async wrapper for ensemble log analysis.
    
    Args:
        log_messages: List of log messages
        detector: Optional pre-initialized detector
        
    Returns:
        Anomaly detection results
    """
    if detector is None:
        detector = create_ensemble_detector()
    
    return detector.detect_anomalies(log_messages)
