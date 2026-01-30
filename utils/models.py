#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义模块

定义配置系统的核心数据结构。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

from .enums import KeyType
from .pk_cache import validate_primary_key


@dataclass
class ColumnDef:
    """列定义类
    
    定义配置表中每一列的属性，包括名称、数据类型、描述和默认值。
    
    支持的数据类型：
    - int, float, string, bool: 基本类型
    - List<T>, Dictionary<K, V>: 复杂类型
    
    注意：
    每个配置表的第一列必须为int类型的主键列
    
    Attributes:
        name (str): 列名
        type (str): 数据类型
        description (str): 列描述
        default (Any): 默认值
    """
    name: str  # 列名
    type: str  # 数据类型：int, float, string, bool, List<T>, Dictionary<K, V>
    description: str = ""  # 列描述
    default: Any = None  # 默认值

    def validate_value(self, value: Any) -> Any:
        """验证并转换值为指定类型
        
        Args:
            value: 要验证的原始值
            
        Returns:
            Any: 转换后的值，如果为空则返回None
            
        Raises:
            ValueError: 当值无法转换为指定类型时
        """
        # 处理空值情况
        if value is None or value == "":
            return None

        try:
            # 根据类型进行转换
            if self.type == "int":
                return int(value)
            elif self.type == "float":
                return float(value)
            elif self.type == "string":
                return str(value)
            elif self.type == "bool":
                if isinstance(value, bool):
                    return value
                # 字符串转布尔值
                return str(value).lower() in ("true", "1", "yes")
            elif self.type.startswith("List"):
                if isinstance(value, list):
                    return value
                # 尝试从JSON字符串解析
                import json
                return json.loads(value) if isinstance(value, str) else [value]
            elif self.type.startswith("Dictionary"):
                if isinstance(value, dict):
                    return value
                # 尝试从JSON字符串解析
                import json
                return json.loads(value) if isinstance(value, str) else {}
            else:
                # 未知类型直接返回
                return value
        except Exception as e:
            raise ValueError(f"列 {self.name} 的值 {value} 无法转换为 {self.type}: {e}")


@dataclass
class ConfigTable:
    """配置表类
    
    表示一个完整的配置表，包含表名、列定义和数据行。
    
    支持数据验证、序列化和反序列化功能。
    每个表有一个主键约束类型（Table/Group/Global）。
    
    Attributes:
        table_name (str): 表名
        group_name (str): 分组名
        key_type (KeyType): 主键约束类型
        columns (List[ColumnDef]): 列定义列表
        data (List[Dict[str, Any]]): 数据行列表
    """
    table_name: str
    group_name: str
    key_type: KeyType = KeyType.GROUP  # 主键约束类型
    columns: List[ColumnDef] = field(default_factory=list)
    data: List[Dict[str, Any]] = field(default_factory=list)

    def validate_all_primary_keys(self):
        """验证所有数据行的主键约束
        
        遍历表中的所有数据行，验证主键列的值是否符合表的主键约束类型。
        
        Raises:
            ValueError: 当发现主键冲突时
        """
        if not self.columns:
            return
        
        pk_column = self.columns[0]
        
        for row in self.data:
            pk_value = row.get(pk_column.name)
            if pk_value is None or pk_value == "":
                continue
            
            validate_primary_key(self.group_name, self.table_name, pk_value, self.key_type)

    def validate_pk_by_row(self, row_data: Dict[str, Any]):
        """验证主键的约束
        
        根据表的key_type（GROUP/GLOBAL），进行不同级别的主键验证。
        
        验证级别：
        1. GROUP: 检查同一分组中是否重复
        2. GLOBAL: 检查全局是否重复
        
        Args:
            row_data: 新行的数据
            
        Raises:
            ValueError: 当主键冲突时
        """
        if not self.columns:
            return
        
        pk_column = self.columns[0]
        pk_value = row_data.get(pk_column.name)
        
        if pk_value is None or pk_value == "":
            return
        
        self.validate_key_func[self.key_type](self.group_name, self.table_name, pk_value)

    def to_dict(self) -> Dict:
        """转换为字典格式，用于序列化
        
        Returns:
            Dict: 包含所有配置表信息的字典
        """
        return {
            "table_name": self.table_name,
            "group_name": self.group_name,
            "key_type": self.key_type.value if isinstance(self.key_type, KeyType) else self.key_type,
            "columns": [
                {
                    "name": col.name,
                    "type": col.type,
                    "description": col.description,
                    "default": col.default
                }
                for col in self.columns
            ],
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConfigTable":
        """从字典创建配置表实例
        
        Args:
            data: 包含配置表信息的字典
            
        Returns:
            ConfigTable: 新创建的配置表实例
        """
        table = cls(
            table_name=data.get("table_name", ""),
            group_name=data.get("group_name", "")
        )
        
        # 加载主键类型
        key_type_str = data.get("key_type", "group")
        if isinstance(key_type_str, str):
            try:
                table.key_type = KeyType(key_type_str)
            except ValueError:
                table.key_type = KeyType.GROUP
        elif isinstance(key_type_str, KeyType):
            table.key_type = key_type_str
        else:
            table.key_type = KeyType.GROUP

        # 加载列定义
        for col_data in data.get("columns", []):
            table.columns.append(ColumnDef(
                name=col_data["name"],
                type=col_data["type"],
                description=col_data.get("description", ""),
                default=col_data.get("default")
            ))

        # 加载数据行
        table.data = data.get("data", [])

        return table
