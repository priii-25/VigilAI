"""
LogBERT model for anomaly detection in system logs
"""
import torch
import torch.nn as nn
from transformers import BertModel, BertTokenizer, BertConfig
from typing import List, Tuple, Dict
import numpy as np
from loguru import logger
from src.core.config import settings


class LogBERT(nn.Module):
    """BERT-based model for log anomaly detection"""
    
    def __init__(self, config: BertConfig):
        super(LogBERT, self).__init__()
        self.bert = BertModel(config)
        self.classifier = nn.Linear(config.hidden_size, 2)  # Binary: normal/anomaly
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
    
    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        return logits


class LogAnomalyDetector:
    """Log anomaly detection service using LogBERT"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.LOGBERT_MODEL_PATH
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.model = None
        self.threshold = settings.ANOMALY_THRESHOLD
        
        # Log templates for parsing
        self.log_templates = {}
        
    def load_model(self):
        """Load pre-trained LogBERT model"""
        try:
            config = BertConfig.from_pretrained('bert-base-uncased')
            self.model = LogBERT(config)
            
            # Load trained weights if available
            import os
            if os.path.exists(self.model_path):
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                logger.info(f"Loaded LogBERT model from {self.model_path}")
            else:
                logger.warning(f"Model file not found at {self.model_path}, using untrained model")
            
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"Error loading LogBERT model: {str(e)}")
            # Initialize with default BERT
            config = BertConfig.from_pretrained('bert-base-uncased')
            self.model = LogBERT(config)
            self.model.to(self.device)
            self.model.eval()
    
    def parse_log(self, log_message: str) -> Dict:
        """Parse log message into structured format"""
        # Simple log parsing - can be enhanced with Drain algorithm
        parts = log_message.split('|')
        
        parsed = {
            'timestamp': parts[0].strip() if len(parts) > 0 else '',
            'level': parts[1].strip() if len(parts) > 1 else 'INFO',
            'source': parts[2].strip() if len(parts) > 2 else 'unknown',
            'message': parts[3].strip() if len(parts) > 3 else log_message
        }
        
        return parsed
    
    def detect_anomaly(self, log_message: str) -> Tuple[bool, float]:
        """Detect if log message is anomalous"""
        if not self.model:
            self.load_model()
        
        # Tokenize log message
        inputs = self.tokenizer(
            log_message,
            return_tensors='pt',
            max_length=512,
            truncation=True,
            padding='max_length'
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get prediction
        with torch.no_grad():
            logits = self.model(**inputs)
            probs = torch.softmax(logits, dim=-1)
            anomaly_score = probs[0][1].item()  # Probability of anomaly class
        
        is_anomaly = anomaly_score > self.threshold
        
        return is_anomaly, anomaly_score
    
    def detect_anomalies_batch(self, log_messages: List[str]) -> List[Dict]:
        """Detect anomalies in batch of log messages"""
        results = []
        
        for log in log_messages:
            is_anomaly, score = self.detect_anomaly(log)
            parsed = self.parse_log(log)
            
            results.append({
                'log_message': log,
                'is_anomaly': is_anomaly,
                'anomaly_score': float(score),
                'parsed': parsed
            })
        
        logger.info(f"Processed {len(log_messages)} logs, found {sum(r['is_anomaly'] for r in results)} anomalies")
        return results
    
    def analyze_log_sequence(self, log_sequence: List[str]) -> Dict:
        """Analyze sequence of logs for patterns"""
        # Detect anomalies
        anomaly_results = self.detect_anomalies_batch(log_sequence)
        
        # Calculate sequence metrics
        anomaly_count = sum(r['is_anomaly'] for r in anomaly_results)
        avg_score = np.mean([r['anomaly_score'] for r in anomaly_results])
        
        # Identify patterns
        log_levels = [self.parse_log(log).get('level', 'INFO') for log in log_sequence]
        error_count = sum(1 for level in log_levels if level in ['ERROR', 'CRITICAL'])
        
        analysis = {
            'total_logs': len(log_sequence),
            'anomaly_count': anomaly_count,
            'anomaly_rate': anomaly_count / len(log_sequence) if log_sequence else 0,
            'avg_anomaly_score': float(avg_score),
            'error_count': error_count,
            'anomalous_logs': [r for r in anomaly_results if r['is_anomaly']],
            'severity': self._calculate_severity(anomaly_count, error_count, avg_score)
        }
        
        return analysis
    
    def _calculate_severity(self, anomaly_count: int, error_count: int, avg_score: float) -> str:
        """Calculate severity level based on metrics"""
        if anomaly_count > 5 or error_count > 3 or avg_score > 0.9:
            return 'critical'
        elif anomaly_count > 2 or error_count > 1 or avg_score > 0.85:
            return 'high'
        elif anomaly_count > 0 or avg_score > 0.7:
            return 'medium'
        else:
            return 'low'


class RootCauseAnalyzer:
    """AI-powered root cause analysis for incidents"""
    
    def __init__(self):
        from src.services.ai.processor import AIProcessor
        self.ai_processor = AIProcessor()
    
    async def analyze_incident(self, anomalous_logs: List[Dict], context: Dict = None) -> Dict:
        """Perform root cause analysis on incident"""
        
        # Format logs for analysis
        log_summary = self._format_logs(anomalous_logs)
        
        prompt = f"""
Analyze the following anomalous system logs and provide root cause analysis:

ANOMALOUS LOGS:
{log_summary}

CONTEXT:
{context or 'No additional context'}

Provide:
1. Root Cause (1-2 sentences explaining what went wrong)
2. Affected Components (list)
3. Suggested Fix (actionable steps)
4. Prevention Strategy (how to avoid in future)

Format as JSON with keys: root_cause, affected_components, suggested_fix, prevention_strategy
"""
        
        try:
            response = await self.ai_processor._call_claude(prompt)
            result = self.ai_processor._parse_json_response(response)
            logger.info("Root cause analysis completed")
            return result
        except Exception as e:
            logger.error(f"Error in root cause analysis: {str(e)}")
            return {
                'root_cause': 'Analysis pending',
                'affected_components': [],
                'suggested_fix': 'Manual investigation required',
                'prevention_strategy': 'To be determined'
            }
    
    def _format_logs(self, logs: List[Dict]) -> str:
        """Format logs for AI prompt"""
        formatted = []
        for log in logs[:20]:  # Limit to most recent
            formatted.append(
                f"[{log.get('parsed', {}).get('level', 'INFO')}] "
                f"{log.get('parsed', {}).get('message', log.get('log_message', ''))}"
            )
        return '\n'.join(formatted)
