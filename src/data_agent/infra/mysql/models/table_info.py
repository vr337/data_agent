from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from data_agent.infra.mysql.models.base import Base


class TableInfoORM(Base):
    __tablename__ = "table_info"

    id: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True, comment="表编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="表名称"
    )
    role: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="表类型(fact/dim)"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="表描述"
    )
