import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.llm import get_llm_client
from data_agent.agent.prompts.prompt_loader import load_prompt
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger


async def correct_sql(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    矫正SQL

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """
    try:
        # 通过llm来矫正sql
        # 获取提示模板文本
        prompt_text = load_prompt("correct_sql")
        # 准备提示词模板需要的数据
        input_data = {
            "query": state.get("query"),
            "table_infos": json.dumps(state.get("table_infos"), ensure_ascii=False),
            "metric_infos": json.dumps(state.get("metric_infos"), ensure_ascii=False),
            "date_info": json.dumps(state.get("date_info"), ensure_ascii=False),
            "db_info": json.dumps(state.get("db_info"), ensure_ascii=False),
            "sql": state.get("sql"),
            "error": state.get("error"),
        }
        # 创建提示词模板
        prompt_template = PromptTemplate.from_template(
            template=prompt_text, template_format="jinja2"
        )
        # 调用llm
        chain = prompt_template | get_llm_client() | StrOutputParser()
        sql = await chain.ainvoke(input_data)
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage": "矫正SQL"})
        logger.info(f"矫正sql完成,{sql}")
        return {"sql": sql}
    except Exception:
        logger.error("矫正SQL失败")
        raise
