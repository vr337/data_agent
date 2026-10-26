import copy
from typing import Any, TypedDict

from langchain_huggingface import data

from data_agent.infra.es.models.value_info_es import ValueInfoES
from data_agent.infra.qdrant.models.column_info_qdrant import ColumnInfoQdrant
from data_agent.infra.qdrant.models.metric_info_qdrant import MetricInfoQdrant


# 私有状态
class ColumnInfoState(TypedDict):
    """列信息封装实体"""

    name: str
    type: str
    role: str
    examples: list[Any]
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    """表信息封装实体"""

    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    """指标信息封装实体"""

    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DataInfoState(TypedDict):
    """当前日期时间的封装实体"""

    data: str  # 年月日
    weekday: str  # 星期
    quarter: str  # 季度 Q1-Q4


class DBInfoState(TypedDict):
    """数据库信息的封装实体"""

    version: str  # 版本号
    dialect: str  # 数据库名称


# 全局状态
class DataAgentState(TypedDict):
    query: str  # 用户的查询
    keywords: list[str]  # 提取的关键字列表
    sql: str  # 要校验，要矫正，要执行的sql，作为中间变量
    error: str  # 异常信息
    recall_columns: list[ColumnInfoQdrant]  # 召回的字段信息
    recall_metrics: list[MetricInfoQdrant]  # 召回的指标信息
    recall_values: list[ValueInfoES]  # 召回的字段值信息
    table_infos: list[TableInfoState]  # 合并3路召回产生的相关表及其字段信息状态列表
    metric_infos: list[MetricInfoState]  # 指标信息状态对象列表
    date_info: DataInfoState  # 当前日期时间信息
    db_info: DBInfoState  # 数据信息
    fail_count: int  # 失败的次数


_graph_default_state: dict[str, Any] = {
    "query": "",
    "keywords": [],
    "sql": "",
    "error": None,
    "recall_columns": [],
    "recall_metrics": [],
    "recall_values": [],
    "table_infos": [],
    "metric_infos": [],
    "date_info": None,
    "db_info": None,
    "fail_count": 0,
}


def create_default_state(**overrides) -> DataAgentState:
    """
    创建默认状态，支持覆盖
    Args:
        **overrides: 要覆盖的字段（关键字参数解包）
    Returns:
        新的状态实例
    Examples:
        state = create_default_state(query="hello world", error="你错了")
    """

    # 默认状态
    state = copy.deepcopy(_graph_default_state)
    # 用 overrides 覆盖默认值
    state.update(overrides)
    # 返回创建好的状态字典实例
    return state
