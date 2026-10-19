from contextlib import asynccontextmanager

from fastapi import FastAPI

from data_agent.infra.embedding.manager import get_embedding_client_manger
from data_agent.infra.mysql.manager import get_dw_mysql_manager, get_meta_mysql_manager
from data_agent.infra.qdrant.manager import get_qdrant_client_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # fast api启动时执行
    # 初始化数据库
    get_dw_mysql_manager().init_db()
    get_meta_mysql_manager().init_db()
    # 初始化Qdrant向量数据库的客户端
    get_qdrant_client_manager().init_qdrant()
    # 初始化嵌入模型
    get_embedding_client_manger().init_client()
    yield
    # fast api 销毁时执行
    await get_dw_mysql_manager().close()
    await get_meta_mysql_manager().close()
    await get_qdrant_client_manager().close()


app = FastAPI(lifespan=lifespan)
