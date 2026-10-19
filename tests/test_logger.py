import asyncio

from data_agent.core.context import get_request_id, set_request_id
from src.data_agent.core.logger import logger

if __name__ == "__main__":

    async def req1():
        # 接收到请求
        set_request_id("111")
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_request_id())

    async def req2():
        # 接收到请求
        set_request_id("222")
        # 模拟处理
        await asyncio.sleep(1)
        logger.info(get_request_id())

    async def test():
        await asyncio.gather(req1(), req2())

    asyncio.run(test())
