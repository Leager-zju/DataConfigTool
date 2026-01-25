#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口应用程序模块

提供配置表编辑器的主应用程序窗口。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from pathlib import Path

import utils
from utils.setting_data import SettingData, PathKey
from .file_tree import FileTreeFrame
from .dialogs import CreateTableDialog


class ConfigEditorApp:
    """配置表编辑器主应用程序
    
    主窗口应用程序，集成了文件树视图、信息面板、菜单栏和状态栏。
    提供完整的配置表管理功能，包括创建、编辑、导出等。
    
    界面布局：
    - 左侧：文件树视图
    - 右侧：信息显示面板
    - 顶部：菜单栏
    - 底部：状态栏
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("配置表编辑器 v1.0")
        self.root.resizable(True, True)  # 允许窗口大小调整
        self.root.geometry("900x650")  # 设置默认窗口大小

        # 初始化UI组件
        self._create_main_layout()
        self._create_menu()
        self._create_status_bar()
        
        # 初始化数据
        self._initialize_data()

    def _create_menu(self):
        """创建主窗口菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建配置表", command=self.create_new_config, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="刷新", command=self.file_tree_frame.refresh, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")

        # 导出菜单
        export_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="导出", menu=export_menu)
        export_menu.add_command(label="导出选中到本地", command=self.file_tree_frame.export_selected_table)
        export_menu.add_command(label="导出全部到本地", command=self.file_tree_frame.export_all_tables)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="清理临时文件", command=self.clean_temp_files)
        tools_menu.add_command(label="打开配置目录", command=self.open_config_directory)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self.show_about)

    def _create_main_layout(self):
        """创建主界面布局"""
        # 主容器（水平分割窗口）
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧文件树面板
        self.file_tree_frame = FileTreeFrame(self.main_container)
        
        # 右侧信息显示面板
        self.detail_frame = ttk.Frame(self.main_container)
        self._create_info_panel()

        # 添加到分割窗口（设置权重）
        self.main_container.add(self.file_tree_frame, weight=1)
        self.main_container.add(self.detail_frame, weight=2)

    def _create_info_panel(self):
        """创建信息显示面板"""
        # 信息面板标题
        info_label = ttk.Label(self.detail_frame, text="配置信息", font=("Arial", 10, "bold"))
        info_label.pack(pady=5)

        # 信息文本显示区域
        info_frame = ttk.Frame(self.detail_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        # 文本显示组件（只读）
        self.info_text = tk.Text(info_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                font=("Consolas", 9), bg="#f8f8f8")
        
        # 添加滚动条
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)

        # 布局组件
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_status_bar(self):
        """创建底部状态栏"""
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _initialize_data(self):
        """初始化数据和回调"""
        # 设置文件树的回调函数
        self.file_tree_frame.set_callbacks(
            on_status_update=self.update_status,
            on_info_display=self.display_info
        )

        # 初始加载数据
        self.file_tree_frame.refresh()

    def display_info(self, info: str):
        """在信息面板中显示详细信息
        
        Args:
            info: 要显示的信息内容
        """
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)

    def update_status(self, message: str):
        """更新底部状态栏显示
        
        Args:
            message: 要显示的状态信息
        """
        self.status_bar.config(text=message)
        self.root.update_idletasks()  # 立即更新界面

    def create_new_config(self):
        """创建新的配置表
        
        打开创建对话框，允许用户输入新配置表的信息。
        创建成功后自动刷新文件树显示。
        """
        dialog = CreateTableDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self.file_tree_frame.refresh()
            self.update_status(f"已创建配置表: {dialog.result}")

    def clean_temp_files(self):
        """清理临时Excel文件
        
        删除.cache目录中的所有临时Excel文件。
        """
        try:
            from utils import get_config_dir
            import shutil
            
            temp_dir = get_config_dir() / ".cache"
            if temp_dir.exists():
                file_count = len(list(temp_dir.glob("*.xlsx")))
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(exist_ok=True)
                
                messagebox.showinfo("成功", f"已清理 {file_count} 个临时文件")
                self.update_status("临时文件清理完成")
            else:
                messagebox.showinfo("信息", "没有找到临时文件")
                
        except Exception as e:
            messagebox.showerror("错误", f"清理失败: {str(e)}")

    def open_config_directory(self):
        """在文件管理器中打开配置目录"""
        try:
            config_dir = SettingData.get_instance().get_path(PathKey.DATA_CONFIG_DIR)
            if sys.platform == "win32":
                os.startfile(config_dir)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{config_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{config_dir}'")
        except Exception as e:
            messagebox.showerror("错误", f"打开目录失败: {str(e)}")

    def show_help(self):
        """显示使用说明对话框"""
        help_text = """
配置表编辑器使用说明

基本操作：
1. 双击文件树中的项目可以在Excel中打开编辑
2. 修改Excel文件后会自动同步到配置表文件
3. 右键点击可以显示上下文菜单

支持的数据类型：
- int: 整数
- float: 浮点数
- string: 字符串
- bool: 布尔值
- list: 列表（JSON格式）
- dict: 字典（JSON格式）

文件结构：
- 配置目录/分组名/配置表名.yaml
- 导出目录: 配置目录/bin/配置表名.bytes

注意事项：
- Excel文件为临时文件，关闭后会自动删除
- 修改后请等待同步完成再关闭Excel
        """
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x400")
        help_window.transient(self.root)
        
        # 添加文本显示
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # 添加关闭按钮
        ttk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=10)

    def show_about(self):
        """显示关于对话框"""
        about_text = (
            "配置表编辑器 v1.0\n\n"
            "主要功能：\n"
            "• 配置表数据存储和加载\n"
            "• Excel临时编辑功能\n"
            "• 二进制格式与C#文件导出\n"
            "• 强类型数据支持\n"
            "• 实时文件监控和同步\n\n"
            "技术特性：\n"
            "• 基于Python + Tkinter开发\n"
            "• 支持AES加密导出\n"
            "• 多线程文件监控\n\n"
            "© 2026"
        )
        messagebox.showinfo("关于", about_text)
