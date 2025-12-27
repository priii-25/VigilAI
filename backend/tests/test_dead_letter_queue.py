"""
Tests for Dead Letter Queue implementation
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


class MockRedis:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {}
        self.sorted_sets = {}
        self.lists = {}
        self.hashes = {}
    
    async def get(self, key):
        return self.data.get(key)
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
    
    async def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0
    
    async def zadd(self, key, mapping):
        if key not in self.sorted_sets:
            self.sorted_sets[key] = {}
        self.sorted_sets[key].update(mapping)
    
    async def zrangebyscore(self, key, min_score, max_score, start=0, num=100):
        if key not in self.sorted_sets:
            return []
        items = []
        for member, score in self.sorted_sets[key].items():
            if (min_score == "-inf" or score >= float(min_score)) and \
               (max_score == "+inf" or score <= float(max_score)):
                items.append(member)
        return items[:num]
    
    async def zrem(self, key, member):
        if key in self.sorted_sets and member in self.sorted_sets[key]:
            del self.sorted_sets[key][member]
            return 1
        return 0
    
    async def zcard(self, key):
        return len(self.sorted_sets.get(key, {}))
    
    async def lpush(self, key, value):
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)
    
    async def lrange(self, key, start, end):
        if key not in self.lists:
            return []
        if end == -1:
            return self.lists[key][start:]
        return self.lists[key][start:end+1]
    
    async def llen(self, key):
        return len(self.lists.get(key, []))
    
    async def lrem(self, key, count, value):
        if key in self.lists and value in self.lists[key]:
            self.lists[key].remove(value)
            return 1
        return 0
    
    async def hgetall(self, key):
        return self.hashes.get(key, {})
    
    async def hincrby(self, key, field, amount):
        if key not in self.hashes:
            self.hashes[key] = {}
        if field not in self.hashes[key]:
            self.hashes[key][field] = 0
        self.hashes[key][field] += amount
        return self.hashes[key][field]


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue class"""
    
    @pytest.fixture
    def redis_mock(self):
        return MockRedis()
    
    @pytest.fixture
    def dlq(self, redis_mock):
        from src.core.dead_letter_queue import DeadLetterQueue
        return DeadLetterQueue(redis_mock, max_retries=3)
    
    @pytest.mark.asyncio
    async def test_add_failed_task_schedules_retry(self, dlq):
        """Failed task should be scheduled for retry"""
        task_id = await dlq.add_failed_task(
            task_name="test_task",
            task_args={"key": "value"},
            error="Test error"
        )
        
        assert task_id is not None
        
        stats = await dlq.get_stats()
        assert stats["pending_retry_count"] == 1
        assert stats["dead_letter_count"] == 0
    
    @pytest.mark.asyncio
    async def test_add_failed_task_moves_to_dlq_after_max_retries(self, dlq):
        """Failed task should move to DLQ after max retries"""
        await dlq.add_failed_task(
            task_name="test_task",
            task_args={"key": "value"},
            error="Test error",
            retry_count=3  # Already at max
        )
        
        stats = await dlq.get_stats()
        assert stats["dead_letter_count"] == 1
        assert stats["pending_retry_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_pending_retries_returns_due_tasks(self, dlq, redis_mock):
        """Should return tasks that are due for retry"""
        # Add task with immediate retry
        task_data = {
            "id": "test:1",
            "task_name": "test_task",
            "args": {},
            "error": "error",
            "retry_count": 0,
            "failed_at": datetime.utcnow().isoformat(),
            "status": "pending_retry"
        }
        
        # Set retry time to now
        await redis_mock.zadd(
            "vigilai:dlq:retry_queue",
            {json.dumps(task_data): datetime.utcnow().timestamp()}
        )
        
        pending = await dlq.get_pending_retries()
        assert len(pending) == 1
        assert pending[0]["task_name"] == "test_task"
    
    @pytest.mark.asyncio
    async def test_get_dead_letters_returns_failed_tasks(self, dlq):
        """Should return tasks in DLQ"""
        await dlq.add_failed_task(
            task_name="dead_task",
            task_args={"id": 1},
            error="Fatal error",
            retry_count=3
        )
        
        dead_letters = await dlq.get_dead_letters()
        assert len(dead_letters) == 1
        assert dead_letters[0]["task_name"] == "dead_task"
    
    @pytest.mark.asyncio
    async def test_retry_dead_letter_requeues_task(self, dlq):
        """Should requeue a dead letter for retry"""
        await dlq.add_failed_task(
            task_name="retry_me",
            task_args={"id": 1},
            error="error",
            retry_count=3,
            task_id="retry:1"
        )
        
        # Retry the dead letter
        success = await dlq.retry_dead_letter("retry:1")
        assert success is True
        
        stats = await dlq.get_stats()
        assert stats["dead_letter_count"] == 0
        assert stats["pending_retry_count"] == 1
    
    @pytest.mark.asyncio
    async def test_delete_dead_letter_removes_task(self, dlq):
        """Should delete a dead letter permanently"""
        await dlq.add_failed_task(
            task_name="delete_me",
            task_args={},
            error="error",
            retry_count=3,
            task_id="delete:1"
        )
        
        success = await dlq.delete_dead_letter("delete:1")
        assert success is True
        
        stats = await dlq.get_stats()
        assert stats["dead_letter_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_stats_returns_counts(self, dlq):
        """Should return accurate statistics"""
        # Add some tasks
        await dlq.add_failed_task("task1", {}, "error1", retry_count=0)
        await dlq.add_failed_task("task2", {}, "error2", retry_count=3)
        
        stats = await dlq.get_stats()
        
        assert "dead_letter_count" in stats
        assert "pending_retry_count" in stats
        assert "total_retries_scheduled" in stats
