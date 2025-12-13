"""
OpenStack Log Dataset Integration
Integrates with LogHub OpenStack dataset for training and validation.
Reference: https://github.com/logpai/loghub
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import os
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpenStackLogEntry:
    """Parsed OpenStack log entry."""
    timestamp: Optional[datetime]
    level: str
    component: str
    message: str
    raw_log: str
    is_anomaly: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'is_anomaly': self.is_anomaly
        }


class OpenStackLogParser:
    """
    Parser for OpenStack log format.
    Handles logs from Nova, Neutron, Cinder, and other OpenStack services.
    """
    
    # OpenStack log format: timestamp level component message
    LOG_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+'  # timestamp
        r'(\d+)\s+'  # process id
        r'(\w+)\s+'  # log level
        r'([\w\.]+)\s+'  # component
        r'\[.*?\]\s+'  # request id
        r'(.+)'  # message
    )
    
    # Alternative simpler pattern
    SIMPLE_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'(\w+)\s+'  # level
        r'(.+)'  # message
    )
    
    # Anomaly indicators in OpenStack logs
    ANOMALY_KEYWORDS = [
        'error', 'exception', 'fail', 'timeout', 'refused',
        'critical', 'fatal', 'traceback', 'unable to',
        'cannot', 'not found', 'denied', 'unauthorized'
    ]
    
    def parse_log_line(self, line: str) -> Optional[OpenStackLogEntry]:
        """Parse a single OpenStack log line."""
        line = line.strip()
        if not line:
            return None
        
        # Try main pattern first
        match = self.LOG_PATTERN.match(line)
        if match:
            timestamp_str, pid, level, component, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except:
                timestamp = None
            
            return OpenStackLogEntry(
                timestamp=timestamp,
                level=level.upper(),
                component=component,
                message=message,
                raw_log=line,
                is_anomaly=self._is_anomaly(line)
            )
        
        # Try simpler pattern
        match = self.SIMPLE_PATTERN.match(line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                timestamp = None
            
            return OpenStackLogEntry(
                timestamp=timestamp,
                level=level.upper(),
                component='unknown',
                message=message,
                raw_log=line,
                is_anomaly=self._is_anomaly(line)
            )
        
        # Return as unparsed
        return OpenStackLogEntry(
            timestamp=None,
            level='INFO',
            component='unknown',
            message=line,
            raw_log=line,
            is_anomaly=self._is_anomaly(line)
        )
    
    def _is_anomaly(self, log_line: str) -> bool:
        """Detect if log line indicates an anomaly."""
        log_lower = log_line.lower()
        return any(keyword in log_lower for keyword in self.ANOMALY_KEYWORDS)
    
    def parse_log_file(self, file_path: str) -> List[OpenStackLogEntry]:
        """Parse all logs from a file."""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    entry = self.parse_log_line(line)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error(f"Error parsing log file {file_path}: {str(e)}")
        
        return entries


class OpenStackDatasetLoader:
    """
    Loader for LogHub OpenStack dataset.
    Reference: https://github.com/logpai/loghub
    """
    
    # LogHub raw data URLs (sample)
    LOGHUB_BASE = "https://raw.githubusercontent.com/logpai/loghub/master"
    DATASETS = {
        'openstack_normal': f"{LOGHUB_BASE}/OpenStack/OpenStack_2k.log",
        'openstack_full': f"{LOGHUB_BASE}/OpenStack/OpenStack.log"
    }
    
    def __init__(self, cache_dir: str = "./data/loghub"):
        self.cache_dir = cache_dir
        self.parser = OpenStackLogParser()
        os.makedirs(cache_dir, exist_ok=True)
    
    def download_dataset(self, dataset_name: str = 'openstack_normal') -> Optional[str]:
        """
        Download dataset from LogHub.
        
        Args:
            dataset_name: Name of dataset to download
            
        Returns:
            Path to downloaded file
        """
        if dataset_name not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset_name}")
            return None
        
        url = self.DATASETS[dataset_name]
        filename = f"{dataset_name}.log"
        filepath = os.path.join(self.cache_dir, filename)
        
        # Check cache
        if os.path.exists(filepath):
            logger.info(f"Using cached dataset: {filepath}")
            return filepath
        
        try:
            logger.info(f"Downloading dataset from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Dataset saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {str(e)}")
            return None
    
    def load_training_data(
        self,
        dataset_name: str = 'openstack_normal',
        max_samples: int = None
    ) -> Dict[str, Any]:
        """
        Load and prepare training data from OpenStack logs.
        
        Args:
            dataset_name: Dataset to load
            max_samples: Maximum number of samples to return
            
        Returns:
            Dict with training data and statistics
        """
        # Download if needed
        filepath = self.download_dataset(dataset_name)
        
        if not filepath:
            # Return synthetic sample data
            return self._generate_synthetic_data(max_samples or 100)
        
        # Parse logs
        entries = self.parser.parse_log_file(filepath)
        
        if max_samples:
            entries = entries[:max_samples]
        
        # Separate normal and anomaly logs
        normal_logs = [e.raw_log for e in entries if not e.is_anomaly]
        anomaly_logs = [e.raw_log for e in entries if e.is_anomaly]
        
        # Calculate statistics
        stats = self._calculate_stats(entries)
        
        return {
            'total_samples': len(entries),
            'normal_logs': normal_logs,
            'anomaly_logs': anomaly_logs,
            'normal_count': len(normal_logs),
            'anomaly_count': len(anomaly_logs),
            'anomaly_ratio': len(anomaly_logs) / len(entries) if entries else 0,
            'statistics': stats,
            'source': dataset_name
        }
    
    def _calculate_stats(self, entries: List[OpenStackLogEntry]) -> Dict[str, Any]:
        """Calculate dataset statistics."""
        levels = {}
        components = {}
        
        for entry in entries:
            levels[entry.level] = levels.get(entry.level, 0) + 1
            components[entry.component] = components.get(entry.component, 0) + 1
        
        return {
            'by_level': levels,
            'by_component': dict(sorted(components.items(), key=lambda x: x[1], reverse=True)[:10]),
            'total_entries': len(entries)
        }
    
    def _generate_synthetic_data(self, count: int) -> Dict[str, Any]:
        """Generate synthetic OpenStack-style logs for demo."""
        import random
        
        templates = {
            'normal': [
                "2024-01-15 10:30:00 INFO nova.compute Creating instance abc-123",
                "2024-01-15 10:30:01 DEBUG nova.virt.libvirt Instance spawned successfully",
                "2024-01-15 10:30:02 INFO neutron.agent Network agent started",
                "2024-01-15 10:30:03 INFO cinder.volume Volume attached to instance",
                "2024-01-15 10:30:04 DEBUG keystone.auth Token validated successfully",
                "2024-01-15 10:30:05 INFO glance.store Image download completed"
            ],
            'anomaly': [
                "2024-01-15 10:30:06 ERROR nova.compute Failed to spawn instance: Timeout",
                "2024-01-15 10:30:07 CRITICAL neutron.agent Connection refused to message broker",
                "2024-01-15 10:30:08 ERROR cinder.volume Unable to attach volume: disk full",
                "2024-01-15 10:30:09 ERROR keystone.auth Authentication failed: invalid token",
                "2024-01-15 10:30:10 ERROR glance.store Image not found in store"
            ]
        }
        
        normal_logs = [random.choice(templates['normal']) for _ in range(int(count * 0.9))]
        anomaly_logs = [random.choice(templates['anomaly']) for _ in range(int(count * 0.1))]
        
        return {
            'total_samples': count,
            'normal_logs': normal_logs,
            'anomaly_logs': anomaly_logs,
            'normal_count': len(normal_logs),
            'anomaly_count': len(anomaly_logs),
            'anomaly_ratio': len(anomaly_logs) / count,
            'statistics': {'by_level': {'INFO': int(count * 0.6), 'DEBUG': int(count * 0.2), 'ERROR': int(count * 0.2)}},
            'source': 'synthetic'
        }


class OpenStackLogTrainer:
    """
    Trainer for anomaly detection models on OpenStack logs.
    """
    
    def __init__(self):
        self.dataset_loader = OpenStackDatasetLoader()
    
    def prepare_training_data(
        self,
        train_ratio: float = 0.8
    ) -> Dict[str, Any]:
        """
        Prepare train/validation split for model training.
        
        Args:
            train_ratio: Ratio of data for training
            
        Returns:
            Dict with train and validation sets
        """
        data = self.dataset_loader.load_training_data()
        
        normal_logs = data['normal_logs']
        anomaly_logs = data['anomaly_logs']
        
        # Split normal logs
        split_idx = int(len(normal_logs) * train_ratio)
        train_normal = normal_logs[:split_idx]
        val_normal = normal_logs[split_idx:]
        
        # Split anomaly logs
        split_idx = int(len(anomaly_logs) * train_ratio)
        train_anomaly = anomaly_logs[:split_idx]
        val_anomaly = anomaly_logs[split_idx:]
        
        return {
            'train': {
                'normal': train_normal,
                'anomaly': train_anomaly,
                'total': len(train_normal) + len(train_anomaly)
            },
            'validation': {
                'normal': val_normal,
                'anomaly': val_anomaly,
                'total': len(val_normal) + len(val_anomaly)
            },
            'statistics': data['statistics']
        }
    
    def train_logbert(self, save_path: str = "./models/trained/logbert.pt"):
        """
        Train LogBERT model on OpenStack logs.
        
        Args:
            save_path: Path to save trained model
        """
        data = self.prepare_training_data()
        
        logger.info(f"Training on {data['train']['total']} samples")
        logger.info(f"Validation set: {data['validation']['total']} samples")
        
        # Training would happen here
        # For now, log the intention
        logger.info(f"Model would be saved to {save_path}")
        
        return {
            'status': 'ready_for_training',
            'train_samples': data['train']['total'],
            'val_samples': data['validation']['total'],
            'save_path': save_path
        }


# Convenience functions
def get_openstack_loader() -> OpenStackDatasetLoader:
    return OpenStackDatasetLoader()


def get_openstack_trainer() -> OpenStackLogTrainer:
    return OpenStackLogTrainer()
