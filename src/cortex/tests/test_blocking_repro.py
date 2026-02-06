import pytest
import asyncio
import time
import json
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from cortex.cortex.server import app, IPPOC_API_KEY

@pytest.mark.asyncio
async def test_blocking_io_behavior():
    # Helper to simulate slow JSON loading
    def slow_json_load(fp):
        time.sleep(1.0)
        return {"data": "mock"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        # Patch json.load to simulate blocking
        with patch("json.load", side_effect=slow_json_load):
            # We also need to patch os.path.exists and open to avoid FileNotFoundError
            with patch("os.path.exists", return_value=True), \
                 patch("builtins.open", new_callable=MagicMock):

                headers = {"Authorization": f"Bearer {IPPOC_API_KEY}"}

                start_time = time.monotonic()

                # Launch the slow request in background
                task_slow = asyncio.create_task(ac.get("/v1/orchestrator/explain/latest", headers=headers))

                # Give it a tiny bit of time to start and reach the blocking call
                await asyncio.sleep(0.1)

                # Launch the fast request
                resp_fast = await ac.get("/healthz")

                end_time = time.monotonic()
                duration = end_time - start_time

                await task_slow

                print(f"Healthz duration including overlap: {duration:.4f}s")

                assert resp_fast.status_code == 200

                # If blocking, the duration should be roughly 1.0s + overhead
                # If non-blocking, the duration should be roughly 0.1s (the sleep) + overhead

                # This assertion expects NON-BLOCKING behavior (OPTIMIZED)
                # We allow some buffer, but it should be significantly less than 1.0s
                assert duration < 0.5, f"Expected non-blocking behavior (<0.5s), but got {duration}s"
