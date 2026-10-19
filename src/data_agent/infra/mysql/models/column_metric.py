from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from data_agent.infra.mysql.models.base import Base


class ColumnMetricORM(Base):
    __tablename__ = "column_metric"

    column_id: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True, comment="列编号"
    )
    metric_id: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True, comment="指标编号"
    )
