from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_agent.infra.mysql.models.column_info import ColumnInfoORM
from data_agent.infra.mysql.models.column_metric import ColumnMetricORM
from data_agent.infra.mysql.models.metric_info import MetricInfoORM
from data_agent.infra.mysql.models.table_info import TableInfoORM


class MetaRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def save_table_infos(self, table_infos: list[TableInfoORM]) -> None:
        """
        保存表信息到meta数据库中的table_info表中
        Args:
            table_infos (list[TableInfoORM]): 表信息
        """

        self._session.add_all(table_infos)

    def save_column_infos(self, column_infos: list[ColumnInfoORM]) -> None:
        """
        保存字段信息到meta数据库中的column_info表中
        Args:
            column_infos (list[ColumnInfoORM]): _description_
        """
        self._session.add_all(column_infos)

    def save_metric_infos(self, metric_infos: list[MetricInfoORM]) -> None:
        """
        保存指标信息到meta数据库中的metric_info表中

        Args:
            metric_infos (list[MetricInfoORM]): 指标信息
        """
        self._session.add_all(metric_infos)

    def save_column_metrics(self, column_metrics: list[ColumnMetricORM]) -> None:
        """
        保存字段指标信息到meta数据库中的column_metric表中，来关联字段信息和指标信息

        Args:
            column_metrics (list[ColumnMetricORM]): 字段指标信息
        """
        self._session.add_all(column_metrics)

    async def get_column_info_by_id(self, column_id: str) -> ColumnInfoORM:
        """
        通过字段id在meta数据库column_info表查询对应的字段信息

        Args:
            column_id (str): 字段id

        Returns:
            ColumnInfoORM: 数据库里的完整的字段信息
        """

        return await self._session.get(ColumnInfoORM, column_id)

    async def get_key_column_infos_by_table_id(self, table_id) -> list[ColumnInfoORM]:
        """通过table_id查询对应的主键和外键字段信息列表

        Args:
            table_id (_type_): 表id

        Returns:
            list[ColumnInfoORM]: 字段列表
        """

        return (
            (
                await self._session.execute(
                    select(ColumnInfoORM)
                    .where(ColumnInfoORM.table_id == table_id)
                    .where(ColumnInfoORM.role.in_(["primary_key", "foreign_key"]))
                )
            )
            .scalars()
            .all()
        )
    async def get_table_infos_by_id(self,table_id:str)->TableInfoORM:
        """根据table_id获取对应的表信息

        Args:
            table_id (str): 表id

        Returns:
            TableInfoORM: 表信息
        """
        return await self._session.get(TableInfoORM,table_id)
