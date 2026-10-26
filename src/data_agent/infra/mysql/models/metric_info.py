from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from data_agent.infra.mysql.models.base import Base


class MetricInfoORM(Base):
    __tablename__ = "metric_info"

    id: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True, comment="指标编码"
    )
    name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="指标名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="指标描述"
    )
    relevant_columns: Mapped[list[Any] | None] = mapped_column(
        JSON, nullable=True, comment="关联的列"
    )
    alias: Mapped[list[Any] | None] = mapped_column(
        JSON, nullable=True, comment="指标别名"
    )
