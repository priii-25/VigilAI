"""
Log Anomaly Detection using LogBERT
Detects scraper failures, system anomalies, and performs root cause analysis.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, CRITICAL
    source: str  # Component that generated the log
    message: str
    raw_log: str
    template: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class LogAnomaly:
    """Represents a detected log anomaly."""
    anomaly_id: str
    severity: str  # low, medium, high, critical
    anomaly_type: str  # pattern_break, error_spike, silence, unusual_sequence
    affected_component: str
    description: str
    log_entries: List[LogEntry]
    root_cause: Optional[str]
    recommendation: Optional[str]
    detected_at: datetime
    confidence_score: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        data['log_entries'] = [entry.to_dict() for entry in self.log_entries]
        return data


class LogParser:
    """
    Parse unstructured logs into structured format.
    Uses Drain algorithm for log template extraction.
    """
    
    def __init__(self):
        self.log_templates = {}
        self.template_counter = Counter()
        
        # Common log patterns
        self.patterns = {
            'timestamp': r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',
            'level': r'(DEBUG|INFO|WARNING|ERROR|CRITICAL|FATAL)',
            'ip': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'url': r'https?://[^\s]+',
            'number': r'\d+'
        }
    
    def parse_log_line(self, log_line: str) -> Optional[LogEntry]:
        """
        Parse a single log line into structured format.
        
        Args:
            log_line: Raw log line
            
        Returns:
            LogEntry object or None if parsing fails
        """
        try:
            # Extract timestamp
            timestamp_match = re.search(self.patterns['timestamp'], log_line)
            timestamp = datetime.fromisoformat(
                timestamp_match.group(0).replace('Z', '+00:00')
            ) if timestamp_match else datetime.utcnow()
            
            # Extract log level
            level_match = re.search(self.patterns['level'], log_line)
            level = level_match.group(1) if level_match else 'INFO'
            
            # Extract source (component name)
            source_pattern = r'\[(\w+)\]|\((\w+)\)|(\w+):'
            source_match = re.search(source_pattern, log_line)
            source = next((g for g in source_match.groups() if g), 'unknown') if source_match else 'unknown'
            
            # Extract message (everything after level/source)
            message = log_line
            if level_match:
                message = log_line[level_match.end():].strip()
            
            # Generate template by replacing variables
            template = self._extract_template(message)
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                source=source,
                message=message,
                raw_log=log_line,
                template=template
            )
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None
    
    def _extract_template(self, message: str) -> str:
        """
        Extract log template by replacing variables with placeholders.
        This is a simplified version of the Drain algorithm.
        """
        template = message
        
        # Replace IPs
        template = re.sub(self.patterns['ip'], '<IP>', template)
        
        # Replace URLs
        template = re.sub(self.patterns['url'], '<URL>', template)
        
        # Replace numbers
        template = re.sub(r'\b\d+\b', '<NUM>', template)
        
        # Replace quoted strings
        template = re.sub(r'"[^"]*"', '<STR>', template)
        template = re.sub(r"'[^']*'", '<STR>', template)
        
        return template
    
    def parse_logs(self, log_lines: List[str]) -> List[LogEntry]:
        """Parse multiple log lines."""
        entries = []
        for line in log_lines:
            entry = self.parse_log_line(line)
            if entry:
                entries.append(entry)
                self.template_counter[entry.template] += 1
        
        return entries


class LogBERTDetector:
    """
    LogBERT-inspired anomaly detection.
    Uses template-based analysis and statistical methods.
    For production, integrate with actual BERT model.
    """
    
    def __init__(self):
        self.baseline_patterns = defaultdict(list)
        self.error_threshold = 0.1  # 10% error rate threshold
        self.silence_threshold = 300  # seconds without logs
    
    def learn_baseline(self, historical_logs: List[LogEntry]):
        """
        Learn normal log patterns from historical data.
        
        Args:
            historical_logs: List of historical log entries
        """
        # Learn template frequencies
        template_counts = Counter()
        for entry in historical_logs:
            template_counts[entry.template] += 1
        
        # Store baseline patterns by component
        for entry in historical_logs:
            self.baseline_patterns[entry.source].append({
                'template': entry.template,
                'level': entry.level,
                'frequency': template_counts[entry.template] / len(historical_logs)
            })
        
        logger.info(f"Learned baseline from {len(historical_logs)} log entries")
    
    def detect_anomalies(self, recent_logs: List[LogEntry]) -> List[LogAnomaly]:
        """
        Detect anomalies in recent logs.
        
        Args:
            recent_logs: Recent log entries to analyze
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # 1. Detect error spikes
        error_anomalies = self._detect_error_spike(recent_logs)
        anomalies.extend(error_anomalies)
        
        # 2. Detect unusual sequences
        sequence_anomalies = self._detect_unusual_sequences(recent_logs)
        anomalies.extend(sequence_anomalies)
        
        # 3. Detect silence (missing expected logs)
        silence_anomalies = self._detect_silence(recent_logs)
        anomalies.extend(silence_anomalies)
        
        # 4. Detect new error patterns
        new_error_anomalies = self._detect_new_errors(recent_logs)
        anomalies.extend(new_error_anomalies)
        
        return anomalies
    
    def _detect_error_spike(self, logs: List[LogEntry]) -> List[LogAnomaly]:
        """Detect sudden increase in error rate."""
        anomalies = []
        
        if not logs:
            return anomalies
        
        # Group by component
        by_component = defaultdict(list)
        for entry in logs:
            by_component[entry.source].append(entry)
        
        for component, component_logs in by_component.items():
            error_count = sum(1 for log in component_logs if log.level in ['ERROR', 'CRITICAL'])
            error_rate = error_count / len(component_logs)
            
            if error_rate > self.error_threshold:
                # Extract error messages
                error_logs = [log for log in component_logs if log.level in ['ERROR', 'CRITICAL']]
                
                # Find most common error
                error_templates = Counter([log.template for log in error_logs])
                most_common_error = error_templates.most_common(1)[0] if error_templates else (None, 0)
                
                anomaly = LogAnomaly(
                    anomaly_id=f"error_spike_{component}_{datetime.utcnow().timestamp()}",
                    severity='high' if error_rate > 0.3 else 'medium',
                    anomaly_type='error_spike',
                    affected_component=component,
                    description=f"Error rate spike detected: {error_rate*100:.1f}% ({error_count}/{len(component_logs)} logs)",
                    log_entries=error_logs[-5:],  # Last 5 errors
                    root_cause=f"Most common error: {most_common_error[0]}" if most_common_error[0] else None,
                    recommendation=self._generate_recommendation('error_spike', component, most_common_error[0]),
                    detected_at=datetime.utcnow(),
                    confidence_score=min(1.0, error_rate * 2)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_unusual_sequences(self, logs: List[LogEntry]) -> List[LogAnomaly]:
        """Detect unusual log sequences (e.g., missing success after start)."""
        anomalies = []
        
        # Look for start-end pattern violations
        by_component = defaultdict(list)
        for entry in logs:
            by_component[entry.source].append(entry)
        
        for component, component_logs in by_component.items():
            # Check for "started" without "completed" patterns
            started_count = sum(1 for log in component_logs if 'start' in log.message.lower())
            completed_count = sum(1 for log in component_logs if any(word in log.message.lower() for word in ['complet', 'success', 'finish']))
            
            if started_count > 0 and completed_count == 0:
                anomaly = LogAnomaly(
                    anomaly_id=f"sequence_{component}_{datetime.utcnow().timestamp()}",
                    severity='medium',
                    anomaly_type='unusual_sequence',
                    affected_component=component,
                    description=f"Found {started_count} 'start' logs but no completion logs",
                    log_entries=[log for log in component_logs if 'start' in log.message.lower()][-3:],
                    root_cause="Process may have failed silently or is still running",
                    recommendation="Check if process is stuck or crashed without logging errors",
                    detected_at=datetime.utcnow(),
                    confidence_score=0.7
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_silence(self, logs: List[LogEntry]) -> List[LogAnomaly]:
        """Detect components that have gone silent."""
        anomalies = []
        
        if not logs:
            return anomalies
        
        # Check for expected components in baseline
        recent_components = {log.source for log in logs}
        baseline_components = set(self.baseline_patterns.keys())
        
        missing_components = baseline_components - recent_components
        
        for component in missing_components:
            anomaly = LogAnomaly(
                anomaly_id=f"silence_{component}_{datetime.utcnow().timestamp()}",
                severity='medium',
                anomaly_type='silence',
                affected_component=component,
                description=f"Component '{component}' has stopped logging",
                log_entries=[],
                root_cause="Component may have crashed or is not running",
                recommendation=f"Check if {component} process is running and restart if necessary",
                detected_at=datetime.utcnow(),
                confidence_score=0.8
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_new_errors(self, logs: List[LogEntry]) -> List[LogAnomaly]:
        """Detect error patterns not seen in baseline."""
        anomalies = []
        
        # Get baseline error templates
        baseline_errors = set()
        for component_patterns in self.baseline_patterns.values():
            baseline_errors.update([p['template'] for p in component_patterns if 'error' in p['template'].lower()])
        
        # Find new error templates
        for log in logs:
            if log.level in ['ERROR', 'CRITICAL'] and log.template not in baseline_errors:
                anomaly = LogAnomaly(
                    anomaly_id=f"new_error_{log.source}_{datetime.utcnow().timestamp()}",
                    severity='high',
                    anomaly_type='pattern_break',
                    affected_component=log.source,
                    description=f"New error pattern detected: {log.template[:100]}",
                    log_entries=[log],
                    root_cause="Previously unseen error occurred",
                    recommendation="Investigate this new error pattern as it may indicate a new issue",
                    detected_at=datetime.utcnow(),
                    confidence_score=0.9
                )
                anomalies.append(anomaly)
                baseline_errors.add(log.template)  # Avoid duplicates
        
        return anomalies
    
    def _generate_recommendation(self, anomaly_type: str, component: str, error_template: Optional[str]) -> str:
        """Generate actionable recommendations based on anomaly type."""
        recommendations = {
            'error_spike': f"1. Check {component} service health\n2. Review recent deployments\n3. Check resource availability (CPU, memory, disk)",
            'unusual_sequence': f"1. Verify {component} is completing tasks\n2. Check for hanging processes\n3. Review timeout configurations",
            'silence': f"1. Verify {component} is running\n2. Check service status and restart if needed\n3. Review startup logs for errors",
            'pattern_break': f"1. Investigate new error: {error_template}\n2. Check recent code changes\n3. Review system dependencies"
        }
        
        return recommendations.get(anomaly_type, "Investigate the issue and review recent changes")


class RootCauseAnalyzer:
    """
    AI-powered root cause analysis for log anomalies.
    Uses pattern matching and LLM integration for explanations.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize RCA analyzer.
        
        Args:
            llm_client: Optional LLM client (Claude, GPT-4) for advanced analysis
        """
        self.llm_client = llm_client
        
        # Known error patterns and their root causes
        self.error_patterns = {
            r'connection.*refused': {
                'cause': 'Service is not running or firewall is blocking connection',
                'fix': 'Verify service is running and check network/firewall rules'
            },
            r'timeout.*exceeded': {
                'cause': 'Operation took longer than allowed timeout period',
                'fix': 'Increase timeout value or optimize slow operation'
            },
            r'no.*space.*left': {
                'cause': 'Disk is full',
                'fix': 'Free up disk space or increase storage capacity'
            },
            r'permission.*denied': {
                'cause': 'Insufficient permissions to access resource',
                'fix': 'Check file permissions and user access rights'
            },
            r'404.*not.*found': {
                'cause': 'Requested resource does not exist',
                'fix': 'Verify URL/path is correct and resource exists'
            },
            r'memory.*error|out.*of.*memory': {
                'cause': 'Insufficient memory available',
                'fix': 'Increase memory allocation or optimize memory usage'
            }
        }
    
    def analyze(self, anomaly: LogAnomaly) -> Dict[str, Any]:
        """
        Perform root cause analysis on an anomaly.
        
        Args:
            anomaly: LogAnomaly to analyze
            
        Returns:
            Dictionary with RCA results
        """
        # Pattern-based analysis
        pattern_results = self._pattern_based_analysis(anomaly)
        
        # If LLM is available, use it for deeper analysis
        if self.llm_client and len(anomaly.log_entries) > 0:
            llm_results = self._llm_based_analysis(anomaly)
            return {
                **pattern_results,
                'llm_analysis': llm_results,
                'confidence': 'high'
            }
        
        return {
            **pattern_results,
            'confidence': 'medium'
        }
    
    def _pattern_based_analysis(self, anomaly: LogAnomaly) -> Dict[str, Any]:
        """Analyze anomaly using pattern matching."""
        for log_entry in anomaly.log_entries:
            message_lower = log_entry.message.lower()
            
            for pattern, info in self.error_patterns.items():
                if re.search(pattern, message_lower):
                    return {
                        'root_cause': info['cause'],
                        'recommended_fix': info['fix'],
                        'matched_pattern': pattern,
                        'analysis_method': 'pattern_matching'
                    }
        
        # No pattern matched
        return {
            'root_cause': anomaly.root_cause or 'Unable to determine root cause automatically',
            'recommended_fix': anomaly.recommendation or 'Manual investigation required',
            'matched_pattern': None,
            'analysis_method': 'heuristic'
        }
    
    def _llm_based_analysis(self, anomaly: LogAnomaly) -> str:
        """
        Use LLM for advanced root cause analysis.
        This is a placeholder for LLM integration.
        """
        # In production, send logs to Claude/GPT-4 for analysis
        prompt = f"""
        Analyze the following log anomaly and provide root cause analysis:
        
        Component: {anomaly.affected_component}
        Anomaly Type: {anomaly.anomaly_type}
        Severity: {anomaly.severity}
        
        Recent logs:
        {chr(10).join([log.message for log in anomaly.log_entries[-5:]])}
        
        Provide:
        1. Root cause
        2. Impact assessment
        3. Recommended fix
        """
        
        # Placeholder response
        return "LLM analysis not configured. Configure Claude/GPT-4 API for advanced analysis."


class LogMonitoringService:
    """
    Main service for log monitoring and anomaly detection.
    """
    
    def __init__(self):
        self.parser = LogParser()
        self.detector = LogBERTDetector()
        self.rca = RootCauseAnalyzer()
        self.historical_logs = []
    
    def train_on_historical_data(self, log_lines: List[str]):
        """Train detector on historical normal logs."""
        entries = self.parser.parse_logs(log_lines)
        self.historical_logs = entries
        self.detector.learn_baseline(entries)
        logger.info(f"Trained on {len(entries)} historical log entries")
    
    def analyze_logs(self, log_lines: List[str]) -> Dict[str, Any]:
        """
        Analyze new logs and detect anomalies.
        
        Args:
            log_lines: List of raw log lines
            
        Returns:
            Analysis results with detected anomalies
        """
        # Parse logs
        entries = self.parser.parse_logs(log_lines)
        
        # Detect anomalies
        anomalies = self.detector.detect_anomalies(entries)
        
        # Perform RCA on anomalies
        analyzed_anomalies = []
        for anomaly in anomalies:
            rca_result = self.rca.analyze(anomaly)
            anomaly_dict = anomaly.to_dict()
            anomaly_dict['rca'] = rca_result
            analyzed_anomalies.append(anomaly_dict)
        
        return {
            'total_logs': len(entries),
            'anomalies_detected': len(anomalies),
            'anomalies': analyzed_anomalies,
            'timestamp': datetime.utcnow().isoformat(),
            'log_summary': {
                'errors': sum(1 for e in entries if e.level in ['ERROR', 'CRITICAL']),
                'warnings': sum(1 for e in entries if e.level == 'WARNING'),
                'info': sum(1 for e in entries if e.level == 'INFO')
            }
        }
