import json
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.llm import get_llm_client
from data_agent.agent.prompts.prompt_loader import load_prompt
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger


async def filter_metric(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    过滤指标信息

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """

    try:
        # 1.调用llm，决策要保留指标信息，返回结构：["指标1","指标2","指标3"]，这是要保留的指标信息
        # 获取提示模板文本
        prompt_text = load_prompt("filter_metric_info")
        # 准备提示词模板需要的数据
        input_data = {
            "query": state.get("query"),
            "metric_infos": json.dumps(state.get("metric_infos"), ensure_ascii=False),
        }
        # 创建提示词模板
        prompt_template = PromptTemplate.from_template(
            template=prompt_text, template_format="jinja2"
        )
        # 调用llm
        chain = prompt_template | get_llm_client() | JsonOutputParser()
        result: list[Any] = await chain.ainvoke(input_data)

        # 2.过滤掉不保留的
        metric_infos = state.get("metric_infos")
        for i in range(len(metric_infos) - 1, -1, -1):
            # 判断表信息需不需要保留
            if metric_infos[i].get("name") not in result:
                # 不在里面，不需要这个表信息
                del metric_infos[i]

        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage":"过滤指标信息"})
        logger.info(f"过滤指标完成：{metric_infos}")
        return {"metric_infos":metric_infos}
    except Exception:
        logger.error("过滤指标信息失败")
        raise
