# Sequentum Bridge — Redis Queue → Sequentum API
# Polls Redis for Sequentum tasks, calls Sequentum Enterprise API on Windows host.
# Runs in Docker, communicates with Sequentum on host via host.docker.internal.

import asyncio
import os
import json
import time
import httpx
import redis.asyncio as redis

SEQUENTUM_API = os.getenv("SEQUENTUM_API", "http://host.docker.internal:8081/api")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = "sequentum:tasks"
RESULT_KEY = "sequentum:results"

redis_client = redis.from_url(REDIS_URL)

async def run_sequentum_agent(agent_name: str, inputs: dict) -> dict:
    """Start a Sequentum agent, poll until complete, return results."""
    async with httpx.AsyncClient(timeout=7200) as client:
        # 1. Start agent
        resp = await client.post(f"{SEQUENTUM_API}/agents/run", json={
            "agentName": agent_name, "inputs": inputs
        })
        resp.raise_for_status()
        run_id = resp.json()["runId"]

        # 2. Poll until done
        while True:
            status_resp = await client.get(f"{SEQUENTUM_API}/runs/{run_id}/status")
            status = status_resp.json()
            if status["status"] == "completed":
                break
            if status["status"] in ("failed", "error"):
                raise Exception(f"Sequentum run failed: {status.get('error')}")
            await asyncio.sleep(5)

        # 3. Fetch results
        data_resp = await client.get(f"{SEQUENTUM_API}/runs/{run_id}/data")
        return {"success": True, "data": data_resp.json()["rows"]}

async def main():
    print(f"Sequentum bridge starting. API: {SEQUENTUM_API}")
    while True:
        # Block until a task arrives
        result = await redis_client.blpop(QUEUE_KEY, timeout=60)
        if result is None:
            continue

        _, task_json = result
        task = json.loads(task_json)
        task_id = task.get("id", "unknown")
        agent = task["agent"]
        inputs = task.get("inputs", {})

        print(f"Processing task {task_id}: {agent} with {json.dumps(inputs)[:100]}")

        try:
            output = await run_sequentum_agent(agent, inputs)
            await redis_client.hset(RESULT_KEY, task_id, json.dumps(output))
            print(f"Task {task_id} completed successfully")
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            await redis_client.hset(RESULT_KEY, task_id, json.dumps(error_result))
            print(f"Task {task_id} failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
