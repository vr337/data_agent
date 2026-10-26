import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from data_agent.agent.context import DataAgentContext
from data_agent.agent.graph import data_agent_app
from data_agent.agent.state import create_default_state
from data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from data_agent.infra.mysql.repositories.dw_repository import DwRepository
from data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)


class QueryService:
    def __init__(
        self,
        dw_repository: DwRepository,
        meta_repository: MetaRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        value_es_repository=ValueESRepository,
        embedding_client=HuggingFaceEndpointEmbeddings,
    ):
        self._dw_repository = dw_repository
        self._meta_repository = meta_repository
        self._column_qdrant_repository = column_qdrant_repository
        self._metric_qdrant_repository = metric_qdrant_repository
        self._value_es_repository = value_es_repository
        self._embedding_client = embedding_client

    async def search(self, query: str):
        try:
            # 1.定义state
            data_agent_state = create_default_state(query=query)
            # 2.定义context
            data_agent_context = DataAgentContext(
                dw_repository=self._dw_repository,
                meta_repository=self._meta_repository,
                column_qdrant_repository=self._column_qdrant_repository,
                metric_qdrant_repository=self._metric_qdrant_repository,
                value_es_repository=self._value_es_repository,
                embedding_client=self._embedding_client,
            )
            # 调用图返回
            async for chunk in data_agent_app.astream(
                input=data_agent_state,
                context=data_agent_context,
                stream_mode="custom",  # 自定义模式，输出的是每个节点stream_writer输出的内容
            ):
                # 以sse的格式返回给前端
                yield f"data:{json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:  # noqa: BLE001
            # 将错误信息也返回给用户
            yield f"data:{json.dumps({'error': str(e)}, ensure_ascii=False, default=str)}\n\n"
