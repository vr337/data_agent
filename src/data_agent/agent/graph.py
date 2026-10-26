from langgraph.graph import StateGraph

from data_agent.agent.context import DataAgentContext
from data_agent.agent.nodes.add_extra_context import add_extra_context
from data_agent.agent.nodes.correct_sql import correct_sql
from data_agent.agent.nodes.execute_sql import execute_sql
from data_agent.agent.nodes.extract_keywords import extract_keywords
from data_agent.agent.nodes.filter_metric import filter_metric
from data_agent.agent.nodes.filter_table import filter_table
from data_agent.agent.nodes.generate_sql import generate_sql
from data_agent.agent.nodes.merge_retrieved_info import merge_retrieved_info
from data_agent.agent.nodes.recall_column import recall_column
from data_agent.agent.nodes.recall_metric import recall_metric
from data_agent.agent.nodes.recall_value import recall_value
from data_agent.agent.nodes.validate_sql import validate_sql
from data_agent.agent.state import DataAgentState

# 1.创建状态图
state_graph = StateGraph(state_schema=DataAgentState, context_schema=DataAgentContext)
# 2.添加节点
state_graph.add_node("extract_keywords", extract_keywords)
state_graph.add_node("recall_column", recall_column)
state_graph.add_node("recall_metric", recall_metric)
state_graph.add_node("recall_value", recall_value)
state_graph.add_node("merge_retrieved_info", merge_retrieved_info)
state_graph.add_node("filter_metric", filter_metric)
state_graph.add_node("filter_table", filter_table)
state_graph.add_node("add_extra_context", add_extra_context)
state_graph.add_node("generate_sql", generate_sql)
state_graph.add_node("validate_sql", validate_sql)
state_graph.add_node("correct_sql", correct_sql)
state_graph.add_node("execute_sql", execute_sql)
# 3.添加边
# 关键字提取
state_graph.set_entry_point("extract_keywords")

# 多路召回
state_graph.add_edge("extract_keywords", "recall_column")
state_graph.add_edge("extract_keywords", "recall_metric")
state_graph.add_edge("extract_keywords", "recall_value")

# 召回合并
state_graph.add_edge("recall_column", "merge_retrieved_info")
state_graph.add_edge("recall_metric", "merge_retrieved_info")
state_graph.add_edge("recall_value", "merge_retrieved_info")

# 过滤信息
state_graph.add_edge("merge_retrieved_info", "filter_metric")
state_graph.add_edge("merge_retrieved_info", "filter_table")

# 添加额外的上下文
state_graph.add_edge("filter_metric", "add_extra_context")
state_graph.add_edge("filter_table", "add_extra_context")

# 生成sql
state_graph.add_edge("add_extra_context", "generate_sql")

# 校验sql
state_graph.add_edge("generate_sql", "validate_sql")

# 添加条件边,根据是否有error信息来判断生成的sql是否校验成功
state_graph.add_conditional_edges(
    "validate_sql",
    lambda state: "correct_sql" if state.get("error") is not None else "execute_sql",
    {"execute_sql": "execute_sql", "correct_sql": "correct_sql"},
)

state_graph.add_edge("correct_sql", "validate_sql")

state_graph.set_finish_point("execute_sql")
# 4.编译
data_agent_app = state_graph.compile()
