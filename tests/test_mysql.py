import asyncio

from sqlalchemy import text

from data_agent.core.configs.app_config import app_config
from data_agent.infra.mysql.manager import MySqlClientManager

if __name__ == "__main__":
   
   

    async def test():
        dw_mysql_manager = MySqlClientManager(app_config.db_dw)
        dw_mysql_manager.init_db()                       
        async with  dw_mysql_manager.session_factory() as session:
            result = await session.execute(text("select * from dim_customer limit 2"))
            print(result.all(),type(result.all()))
            print(result.mappings().all(),type(result.mappings().all()))
            print(result.scalars().all())
        await dw_mysql_manager.close()
                                    
    asyncio.run(test())

