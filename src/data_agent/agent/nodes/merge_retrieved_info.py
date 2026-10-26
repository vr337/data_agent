from langgraph.runtime import Runtime

from data_agent.agent.context import DataAgentContext
from data_agent.agent.state import (
    ColumnInfoState,
    DataAgentState,
    MetricInfoState,
    TableInfoState,
)
from data_agent.core.logger import logger
from data_agent.infra.mysql.models.column_info import ColumnInfoORM
from data_agent.infra.mysql.models.table_info import TableInfoORM
from data_agent.infra.qdrant.models.column_info_qdrant import ColumnInfoQdrant
from data_agent.infra.qdrant.models.metric_info_qdrant import MetricInfoQdrant


async def merge_retrieved_info(
    state: DataAgentState, runtime: Runtime[DataAgentContext]
) -> DataAgentState:
    """
    合并召回的信息
    1.收集一个最完整的字段信息列表，去重并合并->dict[column_id,ColumnInfoQdrant]
    1.1.收集召回的字段信息列表
    1.2.收集召回的指标信息列表关联的字段信息列表
    1.3.收集召回的字段值信息列表对应的字段信息列表->将字段值保存到字段的值的阳历列表中
    1.4.收集相关的主键和外键字段信息列表
    2.根据收集所有字段信息列表生成：带字段信息列表的表信息列表
    2.1.对收集的字段信息列表进行按表id进行分组:dict[table_id,list[ColumnInfoQdrant]]
    2.2.生成带字段信息列表的表信息列表->table_infos:list[TableInfoState]
        根据id查询meta数据库中的table_info表得到表信息
        根据当前字段信息列表,生成columnInfoState类型的字段状态信息列表

    Args:
        state (DataAgentState): 全局的状态
        runtime (Runtime[DataAgentContext]): Runtime对象

    Returns:
        DataAgentState: 状态更新
    """

    try:
        # 拿到三路召回的字段信息、指标信息、字段值信息
        recall_columns = state.get("recall_columns")
        recall_metrics = state.get("recall_metrics")
        recall_values = state.get("recall_values")

        # 拿到dw的持久层对象
        meta_repository = runtime.context.get("meta_repository")

        # 1.收集一个最完整的字段信息列表，去重并合并->dict[column_id,ColumnInfoQdrant]
        column_infos_dict: dict[str, ColumnInfoQdrant] = {}
        # 1.1.收集召回的字段信息列表
        # 字典当key重复时(也就时column_id重复时)，表示是相同的字段信息，后面的会覆盖前面的，从而实现去重
        column_infos_dict.update(
            {
                column_info_qdrant.get("id"): column_info_qdrant
                for column_info_qdrant in recall_columns
            }
        )
        metric_infos: list[MetricInfoState] = []
        # 1.2.收集召回的指标信息列表关联的字段信息列表,顺便整理一下metric_infos
        for metric_info_qdrant in recall_metrics:
            for column_id in metric_info_qdrant.get("relevant_columns"):
                # 只有不存在这个字段信息，才需要查询添加
                if column_id not in column_infos_dict:
                    metric_info_qdrant[column_id] = _covert_column_info_mysql_to_qdrant(
                        await meta_repository.get_column_info_by_id(column_id)
                    )
            metric_infos.append(_covert_metric_info_qdrant_to_state(metric_info_qdrant))

        # 1.3.收集召回的字段值信息列表对应的字段信息列表->将字段值保存到字段的值的阳历列表中
        for value_info_es in recall_values:
            column_id = value_info_es.get("column_id")
            if column_id not in column_infos_dict:
                # 只有没有这个字段id这个key,也就是没有这个字段信息，才查询添加
                column_infos_dict[column_id] = _covert_column_info_mysql_to_qdrant(
                    await meta_repository.get_column_info_by_id(column_id)
                )
            # 因为这个字段值通过全文检索查询出来的，相比其它字段值例子，对于llm更有价值，所以添加到对应字段信息的例子里
            value = value_info_es.get("value")
            examples = column_infos_dict.get(column_id).get("examples")
            if value not in examples:
                # 这里的examples和当前字段信息的examples是引用的同一个列表，可以这样赋值
                examples.append(value)

        # 2.根据收集所有字段信息列表生成：带字段信息列表的表信息列表
        # 2.1.对收集的字段信息列表进行按表id进行分组:dict[table_id,list[ColumnInfoQdrant]]
        table_column_infos_dict: dict[str, list[ColumnInfoQdrant]] = {}
        for column_id, column_info in column_infos_dict.items():
            # 根据table_id进行分组，首次添加对应table_id对应的字段信息时，先初始化空列表，有的话获取对应的列表添加其字段信息
            table_column_infos_dict.setdefault(column_info.get("table_id"), []).append(
                column_info
            )
        # 最终完整的table_infos信息
        table_infos: list[TableInfoState] = []
        # 1.4.收集相关的主键和外键字段信息列表，这里补充收集，这个需要分完组的table_column_infos_dict
        for table_id, column_infos in table_column_infos_dict.items():
            # 通过table_id查询对应的主键和外键字段信息列表
            key_column_infos = await meta_repository.get_key_column_infos_by_table_id(
                table_id
            )
            for key_column_info in key_column_infos:
                # 因为column_infos_dict->table_column_infos_dict->column_infos
                # 所以key_column_info字段信息不在column_infos_dict这里面相当于不在column_infos
                if key_column_info.id not in column_infos_dict:
                    column_infos.append(
                        _covert_column_info_mysql_to_qdrant(key_column_info)
                    )
            # 2.3.生成带字段信息列表的表信息列表->table_infos:list[TableInfoState]
            # 根据id查询meta数据库中的table_info表得到表信息
            table_info_mysql: TableInfoORM = (
                await meta_repository.get_table_infos_by_id(table_id)
            )
            # 根据当前字段信息列表,生成columnInfoState类型的字段状态信息列表
            columns: list[ColumnInfoState] = [
                _covert_column_info_qdrant_to_state(column_info_qdrant)
                for column_info_qdrant in column_infos
            ]
            # 组合成完整的TableInfoState对象添加到table_infos中
            table_infos.append(
                TableInfoState(
                    name=table_info_mysql.name,
                    role=table_info_mysql.role,
                    description=table_info_mysql.description,
                    columns=columns,
                )
            )
        # 向图外输出数据，必须配合custom模式
        runtime.stream_writer({"stage":"召回合并信息成功"})
        logger.info(f"合并召回成功 表信息列表：{table_infos}")
        logger.info(f"合并召回成功 指标信息列表：{metric_infos}")
        return {"table_infos": table_infos, "metric_infos": metric_infos}
    except Exception:
        logger.error("召回合并信息失败")
        raise


def _covert_column_info_mysql_to_qdrant(
    column_info_mysql: ColumnInfoORM,
) -> ColumnInfoQdrant:
    """
    将字段信息的ORM对象->Qdrant对象

    Args:
        column_info_mysql (ColumnInfoORM): 字段信息的ORM对象(数据库查询的对象)

    Returns:
        ColumnInfoQdrant: 字段信息的Qdrant对象
    """

    return ColumnInfoQdrant(
        id=column_info_mysql.id,
        name=column_info_mysql.name,
        type=column_info_mysql.type,
        role=column_info_mysql.role,
        examples=column_info_mysql.examples,
        description=column_info_mysql.description,
        alias=column_info_mysql.alias,
        table_id=column_info_mysql.table_id,
    )


def _covert_column_info_qdrant_to_state(
    column_info_qdrant: ColumnInfoQdrant,
) -> ColumnInfoState:
    """
    将字段信息的Qdrant对象->State对象

    Args:
        column_info_qdrant (ColumnInfoQdrant): ColumnInfoQdrant对象

    Returns:
        ColumnInfoState: ColumnInfoState对象
    """

    return ColumnInfoState(
        name=column_info_qdrant.get("name"),
        description=column_info_qdrant.get("description"),
        examples=column_info_qdrant.get("examples"),
        alias=column_info_qdrant.get("alias"),
        role=column_info_qdrant.get("role"),
        type=column_info_qdrant.get("type")

    )


def _covert_metric_info_qdrant_to_state(
    metric_info_qdrant: MetricInfoQdrant,
) -> MetricInfoState:
    """
    将指标信息的Qdrant对象->State对象

    Args:
        metric_info_qdrant (MetricInfoQdrant): MetricInfoQdrant对象

    Returns:
        MetricInfoState: MetricInfoState对象
    """
    return MetricInfoState(
        name=metric_info_qdrant.get("name"),
        description=metric_info_qdrant.get("description"),
        relevant_columns=metric_info_qdrant.get("relevant_columns"),
        alias=metric_info_qdrant.get("alias"),
    )
