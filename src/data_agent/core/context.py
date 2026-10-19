"""管理协程上下文的模块，用来为日志模块服务，来区分不同协程的请求的日志"""

from contextvars import ContextVar, Token

# 1.创建上下文变量，用来代理当前协程的上下文对象,这里的"request_id"单纯时上下文变量的名称，起到标识作用，而default仅仅是创建时或重置时的默认值
_req_context_var = ContextVar("request_id", default="")


def get_request_id() -> str:
    """
    获取当前当前协程上下文对象里存储的request_id

    Returns:
        str: request_id(请求id)
    """
    return _req_context_var.get()


def set_request_id(request_id: str) -> Token:
    """
    给当前当前协程上下文对象设置request_id
    Args:
        request_id (str): request_id(请求id)

    Returns:
        Token: 令牌
    """
    return _req_context_var.set(request_id)


def reset_request_id(token: Token) -> None:
    """
    将当前协程上下文对象重置为默认值
    Args:
        token (Token): 令牌
    """
    _req_context_var.reset(token)
