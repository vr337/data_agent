import uuid
from pathlib import Path
from typing import Any

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from data_agent.core.configs.meta_config import (
    MetricConfig,
    TableConfig,
    load_meta_config,
)
from data_agent.infra.es.models.value_info_es import ValueInfoES
from data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from data_agent.infra.mysql.models.column_info import ColumnInfoORM
from data_agent.infra.mysql.models.column_metric import ColumnMetricORM
from data_agent.infra.mysql.models.metric_info import MetricInfoORM
from data_agent.infra.mysql.models.table_info import TableInfoORM
from data_agent.infra.mysql.repositories.dw_repository import DwRepository
from data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from data_agent.infra.qdrant.models.column_info_qdrant import ColumnInfoQdrant
from data_agent.infra.qdrant.models.metric_info_qdrant import MetricInfoQdrant
from data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)
from src.data_agent.core.logger import logger


class MetaKnowledgeService:
    """
    构建元数据知识库的业务类
    """

    def __init__(
        self,
        dw_repository: DwRepository,
        meta_repository: MetaRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        value_es_repository: ValueESRepository,
        embedding_client: HuggingFaceEndpointEmbeddings,
    ):
        self._dw_repository = dw_repository
        self._meta_repository = meta_repository
        self._column_qdrant_repository = column_qdrant_repository
        self._metric_qdrant_repository = metric_qdrant_repository
        self._value_es_repository = value_es_repository
        self._embedding_client = embedding_client

    async def build(self, config_path: Path) -> None:
        """
        构建元数据知识库
        构建流程：
            1.处理表相关信息数据
                1.1.保存表信息和字段信息到数据库的meta库中
                1.2.为字段信息建立向量索引，保存到qdrant中
                1.3.为字段值信息建立全文缩影，保存到es中
            2.处理指标相关信息数据
                2.1.保存指标信息到数据库meta库中
                2.2.为指标信息建立向量索引，保存到qdrant中
        Args:
            meta_config (MetaConfig): 元数据的配置信息，信息来源于这里
        """
        logger.info("开始构建元数据知识库")

        # 加载静态元数据
        meta_config=load_meta_config(config_path)

        # 1.处理表相关信息数据
        if meta_config.tables:
            # 1.1.保存表信息和字段信息到数据库meta中的table_info和column_info表中
            column_infos: list[ColumnInfoORM] = await self._save_table_infos_to_meta_db(
                meta_config.tables
            )
            logger.info("保存表信息和字段信息到meta库成功")
            # 1.2.为字段信息建立向量索引，保存到qdrant中
            await self._save_column_infos_to_qdrant(column_infos)
            logger.info("为字段信息建立向量索引成功")
            # 1.3.为字段值信息建立全文索引，保存到es中
            await self._save_value_infos_to_es(meta_config.tables, column_infos)
            logger.info("为字段取值建立全文索引成功")
        # 2.处理指标相关信息数据
        if meta_config.metrics:
            # 2.1.保存指标信息到数据库meta库中
            metric_infos: list[
                MetricInfoORM
            ] = await self._save_metric_infos_to_meta_db(meta_config.metrics)
            logger.info("保存指标信息到meta库成功")
            # 2.2.为指标信息建立向量索引，保存到qdrant中
            await self._save_metric_infos_to_qdrant(metric_infos)
            logger.info("为指标信息建立向量索引成功")

    async def _save_table_infos_to_meta_db(
        self,
        tables: list[TableConfig],
    ) -> list[ColumnInfoORM]:
        """
        保存表信息和字段信息到数据库的meta库中
        Args:
            tables (list[TableConfig]): 表配置信息(包含字段配置信息)

        Returns:
            list[ColumnInfoORM]: 最终完整存储到数据库中的字段信息
        """
        # 1.准备存储表信息和字段信息对象的列表
        table_infos: list[TableInfoORM] = []
        column_infos: list[ColumnInfoORM] = []
        # 2.遍历tables配置信息构建表信息和字段信息
        for table in tables:
            # 拿到每个表对应的字段->类型的映射字典,再同一个表中，字段名是不可能重复的
            column_type_dict: dict[
                str, str
            ] = await self._dw_repository.get_column_type_dict(table.name)

            # 构建表信息对象添加到列表中
            table_infos.append(
                TableInfoORM(
                    id=table.name,
                    name=table.name,
                    role=table.role,
                    description=table.description,
                )
            )
            for column in table.columns:
                # 查询dw数据库，将当前字段的前十条作为数据实例
                column_values = await self._dw_repository.get_column_values(
                    table.name, column.name
                )
                column_infos.append(
                    ColumnInfoORM(
                        id=f"{table.name}.{column.name}",  # 不同表可能会出现同名字
                        name=column.name,
                        type=column_type_dict.get(column.name),  # 字段的类型
                        role=column.role,
                        examples=column_values,  # 数据实例，字段前10条数据作为例子
                        description=column.description,
                        alias=column.alias,
                        table_id=table.name,
                    )
                )
        # 保存表信息到meta数据库中
        self._meta_repository.save_table_infos(table_infos)
        # 保存字段信息到meta数据库中
        self._meta_repository.save_column_infos(column_infos)

        return column_infos

    async def _save_column_infos_to_qdrant(
        self, column_infos: list[ColumnInfoORM]
    ) -> None:
        """
        为字段信息建立向量索引，保存到qdrant中
        向量化只有name、description和alias字段，标量存储qdrant中的payload中

        Args:
            column_infos (list[ColumnInfoORM]): 最终存储到数据库中的完整的字段信息
        """

        # 1.构建要存储向量数据库Qdrant的信息,ids、payloads和vectors
        # 准备一个数组容器，存储一个字典对象（id,待向量化的文本，payload）
        data_dict_list: list[dict[str, Any]] = []
        # 遍历column_infos，创建一个字典对象({id:xx,embedding_text:xx,payload:xx})，指定相应的属性，添加到数组中
        for column_info in column_infos:
            # 构建字典对象
            column_info_qdrant = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            # 向量化只向量化name、description、alias中每个alia，每个字段信息有三种维度的语义搜索
            # 添加name对应字典
            data_dict_list.append(
                {
                    "id": uuid.uuid4().hex,
                    "embedding_text": column_info.name,
                    "payload": column_info_qdrant,
                }
            )
            # 添加description对应的字典
            data_dict_list.append(
                {
                    "id": uuid.uuid4().hex,
                    "embedding_text": column_info.description,
                    "payload": column_info_qdrant,
                }
            )
            # 添加alias对应的字典
            for alia in column_info.alias:
                data_dict_list.append(
                    {
                        "id": uuid.uuid4().hex,
                        "embedding_text": alia,
                        "payload": column_info_qdrant,
                    }
                )
            # 需要向量化的文本列表
            embedding_texts = [
                data_dict.get("embedding_text") for data_dict in data_dict_list
            ]
            # 分批，多文本嵌入
            # 最终向量化后的向量列表
            vectors: list[list[float]] = []
            batch_size = 10
            for i in range(0, len(data_dict_list), batch_size):
                batch_embedding_texts = embedding_texts[i : i + batch_size]
                # 多文本嵌入
                batch_vectors = await self._embedding_client.aembed_documents(
                    batch_embedding_texts
                )
                # 汇总所有向量
                vectors.extend(batch_vectors)
            # 最终的ids
            ids = [data_dict.get("id") for data_dict in data_dict_list]
            payloads = [data_dict.get("payload") for data_dict in data_dict_list]

        # 2.保存字段信息到Qdrant中
        await self._column_qdrant_repository.save_column_vectors(ids, payloads, vectors)

    async def _save_value_infos_to_es(
        self, tables: list[TableConfig], column_infos: list[ColumnInfoORM]
    ) -> None:
        """
        为字段值信息建立全文索引，保存到es中

        Args:
            tables (list[TableConfig]): 表信息(包含字段信息)
            column_infos (list[ColumnInfoORM]): 最终存储到数据库中的完整的字段信息
        """
        # 1.构建字段值信息列表
        column_value_infos: list[ValueInfoES] = []
        # 生成字段id与是否需要建立全文索引(存到es中)的映射字典
        column_sync_dict: dict[str, bool] = {
            f"{table.name}.{column.name}": column.sync
            for table in tables
            for column in table.columns
        }
        for column in column_infos:
            # 只有配置sync为True的字段才建立全文索引(存到es中)
            if column_sync_dict.get(column.id):
                # 根据表name、字段name检索对应字段值信息,其中limit，尽可能包含所有字段
                column_values = await self._dw_repository.get_column_values(
                    column.table_id, column.name, 10000
                )
                for column_value in column_values:
                    column_value_infos.append(
                        ValueInfoES(
                            id=f"{column.id}.{column_value}",  # 字段值id(table_name.column_name.column_value)
                            value=column_value,
                            type=column.type,
                            column_id=column.id,
                            column_name=column.name,
                            table_id=column.table_id,
                            table_name=column.table_id,
                        )
                    )
        # 2.保存字段值信息到es中
        await self._value_es_repository.save_value_infos(column_value_infos)

    async def _save_metric_infos_to_meta_db(
        self,
        metrics: list[MetricConfig],
    ) -> list[MetricInfoORM]:
        """
        保存指标信息到数据库meta库中(metric_info表和column_metric表)

        Args:
            metrics (list[MetricConfig]): 指标配置信息

        Returns:
            list[MetricInfoORM]: 最终存储到数据库中的完整的指标信息
        """

        # 1.构建指标信息列表和字段指标列表
        metric_infos: list[MetricInfoORM] = []
        column_metrics: list[ColumnMetricORM] = []
        for metric in metrics:
            metric_infos.append(
                MetricInfoORM(
                    id=metric.name,
                    name=metric.name,
                    description=metric.description,
                    relevant_columns=metric.relevant_columns,
                    alias=metric.alias,
                )
            )

            for column_id in metric.relevant_columns:
                column_metrics.append(
                    ColumnMetricORM(column_id=column_id, metric_id=metric.name)
                )

        # 2.保存指标信息到meta数据库中的metric_info表中，并同步一下column_metric中间表
        self._meta_repository.save_metric_infos(metric_infos)
        self._meta_repository.save_column_metrics(column_metrics)

        return metric_infos

    async def _save_metric_infos_to_qdrant(
        self, metric_infos: list[MetricInfoORM]
    ) -> None:
        """
        为指标信息建立向量索引，保存到qdrant中，建立索引的字段只有name、description和alias

        Args:
            metric_infos (list[MetricInfoORM]): 最终存储到数据库中的完整的指标信息
        """

        # 1.构建要存储向量数据库Qdrant的信息,ids、payloads和vectors
        # 准备一个数组容器，存储一个字典对象（id,待向量化的文本，payload）
        data_dict_list: list[dict[str, Any]] = []
        # 遍历column_infos，创建一个字典对象({id:xx,embedding_text:xx,payload:xx})，指定相应的属性，添加到数组中
        for metric_info in metric_infos:
            # 构建字典对象
            column_info_qdrant = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                relevant_columns=metric_info.relevant_columns,
                description=metric_info.description,
                alias=metric_info.alias,
            )
            # 向量化只向量化name、description、alias中每个alia，每个指标信息有三种维度的语义搜索
            # 添加name对应字典
            data_dict_list.append(
                {
                    "id": uuid.uuid4().hex,
                    "embedding_text": metric_info.name,
                    "payload": column_info_qdrant,
                }
            )
            # 添加description对应的字典
            data_dict_list.append(
                {
                    "id": uuid.uuid4().hex,
                    "embedding_text": metric_info.description,
                    "payload": column_info_qdrant,
                }
            )
            # 添加alias对应的字典
            for alia in metric_info.alias:
                data_dict_list.append(
                    {
                        "id": uuid.uuid4().hex,
                        "embedding_text": alia,
                        "payload": column_info_qdrant,
                    }
                )
            # 需要向量化的文本列表
            embedding_texts = [
                data_dict.get("embedding_text") for data_dict in data_dict_list
            ]
            # 分批，多文本嵌入
            # 最终向量化后的向量列表
            vectors: list[list[float]] = []
            batch_size = 10
            for i in range(0, len(data_dict_list), batch_size):
                batch_embedding_texts = embedding_texts[i : i + batch_size]
                # 多文本嵌入
                batch_vectors = await self._embedding_client.aembed_documents(
                    batch_embedding_texts
                )
                # 汇总所有向量
                vectors.extend(batch_vectors)
            # 最终的ids
            ids = [data_dict.get("id") for data_dict in data_dict_list]
            payloads = [data_dict.get("payload") for data_dict in data_dict_list]

        # 2.保存指标信息到Qdrant中
        await self._metric_qdrant_repository.save_metric_vectors(ids, payloads, vectors)
