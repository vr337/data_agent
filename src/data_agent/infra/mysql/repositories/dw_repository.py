from sys import version
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DwRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_column_type_dict(self, table_name: str) -> dict[str, str]:
        """
        获取对应表的字段名与字段类型的映射字典
        Args:
            table_name (str): 表名

        Returns:
            dict[str,str]: 字段名与字段类型的映射字典
        """
        sql = f"show columns from {table_name}"
        result = await self._session.execute(text(sql))

        return {row.Field: row.Type for row in result.all()}

    async def get_column_values(
        self, table_name: str, column_name: str, limit: int = 10
    ) -> list[Any]:
        """
        获取对应表中的指定字段的前limit条数据,不包含重复的数据

        Args:
            table_name (str): 表名
            column_name (str): 字段名
            limit (int): 前几条数据，默认前10条

        Returns:
            list[Any]: 前十条数据构成的列表
        """
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self._session.execute(text(sql))

        # 如果不用ORM对象查询的话，返回的就是查询的第一个字段的值构成的列表
        return result.scalars().all()

    async def get_db_info(self) -> dict[str, str]:
        """
        获取数据库信息

        Returns:
            dict[str,str]: {"version":"数据库版本","dialect":"方言(Mysql、PostSql...)"}
        """
        return {
            "version": (await self._session.execute(text("select version()"))).scalar(),
            "dialect": self._session.get_bind().dialect.name,
        }

    async def validate_sql(self, sql: str) -> None:
        """
        使用explain 关键字校验sql
            它利用数据库的解析器，能发现表不存在、字段名、JOIN 语法错误等实际问题
            不会执行SQL,校验失败会抛出异常

        Args:
            sql (str): sql语句
        """
        await self._session.execute(text(f"explain {sql}"))

    async def execute_sql(self, sql: str) -> list[dict[str, Any]]:
        """
        执行sql

        Args:
            sql (str): sql语句

        Returns:
            list[dict[str, Any]]: sql执行结果，方便序列化
        """
        result = await self._session.execute(text(sql))
        # return result.mappings().all()   #rowMapping对象  不能直接序列化
        return [dict(row_mapping) for row_mapping in result.mappings().all()]
