from typing import TypedDict


class MetricInfoQdrant(TypedDict):
    """指标信息模型类(Qdrant)"""
    id:str
    name:str
    description:str
    relevant_columns:list[str]
    alias:list[str]