#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主键缓存管理模块

管理全局和分组级别的主键约束缓存，支持跨表/跨分组的主键验证。
"""

from typing import Dict, Any, Tuple

# 全局主键缓存（用于跨表/跨分组的主键验证）
# 结构：{pk_value: (table_name, group_name, column_name)}
_global_pk_cache: Dict[Any, Tuple[str, str, str]] = {}

# 分组主键缓存
# 结构：{group_name: {pk_value: (table_name, column_name)}}
_group_pk_caches: Dict[str, Dict[Any, Tuple[str, str]]] = {}


def clear_pk_caches():
    """清空所有主键缓存"""
    global _global_pk_cache, _group_pk_caches
    _global_pk_cache.clear()
    _group_pk_caches.clear()


def get_global_pk_cache() -> Dict[Any, Tuple[str, str, str]]:
    """获取全局主键缓存
    
    Returns:
        Dict[Any, Tuple[str, str, str]]: 全局主键缓存
    """
    return _global_pk_cache


def get_group_pk_caches() -> Dict[str, Dict[Any, Tuple[str, str]]]:
    """获取分组主键缓存
    
    Returns:
        Dict[str, Dict[Any, Tuple[str, str]]]: 分组主键缓存
    """
    return _group_pk_caches


def add_global_pk(pk_value: Any, table_name: str, group_name: str, column_name: str):
    """添加全局主键到缓存
    
    Args:
        pk_value: 主键值
        table_name: 表名
        group_name: 分组名
        column_name: 列名
    """
    _global_pk_cache[pk_value] = (table_name, group_name, column_name)


def add_group_pk(group_name: str, pk_value: Any, table_name: str, column_name: str):
    """添加分组主键到缓存
    
    Args:
        group_name: 分组名
        pk_value: 主键值
        table_name: 表名
        column_name: 列名
    """
    if group_name not in _group_pk_caches:
        _group_pk_caches[group_name] = {}
    _group_pk_caches[group_name][pk_value] = (table_name, column_name)
