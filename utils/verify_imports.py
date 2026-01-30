#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入验证脚本

用于验证所有模块的导入是否正确，无循环依赖。
"""

import sys
from pathlib import Path

# 添加utils目录到路径
utils_dir = Path(__file__).parent

print("=" * 60)
print("开始验证utils模块导入...")
print("=" * 60)

try:
    # 1. 验证基础模块
    print("\n[1/8] 验证 enums 模块...", end=" ")
    from utils.enums import KeyType
    print("✓")
    
    # 2. 验证缓存模块
    print("[2/8] 验证 caches 模块...", end=" ")
    from utils.pk_cache import clear_pk_caches, get_global_pk_cache, get_group_pk_caches
    print("✓")
    
    # 3. 验证数据模型
    print("[3/8] 验证 models 模块...", end=" ")
    from utils.models import ColumnDef, ConfigTable
    print("✓")
    
    # 4. 验证YAML处理
    print("[4/8] 验证 yaml_handlers 模块...", end=" ")
    import utils.yaml_handlers
    print("✓")
    
    # 5. 验证Excel处理
    print("[5/8] 验证 excel 模块...", end=" ")
    from utils.excel import format_worktable, get_next_primary_key
    print("✓")
    
    # 6. 验证存储模块
    print("[6/8] 验证 storage 模块...", end=" ")
    from utils.storage import (
        load_table, save_table, create_table,
        get_group_tables, get_all_tables,
        load_all_tables_for_validation, get_config_dir
    )
    print("✓")
    
    # 7. 验证同步模块
    print("[7/8] 验证 sync 模块...", end=" ")
    from utils.sync import sync_excel_to_yaml, sync_excel_to_all_yaml
    print("✓")
    
    # 8. 验证主模块
    print("[8/8] 验证 __init__ 模块...", end=" ")
    import utils
    print("✓")
    
    print("\n" + "=" * 60)
    print("✓ 所有模块导入验证通过！")
    print("=" * 60)
    
    # 验证公开接口
    print("\n验证公开接口...")
    print(f"  - KeyType: {utils.KeyType}")
    print(f"  - ColumnDef: {utils.ColumnDef}")
    print(f"  - ConfigTable: {utils.ConfigTable}")
    print(f"  - create_temp_excel: {utils.create_temp_excel}")
    print(f"  - create_temp_excel_for_group: {utils.create_temp_excel_for_group}")
    print(f"  - load_table: {utils.load_table}")
    print(f"  - save_table: {utils.save_table}")
    
    print("\n✓ 所有公开接口验证通过！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
