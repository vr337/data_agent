from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from data_agent.infra.mysql.models.base import Base


class ColumnInfoORM(Base):
    __tablename__ = "column_info"

    id: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True, comment="列编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="列名称"
    )
    type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="数据名称"
    )
    role: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="列类型(primary_key,foreign_key,measure,dimension)",
    )
    examples: Mapped[list[Any] | None] = mapped_column(
        JSON, nullable=True, comment="数据示例"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="列描述"
    )
    alias: Mapped[list[Any] | None] = mapped_column(
        JSON, nullable=True, comment="列别名"
    )
    table_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="所属表编号"
    )
