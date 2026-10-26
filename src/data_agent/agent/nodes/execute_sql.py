from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.state import DataAgentState
from data_agent.core.logger import logger


async def execute_sql(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> None:
    """执行SQl

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象
    """
    try:
        result = await runtime.context.get("dw_repository").execute_sql(
            state.get("sql")
        )
        logger.info(f"执行SQL成功 result={result}")
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"result": result})
    except Exception as e:
        logger.error(f"执行SQL失败,{e!s}")
        raise


