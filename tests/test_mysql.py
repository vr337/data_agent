import asyncio

from sqlalchemy import text

from data_agent.infra.mysql.manager import get_dw_mysql_manager

if __name__ == "__main__":
   
   

    async def test():
        # 初始化dw客户端对象
        dw_mysql_manager=get_dw_mysql_manager()
        dw_mysql_manager.init_db()

        # 创建异步会话
        async with dw_mysql_manager.session_factory() as session:
            # 执行查询sql
            sql = "select * from dim_customer limit 2"
            result = await session.execute(text(sql))

            # 读取数据
            """
            result.all()    返回 [row, row, row]  row是可迭代的对象
            result.mappings().all() 返回 [rowMapping, rowMapping, rowMapping]  rowMapping是包含一行数据的字段名和字段值的对象
            result.scalars().all() 所回 [val, val, val]  val是第一列值
            """

            rows = result.all()  # 返回 [row, row, row]   row是可迭代的对象
            for row in rows:
                for val in row:
                    print(val)

            rows = result.mappings().all() # 返回 [rowMapping, rowMapping, rowMapping]  rowMapping是包含一行数据的字段名和字段值的对象
            for row in rows:
                for key, val in row.items():
                    print(key, val)

            rows = result.scalars().all()  # 所回 [val, val, val]  val是第一列值
            for row in rows:
                print(row)

        # 释放资源
        await dw_mysql_manager.close()

    asyncio.run(test())

