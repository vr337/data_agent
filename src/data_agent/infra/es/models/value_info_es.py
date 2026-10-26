from typing import TypedDict


class ValueInfoES(TypedDict):
    """字段值信息的模型类(ES)"""

    id: str # 字段值id(表名.字段名.字段值)
    value: str # 字段值
    type: str # 字段类型
    column_id: str #字段id
    column_name: str # 字段名称
    table_id: str # 关联的表id
    table_name: str # 关联的表名称
