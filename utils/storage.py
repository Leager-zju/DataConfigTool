#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储操作模块

负责配置表文件的加载、保存和查询。
"""

import yaml
from pathlib import Path
from typing import Dict, List

from .models import ConfigTable, ColumnDef
from .enums import KeyType
from .caches import clear_pk_caches, add_global_pk, add_group_pk
from .setting_data import SettingData, PathKey as SettingPathKey
from . import yaml_handlers  # 注册自定义YAML处理器


# 获取配置目录
_config_dir = SettingData.get_instance().get_path(SettingPathKey.DATA_CONFIG_DIR)


def get_config_dir() -> Path:
    """获取配置目录路径
    
    Returns:
        Path: 配置目录路径
    """
    return _config_dir


def load_table(table_path: Path) -> ConfigTable:
    """从YAML文件加载单个配置表
    
    加载完成后会自动更新主键缓存。
    
    Args:
        table_path: YAML文件路径
        
    Returns:
        ConfigTable: 加载的配置表对象
        
    Raises:
        FileNotFoundError: 当文件不存在时
        yaml.YAMLError: 当YAML格式错误时
        ValueError: 当主键验证失败时
    """
    with open(table_path, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    table = ConfigTable.from_dict(data)
    
    # 加载后验证并缓存主键
    _rebuild_pk_cache_for_table(table)
    
    return table


def save_table(table: ConfigTable, table_path: Path):
    """保存配置表到YAML文件
    
    Args:
        table: 要保存的配置表对象
        table_path: 目标YAML文件路径
        
    Raises:
        IOError: 当文件写入失败时
    """
    # 确保目录存在
    table_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(table_path, "w", encoding="utf-8") as f:
        yaml.dump(table.to_dict(), f, allow_unicode=True, sort_keys=False)


def create_table(table_path: Path, table_name: str, group_name: str, columns: List[ColumnDef], key_type: KeyType = KeyType.TABLE):
    """创建新的配置表
    
    Args:
        table_path: 新配置表的文件路径
        table_name: 配置表名称
        group_name: 所属组名称
        columns: 列定义列表
        key_type: 主键类型（默认为TABLE）
    """
    table = ConfigTable(table_name=table_name, group_name=group_name, columns=columns, key_type=key_type)
    save_table(table, table_path)


def get_group_tables(group_name: str) -> List[Path]:
    """获取指定组的所有配置表文件
    
    Args:
        group_name: 组名
        
    Returns:
        List[Path]: 排序后的配置表文件路径列表
    """
    table_path = _config_dir / group_name
    if not table_path.exists():
        return []
    
    pattern = "*.yaml"
    return sorted(table_path.glob(pattern))


def get_all_tables() -> Dict[str, List[Path]]:
    """获取所有组别及其配置表文件

    扫描配置目录，按组返回所有配置表文件。
    
    Returns:
        Dict[str, List[Path]]: 组名到配置表文件列表的映射
    """
    tables = {}
    
    # 搜索所有YAML文件
    yaml_files = list(_config_dir.rglob("*.yaml")) + list(_config_dir.rglob("*.yml"))

    for yaml_file in yaml_files:
        # 使用父目录名作为组名
        group_name = yaml_file.parent.name
        
        # 跳过缓存目录
        if group_name == ".cache":
            continue

        if group_name not in tables:
            tables[group_name] = []
        tables[group_name].append(yaml_file)

    return tables


def _rebuild_pk_cache_for_table(table: ConfigTable):
    """为单个表重建主键缓存
    
    Args:
        table: 配置表对象
    """
    if not table.columns:
        return
    
    pk_column_name = table.columns[0].name
    
    for row in table.data:
        pk_value = row.get(pk_column_name)
        if pk_value is None or pk_value == "":
            continue
        
        # 添加到适应的缓存级别
        if table.key_type == KeyType.TABLE:
            # TABLE类型不需要全局缓存
            pass
        elif table.key_type == KeyType.GROUP:
            # 添加到分组缓存
            add_group_pk(table.group_name, pk_value, table.table_name, pk_column_name)
        elif table.key_type == KeyType.GLOBAL:
            # 添加到全局缓存
            add_global_pk(pk_value, table.table_name, table.group_name, pk_column_name)


def load_all_tables_for_validation():
    """加载所有表以进行跨表/跨分组的主键验证
    
    用于初始化全局和分组主键缓存。
    """
    clear_pk_caches()
    tables = get_all_tables()
    
    for group_name in tables.keys():
        table_files = tables[group_name]
        for table_file in table_files:
            try:
                # 重新加载（不会再触发缓存构建）
                with open(table_file, "r", encoding="utf-8") as f:
                    data = yaml.load(f, Loader=yaml.SafeLoader)
                table = ConfigTable.from_dict(data)
                _rebuild_pk_cache_for_table(table)
            except Exception as e:
                print(f"警告：加载表 {table_file} 失败：{e}")
