"""Qdrant客户端管理模块"""

from qdrant_client import AsyncQdrantClient

from data_agent.core.configs.app_config import QdrantConfig, app_config


class QdrantClientManager:
    """Qdrant向量数据库异步客户端管理器：封装客户端的初始化、关闭逻辑"""

    def __init__(self, qdrant_config: QdrantConfig):
        self._qdrant_config = qdrant_config
        self._client: AsyncQdrantClient | None = None

    def init_qdrant(self):
        """初始化qdrant"""
        if self._client is None:
            self._client = AsyncQdrantClient(
                url=f"http://{self._qdrant_config.host}:{self._qdrant_config.port}"
            )

    async def close(self):
        if self._client is None:
            raise RuntimeError("请先init_qdrant方法初始化qdrant")
        await self._client.close()
        self._client = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            raise RuntimeError("请先调用init_qdrant方法初始化qdrant")
        return self._client


_qdrant_client_manager: QdrantClientManager | None = None


def get_qdrant_client_manager() -> QdrantClientManager:
    global _qdrant_client_manager
    if _qdrant_client_manager is None:
        _qdrant_client_manager = QdrantClientManager(app_config.qdrant)
    return _qdrant_client_manager
