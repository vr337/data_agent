"""加载meta_config.yml配置模块"""

from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf


@dataclass
class ColumnConfig:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool  # 是否需要再es中存储


@dataclass
class TableConfig:
    name: str
    role: str
    description: str
    columns: list[ColumnConfig]


@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


@dataclass
class MetaConfig:
    tables: list[TableConfig]
    metrics: list[MetricConfig]


# 加载元数据函数
def load_meta_config(config_path: Path) -> MetaConfig:

    # 1. 强制转为绝对路径，确保跨平台/跨目录无死角
    path = Path(config_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"找不到配置文件: {path}")

    # 2. 手动读取文本，绕过 OmegaConf.load 的文件类型校验 Bug
    with open(path, "r", encoding="utf-8") as f:
        yaml_content = f.read()

    # 3. 将文本解析为 OmegaConf 对象  2和3步骤等价于OmegaConf.load(path)
    raw_config = OmegaConf.create(yaml_content)

    # 4. 合并到你的强类型 dataclass 中 (保留你原本的逻辑)
    meta_config: MetaConfig = OmegaConf.to_object(
        OmegaConf.merge(OmegaConf.structured(MetaConfig), raw_config)
    )
    return meta_config
