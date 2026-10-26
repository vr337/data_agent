from typing import Any

from elasticsearch import AsyncElasticsearch

from data_agent.infra.es.models.value_info_es import ValueInfoES


class ValueESRepository:
    """操作ES全文索引库的持久层类  专门处理字段值数据"""

    index_name: str = "data_agent_value_index"
    mappings: dict[str, Any] = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword", "index": False},
            "value": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word",
            },
            "type": {"type": "keyword", "index": False},
            "column_id": {"type": "keyword", "index": False},
            "column_name": {"type": "keyword", "index": False},
            "table_id": {"type": "keyword", "index": False},
            "table_name": {"type": "keyword", "index": False},
        },
    }

    def __init__(self, client: AsyncElasticsearch):
        self._client = client

    async def _create_index(self) -> None:
        """创建索引"""
        # TODO 待从测试改为真正生产要用的方式
        # 每次创建前删除之前的索引，这种方式仅限测试
        if await self._client.indices.exists(index=self.index_name):
            await self._client.indices.delete(index=self.index_name)
        await self._client.indices.create(index=self.index_name, mappings=self.mappings)

    async def save_value_infos(self, column_value_infos: list[ValueInfoES]) -> None:
        """
        保存字段值信息到es中(建立全文索引)

        Args:
            column_value_infos (_type_): 字段值信息
        """
        # 1.创建索引
        await self._create_index()
        # 构建operations
        operations: list[Any] = []
        for column_value_info in column_value_infos:
            # 两两一组的插入
            operations.append({"index": {"_index": self.index_name}})
            operations.append(column_value_info)
        # 2.分批，批量插入，防止内存oom
        # 每批10个
        batch_size = 10
        for i in range(0, len(operations), batch_size):
            batch_operations = operations[i : i + batch_size]
            await self._client.bulk(operations=batch_operations)

    async def search(self, keyword: str) -> list[ValueInfoES]:
        """在es中通过关键字进行全文检索

        Args:
            keyword (str): 检索的关键字

        Returns:
            list[ValueInfoES]: 检索后的字段值信息列表
        """

        result = await self._client.search(
            index=self.index_name,
            query={
                # 搜索条件
                "match": {"value": keyword}
            },
        )
        return [ValueInfoES(**item["_source"]) for item in result["hits"]["hits"]]
