from jieba.analyse import extract_tags
from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger


async def extract_keywords(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    关键词提取节点
    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态的更新
    """
    try:
        # 提取用户问题
        query = state.get("query")
        # 定义返回指定词性的元组(只能匹配这些词性的词，不在这个范围内，跳过不计分)
        allow_pos = (
            "n",  # 名词: 数据、服务器、表格
            "nr",  # 人名: 张三、李四
            "ns",  # 地名: 北京、上海
            "nt",  # 机构团体名: 政府、学校、某公司
            "nz",  # 其他专有名词: Unicode、哈希算法、诺贝尔奖
            "v",  # 动词: 运行、开发
            "vn",  # 名动词: 工作、研究
            "a",  # 形容词: 美丽、快速
            "an",  # 名形词: 难度、合法性、复杂度
            "eng",  # 英文
            "i",  # 成语
            "l",  # 常用固定短语
        )
        # 使用jieba库进行字面提取
        keywords: list[str] = extract_tags(query, topK=5, allowPOS=allow_pos)
        logger.info(f"jieba提取的关键字为：{keywords}")
        # 与用户问题合并去重
        keywords = list(set(keywords + [query]))
        logger.info(f"去重后的关键子：{keywords}")
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage": "关键字提取"})
        return {"keywords": keywords}
    except Exception:
        logger.error("关键字提取失败")
        raise
