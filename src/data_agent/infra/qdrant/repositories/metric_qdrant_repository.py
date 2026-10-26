from qdrant_client import AsyncQdrantClient, models

from data_agent.infra.qdrant.models.metric_info_qdrant import MetricInfoQdrant


class MetricQdrantRepository:
    """操作Qdrant向量索引库的持久层类  专门处理指标信息数据"""

    collection_name: str = "data_agent_metric_collection"

    def __init__(self, client: AsyncQdrantClient):
        self._client = client

    async def _create_collection(self) -> None:
        """在Qdrant向量数据库中创建集合"""
        # TODO 待从测试的方式改为生产的方式
        # 创建集合，如果集合已经存在，先删除集合再创建，只适合测试阶段
        if await self._client.collection_exists(collection_name=self.collection_name):
            await self._client.delete_collection(collection_name=self.collection_name)
        await self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=1024, distance=models.Distance.COSINE
            ),
        )

    async def save_metric_vectors(
        self,
        ids: list[str],
        payloads: list[MetricInfoQdrant],
        vectors: list[list[float]],
    ) -> None:
        """
        保存指标信息到Qdrant向量数据中，三个列表元素关系都是一一对应的，长度也一样
        Args:
            ids (list[str]): 存储到向量数据中数据的id列表
            payloads (list[ColumnInfoQdrant]): 存储的载荷(标量)列表
            vectors (list[list[float]]): 用来检索的向量列表

        Args:
            ids (list[str]): _description_
            payloads (list[MetricInfoQdrant]): _description_
            vectors (list[list[float]]): _description_
        """

        # 1.创建集合
        await self._create_collection()
        # 2.保存
        # 分批，批量保存,防止内存oom和提高保存速度
        batch_size = 20
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_payloads = payloads[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]

            # 插入向量
            await self._client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[i],  # 表示id
                        payload=batch_payloads[i],
                        # 生成1024维随机向量
                        vector=batch_vectors[i],
                    )
                    for i in range(len(batch_ids))
                ],
            )
    async def search(self, keyword_vector: list[float]) -> list[MetricInfoQdrant]:
            """
            指标信息检索
    
            Args:
                keyword_vector (list[float]): 要检索关键字向量
    
            Returns:
                list[ColumnInfoQdrant]: 检索出来的指标信息
            """
    
            result = await self._client.query_points(
                collection_name=self.collection_name,
                query=keyword_vector,
                score_threshold=0,
            )
            return [MetricInfoQdrant(**point.payload) for point in result.points]
