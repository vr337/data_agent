import asyncio
from pathlib import Path

from data_agent.scripts.build_meta_knowledge import start_build


async def test():
    meta_config_path = Path(__file__).parents[2] / "configs" / "meta_config.yml"
    await start_build(meta_config_path)


if __name__ == "__main__":
    asyncio.run(test())
