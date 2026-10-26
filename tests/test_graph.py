
import asyncio

from httpx2 import query

from src.data_agent.agent.context import DataAgentContext
from src.data_agent.agent.graph import data_agent_app
from src.data_agent.agent.state import DataAgentState, create_default_state
from src.data_agent.infra.embedding.manager import get_embedding_client_manger
from src.data_agent.infra.es.manager import get_es_client_manager
from src.data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from src.data_agent.infra.mysql.manager import (
    get_dw_mysql_manager,
    get_meta_mysql_manager,
)
from src.data_agent.infra.mysql.repositories.dw_repository import DwRepository
from src.data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from src.data_agent.infra.qdrant.manager import get_qdrant_client_manager
from src.data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from src.data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)


async def test1():

    # 1.初始化所有客户端管理器
    # 初始化数据库客户端
    dw_mysql_manager = get_dw_mysql_manager()
    meta_mysql_manager = get_meta_mysql_manager()
    dw_mysql_manager.init_db()
    meta_mysql_manager.init_db()

    # 初始化向量数据库Qdrant客户端
    qdrant_client_manager = get_qdrant_client_manager()
    qdrant_client_manager.init_qdrant()

    # 初始化全文索引库ES的客户端
    es_client_manager = get_es_client_manager()
    es_client_manager.init_client()

    # 初始化向量模型客户端
    embedding_client_manager = get_embedding_client_manger()
    embedding_client_manager.init_client()
    # 2.创建构建的业务对象

    try:
        async with (
            dw_mysql_manager.session_factory() as dw_session,
            meta_mysql_manager.session_factory() as meta_session,
        ):
            data_agent_state = create_default_state(query="各个地区iPhone 15 Pro去年卖了多少钱")
            data_agent_context = DataAgentContext(
                dw_repository=DwRepository(dw_session),
                meta_repository=MetaRepository(meta_session),
                column_qdrant_repository=ColumnQdrantRepository(
                    qdrant_client_manager.client
                ),
                metric_qdrant_repository=MetricQdrantRepository(
                    qdrant_client_manager.client
                ),
                value_es_repository=ValueESRepository(es_client_manager.client),
                embedding_client=embedding_client_manager.client,
            )
            async for chunk in data_agent_app.astream(
                input=data_agent_state,
                context=data_agent_context,
                stream_mode="custom",  # 自定义模式，答应输出每个节点stream_writer输出的内容
            ):
                print(f"---{chunk}---")
    except Exception:
        raise  # 方便查看异常具体情况
    finally:
        # 6.无论如何最终倒要关闭客户端管理器
        await dw_mysql_manager.close()
        await meta_mysql_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()
def test2():
    # data_agent_app.get_graph().print_ascii()
    print(data_agent_app.get_graph().draw_mermaid())
if __name__ == "__main__":
    asyncio.run(test1())
    # test2()
