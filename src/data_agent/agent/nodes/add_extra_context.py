from datetime import datetime

from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.state import DataAgentState, DataInfoState, DBInfoState
from data_agent.core.logger import logger


async def add_extra_context(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    增加额外的上下文，日期信息和数据库版本信息

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """
    try:
        dw_repository = runtime.context.get("dw_repository")
        # 1.收集当前时间日期
        today = datetime.today()
        date_info = DataInfoState(
            data=today.strftime("%Y-%m-%d"),
            weekday=today.strftime("%A"),
            quarter=(f"Q{(today.month + 2) // 3}"),  # Q1:1、2、3;Q2:4、5、6...
        )
        # 2.收集数据库信息
        db_info = await dw_repository.get_db_info()
        db_info = DBInfoState(**db_info)
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage":"添加额外上下文信息"})
        # 返回状态更新
        return {"date_info": date_info, "db_info": db_info}
    except Exception:
        logger.error("添加额外上下文信息失败")
        raise
