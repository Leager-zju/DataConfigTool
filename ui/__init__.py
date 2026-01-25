#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 界面模块

提供配置表编辑器的用户界面组件。

模块结构：
- file_tree: 文件树视图组件
- dialogs: 对话框组件
- main_window: 主应用程序窗口

公开接口：
- FileTreeFrame: 文件树视图类
- CreateTableDialog: 创建表对话框类
- ConfigEditorApp: 主应用程序类
"""

from .file_tree import FileTreeFrame
from .dialogs import CreateTableDialog
from .main_window import ConfigEditorApp

__all__ = [
    'FileTreeFrame',
    'CreateTableDialog',
    'ConfigEditorApp',
]
