#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML处理模块

负责YAML文件的自定义标签处理和序列化/反序列化。
"""

import yaml

from .enums import KeyType


def keytype_constructor(loader, node):
    """YAML构造函数：将!KeyType标签解析为KeyType枚举
    
    使用方式在YAML文件中：
        key_type: !KeyType global
        key_type: !KeyType group
        key_type: !KeyType table
    
    Args:
        loader: YAML加载器
        node: YAML节点
        
    Returns:
        KeyType: 解析后的枚举值
        
    Raises:
        yaml.YAMLError: 当值无效时
    """
    value = loader.construct_scalar(node)
    try:
        return KeyType(value.lower())
    except ValueError:
        raise yaml.YAMLError(f"无效的KeyType值: {value}，必须为 table/group/global")


def keytype_representer(dumper, data):
    """YAML表示器：将KeyType枚举转换为!KeyType标签
    
    Args:
        dumper: YAML转储器
        data: KeyType枚举值
        
    Returns:
        ScalarNode: YAML标量节点
    """
    return dumper.represent_scalar('!KeyType', data.value)


def register_yaml_handlers():
    """注册自定义YAML构造函数和表示器
    
    必须在加载/保存YAML之前调用。
    """
    yaml.add_constructor('!KeyType', keytype_constructor, Loader=yaml.SafeLoader)
    yaml.add_representer(KeyType, keytype_representer, Dumper=yaml.SafeDumper)


# 在模块导入时自动注册
register_yaml_handlers()
