from typing import Annotated

from fastapi import Depends
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from data_agent.infra.embedding.manager import get_embedding_client_manger
from data_agent.infra.es.manager import get_es_client_manager
from data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from data_agent.infra.mysql.manager import get_dw_mysql_manager, get_meta_mysql_manager
from data_agent.infra.mysql.repositories.dw_repository import DwRepository
from data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from data_agent.infra.qdrant.manager import get_qdrant_client_manager
from data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)
from data_agent.services.query_service import QueryService


async def get_dw_session():
    async with get_dw_mysql_manager().session_factory() as session:
        yield session

async def get_meta_session():
    async with get_meta_mysql_manager().session_factory() as session:
        yield session


def get_dw_repository(
    dw_session: Annotated[AsyncSession, Depends(get_dw_session)],
) -> DwRepository:
    return DwRepository(dw_session)
def get_meta_repository(
    meta_session: Annotated[AsyncSession, Depends(get_meta_session)],
) -> MetaRepository:
    return MetaRepository(meta_session)



def get_column_qdrant_repository() -> ColumnQdrantRepository:
    return ColumnQdrantRepository(get_qdrant_client_manager().client)


def get_metric_qdrant_repository() -> MetricQdrantRepository:
    return MetricQdrantRepository(get_qdrant_client_manager().client)


def get_value_es_repository() -> ValueESRepository:
    return ValueESRepository(get_es_client_manager().client)


def get_embedding_client() -> HuggingFaceEndpointEmbeddings:
    return get_embedding_client_manger().client


def get_query_service(
    dw_repository: Annotated[DwRepository, Depends(get_dw_repository)],
    meta_repository: Annotated[MetaRepository, Depends(get_meta_repository)],
    column_qdrant_repository: Annotated[
        ColumnQdrantRepository, Depends(get_column_qdrant_repository)
    ],
    metric_qdrant_repository: Annotated[
        MetricQdrantRepository, Depends(get_metric_qdrant_repository)
    ],
    value_es_repository: Annotated[ValueESRepository, Depends(get_value_es_repository)],
    embedding_client: Annotated[
        HuggingFaceEndpointEmbeddings, Depends(get_embedding_client)
    ],
) -> QueryService:
    return QueryService(
        dw_repository=dw_repository,
        meta_repository=meta_repository,
        column_qdrant_repository=column_qdrant_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        value_es_repository=value_es_repository,
        embedding_client=embedding_client,
    )
