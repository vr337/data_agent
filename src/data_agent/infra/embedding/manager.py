from langchain_huggingface import HuggingFaceEndpointEmbeddings

from data_agent.core.configs.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    """
    嵌入式向量嵌入客户端管理器类
    用于管理 HuggingFaceEndpointEmbeddings 客户端的初始化和配置
    """
    def __init__(self, config: EmbeddingConfig):
        self._config = config
        self._client: HuggingFaceEndpointEmbeddings | None = None

    def init_client(self) -> None:
        if self._client is None:
            model = f"http://{self._config.host}:{self._config.port}"
            self._client = HuggingFaceEndpointEmbeddings(model=model)
    @property
    def client(self)->HuggingFaceEndpointEmbeddings:
        if self._client is None:
            raise RuntimeError("请先调用init方法初始化")
        return self._client


_embedding_client_manager: EmbeddingClientManager | None = None


def get_embedding_client_manger() -> EmbeddingClientManager:
    global _embedding_client_manager
    if _embedding_client_manager is None:
        _embedding_client_manager = EmbeddingClientManager(app_config.embedding)
    return _embedding_client_manager
