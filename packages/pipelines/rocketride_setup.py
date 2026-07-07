import os
import json
import asyncio
from dotenv import load_dotenv
from rocketride import RocketRideClient

load_dotenv(dotenv_path="/Users/mohit/adhdQuest/.env")

uri = os.getenv("ROCKETRIDE_URI")
apikey = os.getenv("ROCKETRIDE_APIKEY")

async def main():
    print("Initializing RocketRideClient with URI:", uri)
    try:
        client = RocketRideClient(uri=uri, auth=apikey)
        print("Listing existing deployments...")
        deployments = await client.deploy.list()
        print("Deployments list:", deployments)
    except Exception as e:
        print("Failed to communicate with RocketRide server:", e)

if __name__ == "__main__":
    asyncio.run(main())
