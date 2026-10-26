from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.llm import get_llm_client
from data_agent.agent.prompts.prompt_loader import load_prompt
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger
from data_agent.infra.es.models.value_info_es import ValueInfoES


async def semantic_extraction(state: DataAgentState) -> list[str]:
    """
    1.将用户提问交给大模型来提取语义化的关键字列表，并且与原来的关键字进行合并：keywords
    Args:
        state (DataAgentState): 全局的状态

    Returns:
        list[str]: 语义提取去重合并后的keywords
    """
    # 1.加载提示词模板所需的模板文本
    prompt_text = load_prompt("extend_keywords_for_value_recall")
    # 2.组装提示词模板所需的数据
    input_data = {"query": state.get("query") or ""}
    # 3.构建提示词模板
    prompt_template = PromptTemplate.from_template(
        template=prompt_text, template_format="jinja2"
    )
    # 4.调用llm
    chain = prompt_template | get_llm_client() | JsonOutputParser()
    keywords = (await chain.ainvoke(input_data)) or []

    # 5.去重
    return list(set(keywords + state.get("keywords")))


async def recall_value(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    1.对query进行大模型语义化的分词，并与jiaba分词后的keywords去重合并->keywords
    2.对每个分词器ES全文搜索，模糊匹配除字段值信息里列表->list[ValueInfoES]
    3.对所得到的所有字段值信息列表进行去重合并->recall_values:list[ValueInfoES]
    4.状态更新recall_values

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """
    try:
        # 1.对query进行大模型语义化的分词，并与jiaba分词后的keywords去重合并->keywords
        keywords = await semantic_extraction(state)
        # 2.对每个分词器ES全文搜索，模糊匹配除字段值信息里列表->list[ValueInfoES]
        value_infos_dict: dict[str, ValueInfoES] = {}
        for keyword in keywords:
            value_infos = await runtime.context.get("value_es_repository").search(
                keyword
            )
            # 3.对所得到的所有字段值信息列表进行去重合并->recall_values:list[ValueInfoES]
            # 去重
            for value_info in value_infos:
                # 字段值id相同，表示是同一个字段值，相同的key，后续会替换前面添加的
                value_infos_dict[value_info.get("id")] = value_info
        # 合并
        recall_values: list[ValueInfoES] = list(value_infos_dict.values())
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage":"字段值召回"})
        logger.info(f"字段值信息召回完成：{recall_values}")
        # 4.状态更新recall_values
        return {"recall_values": recall_values}
    except Exception:
        logger.error("字段值召回失败")
        raise
