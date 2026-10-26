import json

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.llm import get_llm_client
from data_agent.agent.prompts.prompt_loader import load_prompt
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger


async def filter_table(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    过滤表信息

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态的更新
    """
    try:
        # 1.调用llm，决策要保留那些字段、那些表，返回结构：{表名1:[字段名1:字段名2],表名2:[字段名1,字段名2]}，这是要保留的表信息和对应的字段信息
        # 获取提示模板文本
        prompt_text = load_prompt("filter_table_info")
        # 准备提示词模板需要的数据
        input_data = {
            "query": state.get("query"),
            "table_infos": json.dumps(state.get("table_infos"), ensure_ascii=False),
        }
        # 创建提示词模板
        prompt_template = PromptTemplate.from_template(
            template=prompt_text, template_format="jinja2"
        )
        # 调用llm
        chain = prompt_template | get_llm_client() | JsonOutputParser()
        result: dict[str, list[str]] = await chain.ainvoke(input_data)

        # 2.过滤掉不保留的
        table_infos = state.get("table_infos")
        for i in range(len(table_infos) - 1, -1, -1):
            table_name = table_infos[i].get("name")
            # 判断表信息需不需要保留
            if table_name not in result:
                # 不在里面，不需要这个表信息
                del table_infos[i]
            else:
                # 需要表信息，过滤表对应的字段信息
                columns = table_infos[i].get("columns")
                for j in range(len(columns) - 1, -1, -1):
                    if columns[j].get("name") not in result.get(table_name):
                        # 不需要这个字段信息
                        del columns[j]

        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"state":"过滤表信息"})
        logger.info(f"过滤表完成：{table_infos}")
        return {"table_infos":table_infos}
    except Exception:
        logger.error("过滤表信息失败")
        raise
