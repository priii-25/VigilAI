import sys
import os
import asyncio
import requests
import json

# We'll test via direct service instantiation since server is running but we want quick feedback
# Actually, since server is running, let's curl the endpoints if possible, but we need auth.
# Simpler to test the Services directly in a script.

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ai.simulator import ScenarioSimulator
from src.services.ai.drift_detector import StrategyDriftDetector

async def test_services():
    print("\n--- Testing Scenario Simulator ---")
    sim = ScenarioSimulator()
    result = await sim.run_simulation(
        "Stripe", 
        "Stripe lowers processing fees to 1.5% for all startups."
    )
    print("Simulation Result:")
    print(json.dumps(result.get('prediction', {}), indent=2))

    print("\n--- Testing Strategy Drift (Mock) ---")
    # This might fail if no vectors exist, but checks instantiation
    detector = StrategyDriftDetector()
    # Mocking calling detect for ID 1 (assuming it exists or returns empty)
    try:
        drift = await detector.detect_drift(1)
        print("Drift Result:", drift)
    except Exception as e:
        print(f"Drift detection skipped (expected if no DB data): {e}")

if __name__ == "__main__":
    asyncio.run(test_services())
