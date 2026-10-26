from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.llm import get_llm_client
from data_agent.agent.prompts.prompt_loader import load_prompt
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger
from data_agent.infra.qdrant.models.metric_info_qdrant import MetricInfoQdrant


async def semantic_extraction(state: DataAgentState) -> list[str]:
    """
    1.将用户提问交给大模型来提取语义化的关键字列表，并且与原来的关键字进行合并：keywords
    Args:
        state (DataAgentState): 全局的状态

    Returns:
        list[str]: 语义提取去重合并后的keywords
    """
    # 1.加载提示词模板所需的模板文本
    prompt_text = load_prompt("extend_keywords_for_metric_recall")
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


async def recall_metric(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    指标信息召回
    1.将用户提问交给大模型来提取语义化的关键字列表，并且与原来的关键字进行合并：keywords
    2.将提取的keywords进行多文本嵌入(批量向量化)->keyword_vectors
    3.遍历每个keyword_vector，去qdrant中搜索得到区配的字段信息列表：list[MetricInfoQdrant]
    4.对所得到字段信息列表做去重合并->recall_metrics:list[MetricInfoQdrant]
    5.状态更新recall_metrics

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """
    try:
        # 1.将用户提问交给大模型来提取语义化的关键字列表，并且与原来的关键字进行合并：keywords
        keywords = await semantic_extraction(state)
        # 2.将提取的keywords进行多文本嵌入(批量向量化)->keyword_vectors
        keyword_vectors = await runtime.context.get(
            "embedding_client"
        ).aembed_documents(keywords)
        # 3.遍历每个keyword_vector，去qdrant中搜索得到区配的指标信息列表：list[metricInfoQdrant]
        recall_metrics_dict: dict[str, MetricInfoQdrant] = {}
        for keyword_vector in keyword_vectors:
            recall_infos = await runtime.context.get("metric_qdrant_repository").search(
                keyword_vector
            )
            # 去重，相同metric_id，为相同的字段信息
            for recall_info in recall_infos:
                # metric_id相同，即为相同的字段信息，相同的会覆盖之前，从而达到去重效果
                recall_metrics_dict[recall_info.get("id")] = recall_info
        # 4.对所得到字段信息列表做去重合并->recall_metrics:list[ColumInfoQdrant]
        # 合并
        recall_metrics = list(recall_metrics_dict.values())
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage": "指标信息召回"})
        logger.info(f"指标信息召回完成：{recall_metrics}")
        # 5.状态更新recall_metrics
        return {"recall_metrics": recall_metrics}
    except Exception:
        logger.error("指标信息召回失败")
        raise
