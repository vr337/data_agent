"""构建知识库入口模块，主要是固定好流程和准备构建知识库所需的依赖"""

import asyncio
from argparse import ArgumentParser

from anyio import Path

from data_agent.core.logger import logger
from data_agent.infra.embedding.manager import (
    get_embedding_client_manger,
)
from data_agent.infra.es.manager import get_es_client_manager
from data_agent.infra.es.repositories.value_es_repository import ValueESRepository
from data_agent.infra.mysql.manager import get_dw_mysql_manager, get_meta_mysql_manager
from data_agent.infra.mysql.repositories.dw_repository import DwRepository
from data_agent.infra.mysql.repositories.meta_repository import MetaRepository
from data_agent.infra.qdrant.manager import get_qdrant_client_manager
from data_agent.infra.qdrant.repositories.column_qdrant_repository import (
    ColumnQdrantRepository,
)
from data_agent.infra.qdrant.repositories.metric_qdrant_repository import (
    MetricQdrantRepository,
)
from data_agent.services.meta_knowledge_service import MetaKnowledgeService


async def start_build(config_path: Path) -> None:
    """
    构建元数据知识库的入口函数，使用：uv run -m src.data_agent.scripts.build_meta_knowledge -c configs/meta_config.yaml
        步骤：
        1.初始化所有客户端管理器
        2.创建构建的业务对象，要准备
            创建依赖的所有持久对象，传入依赖的session或client
            用来生成向量的客户端
        3.调用业务对象的构建方法构建知识库
        4.如果成功了，事务提交
        5.如果失败了，事务回滚
        6.无论如何最终倒要关闭客户端管理器
    Args:
        config_path (Path): 元数据配置Path对象
    """

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
            meta_knowledge_service = MetaKnowledgeService(
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
            # 3.调用业务对象的构建方法构建知识库
            await meta_knowledge_service.build(config_path)
            # 4.成功了，提交事务(一般只有DML操作才设计到事务)
            await dw_session.commit()
            await meta_session.commit()
    except Exception as e:
        # 5.异常时回滚事务
        await dw_session.rollback()
        await meta_session.rollback()
        logger.error(f"构建知识库失败： {e!s}")
        raise  # 方便查看异常具体情况
    finally:
        # 6.无论如何最终倒要关闭客户端管理器
        await dw_mysql_manager.close()
        await meta_mysql_manager.close()
        await qdrant_client_manager.close()
        await es_client_manager.close()


if __name__ == "__main__":
    # 创建命令参数解析器
    argument_parser = ArgumentParser()
    # 添加一个可解析的命令参数
    argument_parser.add_argument(
        "-c",
        "--conf",  # 参考 git --version -v
        required=True,  # 参数是否是必须的
        help="yaml配置文件路径",  # 命令的帮助文档
    )
    # 解析命令传入的参数，得到包含参数的对象
    args = argument_parser.parse_args()
    print(f"--args={args}")
    # 得到配置文件的路径参数并包装为path对象
    config_path = Path(args.conf)
    # 异步启动构建
    asyncio.run(start_build(config_path))
