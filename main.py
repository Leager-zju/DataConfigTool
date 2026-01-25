#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置表可视化编辑工具

主要功能：
- 支持YAML数据存储和加载
- 提供Excel临时编辑功能
- 支持二进制格式与C#文件导出
- 文件树形视图管理
- 实时文件监控和同步

使用说明：
1. 双击文件树中的项目可以在Excel中打开编辑
2. 修改Excel文件后会自动同步到YAML配置表文件
3. 可以导出单个或所有配置表为二进制格式与C#文件

模块结构：
- ui.file_tree: 文件树视图组件
- ui.dialogs: 对话框组件
- ui.main_window: 主应用程序窗口
- main: 程序入口点
"""

import sys
import tkinter as tk
from tkinter import messagebox

from ui import ConfigEditorApp

def main():
    """主函数 - 程序入口点
    
    初始化Tkinter应用程序并启动主事件循环。
    设置窗口图标和基本属性。
    """
    try:
        # 创建主窗口
        root = tk.Tk()
        
        # 创建主应用程序
        app = ConfigEditorApp(root)
        
        # 设置窗口关闭事件
        def on_closing():
            if messagebox.askokcancel("退出", "确定要退出程序吗？"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 启动主事件循环
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("程序错误", f"程序启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
