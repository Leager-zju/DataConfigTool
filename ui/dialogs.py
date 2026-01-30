#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框组件模块

提供各种对话框组件，包括创建表对话框等。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import utils
from utils.setting_data import SettingData, PathKey
from utils.enums import KeyType


class CreateTableDialog:
    """创建新配置表对话框
    
    提供用户友好的界面来创建新的配置表，包括：
    - 分组名称和配置表名称输入
    - 列定义的文本编辑器
    - 数据验证和错误处理
    - 文件路径预览
    """

    def __init__(self, parent):
        self.working_dir = SettingData.get_instance().get_path(PathKey.DATA_CONFIG_DIR)
        self.result = None  # 存储创建结果

        # 创建模态对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("创建新配置表")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()

    def _create_ui(self):
        """创建对话框UI组件"""
        # 分组名称输入
        ttk.Label(self.dialog, text="分组名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.group_entry = ttk.Entry(self.dialog, width=35)
        self.group_entry.grid(row=0, column=1, padx=10, pady=10)

        # 配置表名称输入
        ttk.Label(self.dialog, text="配置表名称:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.table_entry = ttk.Entry(self.dialog, width=35)
        self.table_entry.grid(row=1, column=1, padx=10, pady=10)
        self.table_entry.insert(0, "Table1")  # 默认名称

        # 主键类型选择
        ttk.Label(self.dialog, text="主键类型:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.key_type_var = tk.StringVar(value=KeyType.GROUP.value)
        key_type_combo = ttk.Combobox(
            self.dialog,
            textvariable=self.key_type_var,
            values=[kt.value for kt in KeyType],
            state="readonly",
            width=32
        )
        key_type_combo.grid(row=2, column=1, padx=10, pady=10)
        
        # 主键类型说明
        help_text = ttk.Label(
            self.dialog,
            text="• table: 在同一表中唯一  • group: 在同一分组中唯一  • global: 全局唯一",
            foreground="gray",
            font=("", 8)
        )
        help_text.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

        # 列定义输入区域
        ttk.Label(self.dialog, text="列定义 (每行一个，格式: 名称:类型):").grid(
            row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W
        )

        # 列定义文本编辑器
        self.columns_text = tk.Text(self.dialog, width=55, height=12)
        self.columns_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
        # 默认列定义示例
        default_columns = "id:int\nname:string\nvalue:float\ndescription:string\nenabled:bool"
        self.columns_text.insert(1.0, default_columns)

        # 文件路径提示
        path_hint = ttk.Label(self.dialog, text="文件将保存至: /分组名称/配置表名称.yaml",
                             foreground="gray")
        path_hint.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

        # 按钮区域
        self._create_buttons()

    def _create_buttons(self):
        """创建对话框按钮"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=7, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="创建", command=self.create).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)

    def create(self):
        """创建新的配置表
        
        验证用户输入，解析列定义，创建目录和文件。
        如果创建成功，关闭对话框并返回结果。
        """
        # 获取用户输入
        group_name = self.group_entry.get().strip()
        table_name = self.table_entry.get().strip()
        columns_text = self.columns_text.get(1.0, tk.END).strip()
        key_type_str = self.key_type_var.get()

        # 验证必填项
        if not group_name or not table_name or not columns_text:
            messagebox.showwarning("警告", "请填写所有必填项")
            return

        try:
            # 解析列定义
            from utils import ColumnDef
            columns = []
            
            for line_num, line in enumerate(columns_text.split("\n"), 1):
                line = line.strip()
                if not line:
                    continue  # 跳过空行
                    
                parts = line.split(":")
                if len(parts) != 2:
                    raise ValueError(f"第{line_num}行列定义格式错误: {line}\n正确格式: 列名:类型")
                    
                col_name, col_type = parts[0].strip(), parts[1].strip()
                
                # 验证数据类型
                valid_types = ["int", "float", "string", "bool", "list", "dict"]
                if col_type not in valid_types:
                    raise ValueError(f"不支持的数据类型: {col_type}\n支持的类型: {', '.join(valid_types)}")
                    
                columns.append(ColumnDef(name=col_name, type=col_type))

            if not columns:
                raise ValueError("至少需要定义一列")

            # 获取选择的主键类型
            key_type = KeyType(key_type_str)

            # 创建目录和文件
            group_dir = self.working_dir / group_name
            group_dir.mkdir(exist_ok=True)
            table_path = group_dir / f"{table_name}.yaml"

            # 检查文件是否已存在
            if table_path.exists():
                if not messagebox.askyesno("文件已存在", f"文件 {table_path.name} 已存在，是否覆盖？"):
                    return
            
            utils.create_table(table_path, table_name, group_name, columns, key_type)

            self.result = f"{group_name}/{table_name}"
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"创建失败: {str(e)}")
