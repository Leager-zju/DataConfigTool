#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
枚举类型定义模块

定义系统中使用的枚举类型。
"""

from enum import Enum


class KeyType(Enum):
    """主键类型枚举
    
    定义不同级别的主键约束类型：
    - TABLE: 在同一表中唯一
    - GROUP: 在同一分组中唯一
    - GLOBAL: 全局唯一
    
    Attributes:
        TABLE (str): 表级约束
        GROUP (str): 分组级约束
        GLOBAL (str): 全局约束
    """
    TABLE = "table"
    GROUP = "group"
    GLOBAL = "global"
    
    def __str__(self):
        return self.value
