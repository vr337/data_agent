from elasticsearch import AsyncElasticsearch

from data_agent.core.configs.app_config import ESConfig, app_config


class ESClientManager:
    """ES异步客户端管理器：封装ES客户端的初始化、连接、关闭逻辑"""

    def __init__(self, config: ESConfig):
        self._config = config
        self._client: AsyncElasticsearch | None = None

    def init_client(self) -> None:
        if self._client is None:
            urls = [f"http://{self._config.host}:{self._config.port}"]
            self._client = AsyncElasticsearch(hosts=urls)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> AsyncElasticsearch:
        if self._client is None:
            raise RuntimeError("请先调用init_client方法初始化es")
        return self._client


_es_client_manger: ESClientManager | None = None


def get_es_client_manager() -> ESClientManager:
    global _es_client_manger
    if _es_client_manger is None:
        _es_client_manger = ESClientManager(app_config.es)
    return _es_client_manger
