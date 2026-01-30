#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

处理YAML和Excel之间的转换，支持强类型数据验证和多级主键约束。

主要功能：
- 配置表的YAML存储和加载
- Excel临时文件的创建和同步
- 强类型数据验证和转换
- 配置表的批量管理
- 支持两种主键约束：GROUP/GLOBAL

模块结构：
- enums: 枚举类型定义
- caches: 主键缓存管理
- models: 数据模型（ColumnDef, ConfigTable）
- yaml_handlers: YAML处理和自定义标签
- excel: Excel文件操作和格式化
- storage: 文件存储操作
- sync: Excel到YAML的数据同步

公开接口：
- KeyType: 主键类型枚举
- ColumnDef: 列定义类
- ConfigTable: 配置表类
- 所有存储和同步函数
"""

# 导入所有公开接口
from .enums import KeyType
from .models import ColumnDef, ConfigTable
from .pk_cache import (
    clear_pk_caches,
    validate_primary_key,
    apply_pk_diff
)
from .storage import (
    load_table,
    save_table,
    create_table,
    get_group_tables,
    get_all_tables,
    load_all_tables_for_validation,
    get_config_dir,
    create_temp_excel,
    create_temp_excel_for_group
)
from .excel import format_worktable, get_next_primary_key
from .sync import (
    sync_excel_to_yaml,
    sync_excel_to_all_yaml,
)
from . import yaml_handlers  # 注册自定义YAML处理器

# ============================================================================
# 公开API列表
# ============================================================================

__all__ = [
    # 类型和枚举
    'KeyType',
    'ColumnDef',
    'ConfigTable',
    
    # 缓存操作
    'clear_pk_caches',
    'validate_primary_key',
    "apply_pk_diff",

    # 存储操作
    'load_table',
    'save_table',
    'create_table',
    'get_group_tables',
    'get_all_tables',
    'load_all_tables_for_validation',
    'get_config_dir',
    
    # Excel操作
    'format_worktable',
    'get_next_primary_key',
    'create_temp_excel',
    'create_temp_excel_for_group',
    
    # 数据同步
    'sync_excel_to_yaml',
    'sync_excel_to_all_yaml',
]
