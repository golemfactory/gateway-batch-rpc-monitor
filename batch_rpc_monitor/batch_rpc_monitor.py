import asyncio
import time
import json
import logging
import aiohttp

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def main():
    print("Starting")
    await asyncio.sleep(1)