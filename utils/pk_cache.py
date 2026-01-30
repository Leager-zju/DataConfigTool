#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主键缓存管理模块

管理全局和分组级别的主键约束缓存，支持跨表/跨分组的主键验证。
缓存只存储主键值及其关联的表和分组信息，不存储冗余数据。
"""

from typing import Dict, Set

from .enums import KeyType

# 分组主键缓存
# 结构：{group_name: {pk_values: (table_name)}}
_group_pk_caches: Dict[str, Dict[int, str]] = {}

# 全局主键缓存：记录每个主键值在哪个分组的哪个表中
# 结构：{pk_values: (group_name, table_name)}
_global_pk_cache: Dict[int, tuple] = {}

# 所有主键池：记录所有主键值及其所属分组和表
# 结构：{pk_values: (group_name, table_name)}
_all_pk_pool: Dict[int, tuple] = {}

def clear_pk_caches():
    """清空所有主键缓存"""
    global _group_pk_caches, _global_pk_cache, _all_pk_pool
    _group_pk_caches.clear()
    _global_pk_cache.clear()
    _all_pk_pool.clear()

def validate_primary_key(group_name: str, table_name: str, pk_value: int, key_type: KeyType):
    """验证并添加主键到缓存
    
    Args:
        group_name: 分组名
        table_name: 表名
        pk_value: 主键值
        key_type: 主键类型
    """
    if group_name not in _group_pk_caches:
        _group_pk_caches[group_name] = {}
    
    if pk_value in _group_pk_caches[group_name]:
        raise ValueError(f"主键冲突：Key {pk_value} 已存在分组 {group_name} 的表 {table_name} 中")
    
    if pk_value in _global_pk_cache:
        raise ValueError(f"主键冲突：Key {pk_value} 已存在分组 {_global_pk_cache[pk_value][0]} 的表 {_global_pk_cache[pk_value][1]} 中")
    
    if key_type == KeyType.GLOBAL and pk_value in _all_pk_pool:
        raise ValueError(f"主键冲突：Key {pk_value} 已存在分组 {_all_pk_pool[pk_value][0]} 的表 {_all_pk_pool[pk_value][1]} 中")

    _group_pk_caches[group_name][pk_value] = table_name
    _all_pk_pool[pk_value] = (group_name, table_name)

    if key_type == KeyType.GLOBAL:
        _global_pk_cache[pk_value] = (group_name, table_name)

def apply_pk_diff(group_name: str, table_name: str, remove_list: Set[int], add_lists: Set[int], key_type: KeyType):
    """应用主键差异，更新缓存
    
    Args:
        group_name: 分组名
        table_name: 表名
        remove_list: 要移除的主键集合
        add_lists: 要添加的主键集合
        key_type: 主键类型
    """
    if group_name not in _group_pk_caches:
        _group_pk_caches[group_name] = {}
    
    for pk_value in remove_list:
        if pk_value in _group_pk_caches[group_name]:
            del _group_pk_caches[group_name][pk_value]
        if pk_value in _all_pk_pool:
            del _all_pk_pool[pk_value]
        if key_type == KeyType.GLOBAL and pk_value in _global_pk_cache:
            del _global_pk_cache[pk_value]
    
    for pk_value in add_lists:
        pk_value = int(pk_value)
        validate_primary_key(group_name, table_name, pk_value, key_type)