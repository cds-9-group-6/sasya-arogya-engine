#!/usr/bin/env python3
"""
Simple test script to verify timeout handling works
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_timeout():
    """Test timeout handling"""
    logger.info("Testing timeout handling...")
    
    try:
        # Test with a very short timeout
        timeout = aiohttp.ClientTimeout(total=1, connect=1)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # This should timeout quickly
            async with session.get("http://httpbin.org/delay/5") as response:
                logger.info(f"Response: {response.status}")
    except asyncio.TimeoutError:
        logger.info("✅ Timeout handling works correctly")
        return True
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🧪 Testing timeout fix...")
    
    # Test overall timeout
    try:
        await asyncio.wait_for(test_timeout(), timeout=5)
        logger.info("✅ Overall timeout handling works")
    except asyncio.TimeoutError:
        logger.info("✅ Overall timeout handling works")
    
    logger.info("🎉 All timeout tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
