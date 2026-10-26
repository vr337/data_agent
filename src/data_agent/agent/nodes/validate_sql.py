from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger

MAX_FAIL_COUNT = 5  # 最大失败次数


async def validate_sql(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    校验sql

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """
    # 每次校验前看一下失败次数是否超过最大失败次数，超过了就报错结束整个流程
    if state.get("fail_count") > MAX_FAIL_COUNT:
        raise RuntimeError("无法矫正成功，矫正失败")
    try:
        # 校验sql，失败时会抛出异常
        await runtime.context.get("dw_repository").validate_sql(state.get("sql"))
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage":"校验SQL"})
        return {"error": None}
    except Exception as e:
        logger.error(f"校验SQL失败,{e!s}")
        # 校验失败
        return {
            "error": f"校验sql失败:{e!s}",
            "fail_count": state.get("fail_count") + 1,
        }
