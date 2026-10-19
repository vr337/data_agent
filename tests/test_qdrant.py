import asyncio
import random
import uuid

from qdrant_client import models

from data_agent.infra.qdrant.manager import get_qdrant_client_manager

if __name__ == "__main__":
    # 创建向量数据库客户端管理器
    qdrant_client_manager = get_qdrant_client_manager()

    async def test():
        collection_name = "test_collection"
        # 初始化客户端对象
        qdrant_client_manager.init_qdrant()
        client = qdrant_client_manager.client

        # 创建集合，如果集合已经存在，先删除集合再创建，只适合测试阶段
        if await client.collection_exists(collection_name=collection_name):
            await client.delete_collection(collection_name=collection_name)
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1024, distance=models.Distance.COSINE
            ),
        )

        # 插入向量
        await client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=uuid.uuid4(),  # 表示id
                    payload={
                        "color": "red" if i % 2 == 0 else "blue",
                    },
                    # 生成1024维随机向量
                    vector=[random.random() for _ in range(1024)],
                )
                for i in range(100)  # 创建100向量
            ],
        )
        # 搜索向量：查找最相似的10个向量
        result = await client.query_points(
            collection_name=collection_name,
            query=[
                random.random() for _ in range(1024)
            ],  # 生成一个1024维随机向量 用于查询，
            limit=5,  # 返回最相似的5个向量
            query_filter=models.Filter(
                must=models.FieldCondition(
                    key="color", match=models.MatchValue(value="red")
                )
            ),  # 值的条件过滤
            score_threshold=0.65,  # 向量相似度阈值，低于该阈值的向量将被忽略
        )
        print(result.points, len(result.points))

        [print(f"reload={point.payload}") for point in result.points]

        # 释放资源
        await qdrant_client_manager.close()

    asyncio.run(test())
