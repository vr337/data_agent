import uuid

import uvicorn
from fastapi import FastAPI, Request

from data_agent.api.routers.query import query_router
from data_agent.core.context import set_request_id
from data_agent.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

# 路由器挂载
app.include_router(query_router, prefix="/api")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    全局中间件，拦截所有的http请求

    Args:
        request (Request): 请求参数
        call_next (_type_): 下一个路由/路由函数
    """
    # 请求
    # 1.给上下文设置request_id
    set_request_id(uuid.uuid4().hex)
    # 2.调用下一个中间件或路由函数
    response = await call_next(request)
    # 3.响应
    return response


app.middleware(add_request_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
