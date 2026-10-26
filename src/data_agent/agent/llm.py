import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from data_agent.core.configs.app_config import app_config

# 加载env配置
load_dotenv(override=True)
_llm = init_chat_model(
    model=os.getenv("LLM_MODEL") or app_config.llm.model_name,
    model_provider=os.getenv("LLM_PROVIDER") or app_config.llm.model_provider,
    base_url=os.getenv("LLM_BASE_URL") or app_config.llm.base_url,
    api_key=os.getenv("LLM_API_KEY") or app_config.llm.api_key,
)


def get_llm_client():
    return _llm
