#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件树视图组件模块

提供配置表的树形视图显示和管理功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from pathlib import Path
from typing import Dict
import threading

import utils
from utils.binary_exporter import BinaryExporter
from utils.code_exporter import CodeExporter
from utils.setting_data import SettingData, PathKey


class FileTreeFrame(ttk.Frame):
    """文件树视图组件
    
    提供配置表的树形视图显示和管理功能，包括：
    - 按分组分组显示配置表
    - 双击打开Excel编辑
    - 右键菜单操作（打开、导出、删除）
    - 实时文件监控和同步
    - 状态信息显示
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 初始化目录路径
        self.data_config_dir = SettingData.get_instance().get_path(PathKey.DATA_CONFIG_DIR)
        self.bin_export_dir = self.data_config_dir / "bin"
        self.bin_export_dir.mkdir(parents=True, exist_ok=True)
        self.code_export_dir = SettingData.get_instance().get_path(PathKey.CODE_EXPORT_DIR)
        self.code_export_dir.mkdir(parents=True, exist_ok=True)

        # 当前打开的Excel文件路径缓存
        self.current_excel_files: Dict[str, Path] = {}

        # 回调函数（用于通知外部组件状态变化）
        self.on_status_update = None
        self.on_info_display = None

        self._create_ui()

    def _create_ui(self):
        """创建UI组件和布局"""
        # 标题标签
        tree_label = ttk.Label(self, text="配置表列表", font=("Arial", 10, "bold"))
        tree_label.pack(pady=5)

        # 树形控件容器框架
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 主树形控件
        self.tree = ttk.Treeview(tree_frame, selectmode="browse")
        self.tree.heading("#0", text="配置表/Table")

        # 添加滚动条支持
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

        # 布局树形控件和滚动条
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 绑定事件处理器
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # 创建右键菜单
        self._create_context_menu()

    def _create_context_menu(self):
        """创建右键上下文菜单"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="打开", command=self.open_selected_item)
        self.context_menu.add_command(label="本地导出配置", command=self.export_selected_table)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_selected_item)
        
        # 绑定右键点击事件
        self.tree.bind("<Button-3>", self._show_context_menu)

    def set_callbacks(self, on_status_update=None, on_info_display=None):
        """设置回调函数用于与外部组件通信
        
        Args:
            on_status_update: 状态更新回调函数
            on_info_display: 信息显示回调函数
        """
        if on_status_update:
            self.on_status_update = on_status_update
        if on_info_display:
            self.on_info_display = on_info_display

    def refresh(self):
        """刷新文件树显示，重新加载所有配置表"""
        # 清空现有节点
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 加载所有分组和配置表
        tables = utils.get_all_tables()
        for group_name in sorted(tables.keys()):
            table_files = tables[group_name]

            # 添加分组节点（使用文件夹图标）
            parent_id = self.tree.insert("", "end", text=f"📁 {group_name}",
                                        values=(group_name,),
                                        tags=("group",))

            # 添加配置表节点
            for table_file in sorted(table_files):
                try:
                    table = utils.load_table(table_file)
                    self.tree.insert(parent_id, "end", text=f"  📄 {table.table_name}",
                                   values=(str(table_file),),
                                   tags=("table",))
                except Exception as e:
                    # 显示加载错误的文件
                    self.tree.insert(parent_id, "end", text=f"  ⚠️ {table_file.stem}: {str(e)}",
                                   tags=("error",))

        # 更新状态信息
        total_tables = sum(len(files) for files in tables.values())
        self._update_status(f"已加载 {len(tables)} 个分组，共 {total_tables} 个配置表")

    def get_selection_info(self):
        """获取当前选中项的详细信息
        
        Returns:
            dict: 包含选中项信息的字典，或None如果没有选中项
                - item: 树节点ID
                - path: 文件路径或分组名
                - tag: (group/table/error）
        """
        selection = self.tree.selection()
        if not selection:
            return None

        item = selection[0]
        values = self.tree.item(item, "values")
        tags = self.tree.item(item, "tags")
        
        if not values or not tags:
            return None

        return {
            "item": item,
            "path": values[0],
            "tag": tags[0],
        }

    def _on_select(self, event):
        """处理树节点选中事件，显示相应信息"""
        selection_info = self.get_selection_info()
        if not selection_info:
            return

        # 根据节点类型显示不同信息
        if selection_info["tag"] == "group":
            # 显示分组概览信息
            group_name = selection_info["path"]
            self._show_group_info(group_name)
        elif selection_info["tag"] == "table":
            # 显示配置表详细信息
            table_path = Path(selection_info["path"]).resolve()
            self._show_table_info(table_path)

    def _on_double_click(self, event):
        """处理双击事件，打开选中的项目"""
        self.open_selected_item()

    def open_selected_item(self):
        """打开当前选中的项目进行Excel编辑"""
        selection_info = self.get_selection_info()
        if not selection_info:
            return

        # 根据选中项类型执行不同操作
        if selection_info["tag"] == "group":
            # 打开整个分组（包含多个配置表的Excel文件）
            group_name = selection_info["path"]
            threading.Thread(target=self._open_group_async,
                            args=(group_name,),
                            daemon=True).start()
        elif selection_info["tag"] == "table":
            # 打开单个配置表
            table_path = Path(selection_info["path"]).resolve()
            threading.Thread(target=self._open_table_async,
                            args=(table_path,),
                            daemon=True).start()

    def delete_selected_item(self):
        """删除当前选中的项目（分组或配置表）"""
        selection_info = self.get_selection_info()
        if not selection_info:
            return

        try:
            if selection_info["tag"] == "group":
                # 删除整个分组（所有配置表文件）
                group_name = selection_info["path"]
                table_files = utils.get_group_tables(group_name)

                confirm_msg = f"确定要删除分组 {group_name} 及其所有配置表（共{len(table_files)}个文件）吗？"
                if messagebox.askyesno("确认删除", confirm_msg):
                    for table_file in table_files:
                        table_file.unlink()
                    self.refresh()
                    self._update_status(f"已删除分组: {group_name}")
                    
            elif selection_info["tag"] == "table":
                # 删除单个配置表
                table_path = Path(selection_info["path"])

                confirm_msg = f"确定要删除配置表 {table_path.stem} 吗？"
                if messagebox.askyesno("确认删除", confirm_msg):
                    table_path.unlink()
                    self.refresh()
                    self._update_status(f"已删除: {table_path.stem}")
                    
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")

    def _show_context_menu(self, event):
        """显示右键上下文菜单"""
        # 获取点击位置的节点
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _open_table_async(self, table_path: Path):
        """异步打开单个配置表进行Excel编辑
        
        创建临时Excel文件并在系统默认程序中打开。
        同时启动文件监控线程进行实时同步。
        
        Args:
            table_path: 要打开的配置表文件路径
        """
        try:
            self._update_status(f"正在打开 {table_path.stem}...")

            # 创建临时Excel文件
            excel_path = utils.create_temp_excel(table_path)

            # 缓存打开的文件路径
            self.current_excel_files[str(table_path)] = excel_path

            # 在系统默认程序中打开Excel文件
            if sys.platform == "win32":
                os.startfile(excel_path)

            self._update_status(f"已打开 {table_path.stem}")

            # 显示配置表信息
            self._show_table_info(table_path)

            # 启动文件监控线程
            self._monitor_table_file(table_path, excel_path)

        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
            self._update_status("打开失败")

    def _open_group_async(self, group_name: str):
        """异步打开整个分组进行Excel编辑
        
        创建包含多个配置表的Excel文件并打开。
        同时启动文件监控线程进行实时同步。
        
        Args:
            table_name: 要打开的分组名称
        """
        try:
            self._update_status(f"正在打开分组 {group_name}...")

            # 创建包含所有配置表的Excel文件
            excel_path = utils.create_temp_excel_for_group(group_name)

            # 缓存打开的文件路径
            self.current_excel_files[f"table:{group_name}"] = excel_path

            # 在系统默认程序中打开Excel文件
            if sys.platform == "win32":
                os.startfile(excel_path)

            self._update_status(f"已打开分组 {group_name}")

            # 显示分组信息
            self._show_group_info(group_name)

            # 启动文件监控线程
            self._monitor_group_file(group_name, excel_path)

        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
            self._update_status("打开失败")

    def _monitor_table_file(self, table_path: Path, excel_path: Path):
        """监控Excel文件变化并自动同步到配置表文件
        
        在后台线程中运行，定期检查Excel文件的修改时间。
        当检测到文件被修改时，自动同步数据到配置表文件。
        
        Args:
            table_path: 目标配置表文件路径
            excel_path: 要监控的Excel文件路径
        """
        import time

        # 获取初始修改时间
        last_mtime = excel_path.stat().st_mtime if excel_path.exists() else 0

        # 持续监控直到文件被删除
        while excel_path.exists():
            time.sleep(2)  # 每2秒检查一次

            try:
                current_mtime = excel_path.stat().st_mtime
                if current_mtime > last_mtime:
                    # 文件已修改，同步数据到配置表
                    utils.sync_excel_to_yaml(excel_path, table_path)
                    last_mtime = current_mtime
                    self._update_status(f"已同步 {table_path.stem} 的修改")
            except ValueError as e:
                # 主键验证失败
                messagebox.showerror("数据验证失败", f"主键验证错误：\n{str(e)}\n\n请检查Excel中的数据并重新保存。")
                print(f"主键验证失败: {e}")
                break
            except Exception as e:
                messagebox.showerror("同步失败", f"数据同步失败：\n{str(e)}")
                print(f"监控文件时出错: {e}")
                break

    def _monitor_group_file(self, group_name: str, excel_path: Path):
        """监控分组Excel文件变化并同步到所有配置表文件
        
        监控包含多个配置表的Excel文件，当检测到修改时，
        同步所有工作表的数据到对应的配置表文件。
        
        Args:
            group_name: 分组名称
            excel_path: 要监控的Excel文件路径
        """
        import time

        # 获取初始修改时间
        last_mtime = excel_path.stat().st_mtime if excel_path.exists() else 0

        # 持续监控直到文件被删除
        while excel_path.exists():
            time.sleep(2)  # 每2秒检查一次

            try:
                current_mtime = excel_path.stat().st_mtime
                if current_mtime > last_mtime:
                    # 文件已修改，同步所有工作表到配置表
                    utils.sync_excel_to_all_yaml(excel_path, group_name)
                    last_mtime = current_mtime
                    self._update_status(f"已同步分组 {group_name} 的修改")
            except ValueError as e:
                # 主键验证失败
                messagebox.showerror("数据验证失败", f"主键验证错误：\n{str(e)}\n\n请检查Excel中的数据并重新保存。")
                print(f"主键验证失败: {e}")
                break
            except Exception as e:
                messagebox.showerror("同步失败", f"数据同步失败：\n{str(e)}")
                print(f"监控文件时出错: {e}")
                break

    def _show_table_info(self, table_path: Path):
        """显示配置表的详细信息
        
        加载并显示配置表的元数据信息，包括名称、所属分组、主键约束类型、
        数据行数、列数和列定义等。第一列标记为主键列。
        
        Args:
            table_path: 配置表文件路径
        """
        try:
            table = utils.load_table(table_path)

            key_type_display = {
                utils.KeyType.TABLE: "表级唯一",
                utils.KeyType.GROUP: "分组级唯一",
                utils.KeyType.GLOBAL: "全局唯一"
            }.get(table.key_type, "未知")

            info_lines = [
                f"配置表: {table.table_name}",
                f"所属分组: {table.group_name}",
                f"主键约束: {key_type_display}",
                f"文件路径: {table_path}",
                f"数据行数: {len(table.data)}",
                f"列数: {len(table.columns)}",
                "",
                "列定义:",
            ]

            # 添加每列的详细信息
            for col_idx, col in enumerate(table.columns):
                desc = f" - {col.description}" if col.description else ""
                pk_marker = " [主键列]" if col_idx == 0 else ""
                info_lines.append(f"  • {col.name} ({col.type}){pk_marker}{desc}")

            self._display_info("\n".join(info_lines))

        except Exception as e:
            self._display_info(f"加载配置表信息失败:\n{str(e)}")

    def _show_group_info(self, group_name: str):
        """显示分组的概览信息
        
        显示分组中所有配置表的统计信息，包括配置表数量、
        每个配置表的名称和数据规模等。
        
        Args:
            table_name: 分组名称
        """
        try:
            table_files = utils.get_group_tables(group_name)

            info_lines = [
                f"分组: {group_name}",
                f"配置表数量: {len(table_files)}",
                "",
                "配置表列表:",
            ]

            # 添加每个配置表的统计信息
            for table_file in table_files:
                try:
                    table = utils.load_table(table_file)
                    row_count = len(table.data)
                    col_count = len(table.columns)
                    info_lines.append(f"  - {table.table_name}: {row_count} 行 × {col_count} 列")
                except Exception as e:
                    info_lines.append(f"  - {table_file.stem}: 加载失败 ({str(e)})")

            self._display_info("\n".join(info_lines))

        except Exception as e:
            self._display_info(f"加载分组信息失败:\n{str(e)}")

    def _update_status(self, message: str):
        """更新状态栏显示信息
        
        Args:
            message: 要显示的状态信息
        """
        if self.on_status_update:
            self.on_status_update(message)

    def _display_info(self, info: str):
        """在信息面板中显示详细信息
        
        Args:
            info: 要显示的信息内容
        """
        if self.on_info_display:
            self.on_info_display(info)

    def _export_table(self, table_file: Path) -> bool:
        """将单个配置表导出到本地
        
        Args: 
            table_file: 要导出的配置表配置表文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            table = utils.load_table(table_file)
            binary_output_file = self.bin_export_dir / f"{table.table_name}.bytes"
            code_output_file = self.code_export_dir / f"{table.table_name}.cs"
            BinaryExporter.export_table(table, binary_output_file)
            CodeExporter.export_code_file(code_output_file, table)
            return True
        except Exception as e:
            print(f"导出 {table_file.stem} 失败: {e}")
            return False

    def _export_tables_batch(self, table_files: list, group_name: str = None) -> int:
        """批量导出多个配置表到本地
        
        Args:
            table_files: 要导出的配置表文件列表
            table_name: 分组名称（可选，用于状态显示）
            
        Returns:
            int: 成功导出的文件数量
        """
        success_count = 0
        for table_file in table_files:
            if self._export_table(table_file):
                success_count += 1
        
        if group_name:
            self._update_status(f"导出分组 {group_name} 完成: {success_count} / {len(table_files)} 个文件")
        
        return success_count

    def export_selected_table(self):
        """导出当前选中的配置表或分组到本地
        
        根据选中项的类型（单个配置表或整个分组）执行相应的导出操作。
        导出的二进制文件将保存在Data/Config/bin/下，C#文件保存在Scripts/Config/下。
        """
        selection_info = self.get_selection_info()
        if not selection_info:
            messagebox.showwarning("警告", "请先选择要导出的分组或配置表")
            return

        try:
            if selection_info["tag"] == "group":
                # 导出整个分组的所有配置表
                group_name = selection_info["path"]
                table_files = utils.get_group_tables(group_name)
                success_count = self._export_tables_batch(table_files, group_name)
                messagebox.showinfo("完成", f"成功导出 {success_count}/{len(table_files)} 个配置表")

            elif selection_info["tag"] == "table":
                # 导出单个配置表
                table_path = Path(selection_info["path"])
                if self._export_table(table_path):
                    table = utils.load_table(table_path)
                    output_file = self.bin_export_dir / f"{table.table_name}.bytes"
                    relative_path = output_file.relative_to(self.data_config_dir)
                    messagebox.showinfo("成功", f"已导出: {relative_path}")
                    self._update_status(f"导出完成: {output_file}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_all_tables(self):
        """导出所有配置表到本地
        
        扫描所有分组和配置表，批量导出到本地。
        显示详细的进度和统计信息。
        """
        try:
            tables = utils.get_all_tables()
            total_success = 0
            total_tables = 0

            # 逐个分组处理
            for table_name, table_files in tables.items():
                try:
                    success_count = self._export_tables_batch(table_files)
                    total_success += success_count
                    total_tables += len(table_files)
                except Exception as e:
                    print(f"导出分组 {table_name} 失败: {e}")

            # 显示最终统计结果
            result_msg = f"成功导出 {total_success}/{total_tables} 个配置表\n共 {len(tables)} 个分组"
            messagebox.showinfo("完成", result_msg)
            self._update_status(f"批量导出完成: {total_success} 个文件")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
