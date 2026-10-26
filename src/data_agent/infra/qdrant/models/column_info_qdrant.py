from typing import Any, TypedDict


class ColumnInfoQdrant(TypedDict):
    """字段信息模型类(Qdrant)"""
    id:str
    name:str
    type:str
    role:str
    examples:list[Any]
    description:str
    alias:list[str]
    table_id:str