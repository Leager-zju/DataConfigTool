#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步模块

负责Excel和YAML之间的数据同步，包括数据验证和自动填充。
"""

import openpyxl
from pathlib import Path

from .models import ConfigTable
from .storage import load_table, save_table
from .caches import clear_pk_caches


def sync_excel_to_yaml_internal(ws, table_path: Path):
    """将Excel工作表的修改同步到YAML文件（内部函数）
    
    从Excel工作表读取数据，验证后更新对应的YAML文件。
    跳过完全空白的行。
    如果第一列（主键）为空，自动填充为上一行+1。
    
    Excel格式：
    - 第1行：列名
    - 第2行：数据类型
    - 第3行：主键信息（KEY(type)）
    - 第4行以后：数据行
    
    Args:
        ws: openpyxl工作表对象
        table_path: 目标YAML文件路径
        
    Raises:
        Exception: 当数据验证、主键冲突或文件保存失败时
    """
    # 加载原始配置表结构
    table = load_table(table_path)
    
    if not table.columns:
        raise ValueError(f"配置表 {table.table_name} 没有列定义")
    
    pk_column_name = table.columns[0].name  # 第一列总是主键

    # 读取Excel中的列名（第一行）
    column_names = []
    for col_idx in range(1, ws.max_column + 1):
        col_name = ws.cell(row=1, column=col_idx).value
        if col_name:
            column_names.append(col_name)

    # 读取数据行（从第四行开始，跳过类型行和主键信息行）
    new_data = []
    for row_idx in range(4, ws.max_row + 1):
        row_data = {}
        is_empty_row = True

        # 读取每列的值
        for col_idx, col_name in enumerate(column_names, start=1):
            value = ws.cell(row=row_idx, column=col_idx).value
            if value is not None and value != "":
                is_empty_row = False
            row_data[col_name] = value

        # 跳过空行
        if not is_empty_row:
            # 处理主键自动填充（第一列）
            pk_value = row_data.get(pk_column_name)
            
            # 如果主键为空，自动填充为上一行+1
            if pk_value is None or pk_value == "":
                if new_data:
                    # 从上一行的主键+1
                    last_pk = new_data[-1].get(pk_column_name, 0)
                    if isinstance(last_pk, int):
                        row_data[pk_column_name] = last_pk + 1
                    else:
                        row_data[pk_column_name] = 1
                else:
                    # 第一行使用1作为初始值
                    row_data[pk_column_name] = 1
                
                # 更新Excel单元格
                pk_col_idx = column_names.index(pk_column_name) + 1
                ws.cell(row=row_idx, column=pk_col_idx, value=row_data[pk_column_name])
            
            # 验证数据类型
            validated_row = {}
            for col in table.columns:
                if col.name in row_data:
                    validated_row[col.name] = col.validate_value(row_data[col.name])
            
            # 验证主键约束
            try:
                table.data = new_data  # 临时更新数据用于验证
                table._validate_primary_key(validated_row)
            except ValueError as e:
                raise ValueError(f"第{row_idx}行：{str(e)}")
            
            new_data.append(validated_row)

    # 更新配置表数据并保存
    table.data = new_data
    save_table(table, table_path)


def sync_excel_to_yaml(excel_path: Path, table_path: Path):
    """将单个配置表的Excel修改同步到YAML
    
    Args:
        excel_path: Excel文件路径
        table_path: 目标YAML文件路径
    """
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    sync_excel_to_yaml_internal(ws, table_path)


def sync_excel_to_all_yaml(excel_path: Path, group_name: str):
    """将多个Excel文件的修改同步到整个分组的所有配置表文件
    
    Args:
        excel_path: Excel文件路径
        group_name: 分组名称
    """
    from .storage import get_config_dir
    
    wb = openpyxl.load_workbook(excel_path)
    group_path = get_config_dir() / group_name
    
    for ws in wb.sheetnames:
        table_path = group_path / f"{ws}.yaml"
        if not table_path.exists():
            print(f"警告：文件 {table_path} 不存在，跳过同步")
            continue

        sync_excel_to_yaml_internal(wb[ws], table_path)
