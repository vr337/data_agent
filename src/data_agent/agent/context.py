from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from data_agent.infra.mysql.repositories.dw_repository import DwRepository
from data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)


class DataAgentContext(TypedDict):
    """智能体运行时的上下文信息，一般不可变"""
    dw_repository: DwRepository # 数据仓储类
    meta_repository: MetaRepository # 元数据仓储类
    column_qdrant_repository: ColumnQdrantRepository # 字段向量仓储类
    metric_qdrant_repository: MetricQdrantRepository # 指标向量仓储类 
    value_es_repository: ValueESRepository # 字段值全文检索仓储类
    embedding_client: HuggingFaceEndpointEmbeddings # 向量服务客户端