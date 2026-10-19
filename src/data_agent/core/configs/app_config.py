from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf


@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation:str
    retention: str


@dataclass
class Console:
    enable: bool
    level: str


@dataclass
class LoggingConfig:
    file: File
    console: Console


@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str


@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str


@dataclass
class LLMConfig:
    model_name: str
    api_key: str


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig



# 将app_config.yml配置数据加载成AppConfig对象

# app_yml配置
_app_yml_path=Path(__file__).parents[4] / "configs" / "app_config.yml"

# 加载成对象
app_config:AppConfig=OmegaConf.to_object(
    OmegaConf.merge(AppConfig,
    OmegaConf.load(_app_yml_path) 
    )
)