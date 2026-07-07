"""
deploy_pipelines.py — Deploy all 3 ADHDQuest pipelines to RocketRide Cloud.

Usage:
    python deploy_pipelines.py

This connects to the RocketRide cloud using the credentials in .env,
uploads each .pipe canvas file, and prints the live webhook trigger URL
for each pipeline so you can paste them into .env.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from rocketride import RocketRideClient

# Load env from the root .env file
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

PIPES_DIR = Path(__file__).parent / "pipes"

PIPELINES = [
    {
        "name": "Pipeline 1 — Ingestion & Game Generation",
        "file": "pipeline1_ingestion.pipe",
        "env_key": "PIPELINE1_WEBHOOK_URL",
    },
    {
        "name": "Pipeline 2 — Struggle Replan",
        "file": "pipeline2_replan.pipe",
        "env_key": "PIPELINE2_WEBHOOK_URL",
    },
    {
        "name": "Pipeline 3 — Memory & Report",
        "file": "pipeline3_memory_report.pipe",
        "env_key": "PIPELINE3_WEBHOOK_URL",
    },
]


async def deploy_all():
    uri = os.getenv("ROCKETRIDE_URI", "https://api.rocketride.ai")
    apikey = os.getenv("ROCKETRIDE_APIKEY", "")

    print(f"Connecting to RocketRide at {uri} ...")
    client = RocketRideClient(uri=uri, auth=apikey)

    try:
        await client.connect()
        print("✓ Connected!\n")

        results = {}
        for p in PIPELINES:
            pipe_path = PIPES_DIR / p["file"]
            print(f"Deploying {p['name']} ({p['file']}) ...")
            try:
                result = await client.use(filepath=str(pipe_path))
                token = result.get("token", "")
                # The webhook URL is constructed from the project_id and the webhook component
                # RocketRide auto-creates a webhook endpoint when the pipeline starts.
                print(f"  ✓ Started  token={token}")
                results[p["env_key"]] = token
            except Exception as e:
                print(f"  ✗ Failed: {e}")

        print("\n=== Paste these into your .env ===")
        for key, token in results.items():
            print(f"{key}={token}")

    finally:
        await client.disconnect()
        print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(deploy_all())
