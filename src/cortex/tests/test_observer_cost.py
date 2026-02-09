
import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.getcwd() + "/src")

from cortex.maintainer import observer
from cortex.maintainer.types import PressureSource
from cortex.core.economy import EconomyManager

# --- Test Case 1: Economy Implementation ---
def test_economy_moving_average():
    # Verify EconomyManager.get_moving_average_cost works as expected
    print("Testing EconomyManager.get_moving_average_cost...")

    # We patch _load to avoid reading from disk/environment
    with patch.object(EconomyManager, "_load") as mock_load:
        # Create a dummy state object
        from cortex.core.economy import EconomyState
        mock_load.return_value = EconomyState(budget=100.0, reserve=100.0)

        # Mock os.getenv to avoid "economy_writer" thread issues if needed
        # But ThreadPoolExecutor is fine.

        eco = EconomyManager(path="dummy.json")

        # 1. No events -> 0.0
        assert eco.get_moving_average_cost() == 0.0

        # 2. Add some events manually
        eco.state.events = []
        eco.state.events.append({"kind": "spend", "cost": 10.0})
        eco.state.events.append({"kind": "spend", "cost": 20.0})
        eco.state.events.append({"kind": "other", "cost": 999.0}) # Should be ignored

        # Avg = (10+20)/2 = 15.0
        assert eco.get_moving_average_cost() == 15.0

        # 3. Test window
        eco.state.events.append({"kind": "spend", "cost": 30.0})
        # All 3: (10+20+30)/3 = 20.0
        assert eco.get_moving_average_cost(window=10) == 20.0

        # Window 2: (20+30)/2 = 25.0
        assert eco.get_moving_average_cost(window=2) == 25.0

    print("PASS")

# --- Test Case 2: Observer Logic ---
async def test_observer_spike_detection():
    print("Testing observer.collect_signals logic...")

    # Create AsyncMock for list_recent because it is awaited
    # However, MagicMock is not awaitable by default unless configured.
    # We can use a helper async function or AsyncMock if available (python 3.8+)

    async def mock_list_recent(limit=50):
        return mock_list_recent.return_value

    mock_list_recent.return_value = []

    mock_ledger = MagicMock()
    mock_ledger.list_recent = mock_list_recent

    mock_economy = MagicMock()

    # Patch get_ledger and get_economy in observer module
    with patch("cortex.maintainer.observer.get_ledger", return_value=mock_ledger), \
         patch("cortex.maintainer.observer.get_economy", return_value=mock_economy):

        # Scenario A: No History (Avg=0), Total Cost=4.0 (< 5.0 fallback)
        # Should NOT trigger COST pressure
        mock_economy.get_moving_average_cost.return_value = 0.0
        mock_list_recent.return_value = [{"cost_spent": 4.0, "status": "completed", "duration_ms": 10}]

        summary = await observer.collect_signals()
        assert PressureSource.COST not in summary.pressure_sources

        # Scenario B: No History, Total Cost=6.0 (> 5.0 fallback)
        # Should trigger COST pressure
        mock_list_recent.return_value = [{"cost_spent": 6.0, "status": "completed", "duration_ms": 10}]
        summary = await observer.collect_signals()
        assert PressureSource.COST in summary.pressure_sources

        # Scenario C: History Avg=1.0. Expected=1.0*10=10.0. Threshold=max(20.0, 1.0) = 20.0
        # Recent actions: 10 items of cost 1.0 -> Total 10.0.
        # 10.0 < 20.0 -> No pressure
        mock_economy.get_moving_average_cost.return_value = 1.0
        recent = [{"cost_spent": 1.0, "status": "completed", "duration_ms": 10} for _ in range(10)]
        mock_list_recent.return_value = recent

        summary = await observer.collect_signals()
        assert PressureSource.COST not in summary.pressure_sources

        # Scenario D: Spike!
        # History Avg=1.0. Expected=10.0. Threshold=20.0.
        # Total Cost = 25.0.
        recent_expensive = [{"cost_spent": 2.5, "status": "completed", "duration_ms": 10} for _ in range(10)] # Total 25.0
        mock_list_recent.return_value = recent_expensive

        summary = await observer.collect_signals()
        assert PressureSource.COST in summary.pressure_sources

        # Scenario E: Low noise floor check
        # Avg = 0.01. Expected for 1 item = 0.01. Threshold = max(0.02, 1.0) = 1.0.
        # Total Cost = 0.5.
        # 0.5 < 1.0 -> No pressure (even though 0.5 is 50x expected!)
        mock_economy.get_moving_average_cost.return_value = 0.01
        mock_list_recent.return_value = [{"cost_spent": 0.5, "status": "completed", "duration_ms": 10}]

        summary = await observer.collect_signals()
        assert PressureSource.COST not in summary.pressure_sources

    print("PASS")

if __name__ == "__main__":
    test_economy_moving_average()
    asyncio.run(test_observer_spike_detection())
