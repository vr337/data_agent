import asyncio

from data_agent.infra.es.manager import get_es_client_manager

if __name__ == "__main__":

    async def test():
        es_client_manager = get_es_client_manager()
        es_client_manager.init_client()
        client = es_client_manager.client
        index_name = "my_index"

        # 创建索引,这种方式仅限测试
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        result = await client.indices.create(
            index=index_name,
            mappings={
                "dynamic": False,
                "properties": {
                    "name": {"type": "text"},
                    "author": {"type": "text"},
                    "release_date": {"type": "date", "format": "yyyy-MM-dd"},
                    "page_count": {"type": "integer"},
                },
            },
        )
        # 插入数据
        result = await client.bulk(
            operations=[
                {"index": {"_index": index_name}},
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585,
                },
                {"index": {"_index": index_name}},
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328,
                },
                {"index": {"_index": index_name}},
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227,
                },
                {"index": {"_index": index_name}},
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268,
                },
                {"index": {"_index": index_name}},
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311,
                },
            ],
        )
        print(result)
        # 刷新保存索引数据，要不然就要等两秒
        await client.indices.refresh(index=index_name)

        # 全文搜索
        result = await client.search(
            index=index_name,
            query={
                # 搜索条件
                "match": {"name": "Brave"}
            },
        )
        print(result)
        print(result["hits"]["hits"])

        # 关闭#ES客户端
        await es_client_manager.close()

    asyncio.run(test())
