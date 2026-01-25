#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二进制导出器
将配置数据导出为二进制格式，支持AES加密
"""

import struct
from pathlib import Path
from typing import Any, List, Dict
from utils import ConfigTable
from cryptography.fernet import Fernet

class BinaryExporter:
    """二进制导出器
    
    负责将配置表数据序列化为二进制格式，并支持AES加密。
    导出的文件格式：
    - 文件头：4字节 "SHET"
    - 数据长度：4字节无符号整数
    - 数据内容：加密后的序列化数据
    """
    
    # 默认加密密钥（生产环境应从安全配置中读取）
    DEFAULT_KEY = b'your-32-byte-secret-key-here!123'
    
    @staticmethod
    def generate_key() -> bytes:
        """生成新的32字节AES加密密钥
        
        Returns:
            bytes: 32字节的随机密钥
        """
        return Fernet.generate_key()
    
    @staticmethod
    def export_table(table: ConfigTable, output_path: Path, encrypt_key: bytes = DEFAULT_KEY):
        """导出单个配置表为二进制文件
        
        Args:
            table: 要导出的配置表对象
            output_path: 输出文件路径
            encrypt_key: AES加密密钥，必须为32字节
        
        Raises:
            Exception: 当文件写入失败时抛出异常
        """
        # 序列化配置表数据
        data_buffer = BinaryExporter._serialize_table(table)

        # 确保密钥长度为32字节
        if len(encrypt_key) != 32:
            key = encrypt_key.ljust(32, b'\0')[:32]
        else:
            key = encrypt_key

        # 使用AES-CBC加密数据
        encrypted_data = BinaryExporter._encrypt_aes_cbc(data_buffer, key)
        data_buffer = encrypted_data
            
        # 写入二进制文件
        with open(output_path, "wb") as f:
            f.write(b"SHET")  # 文件头标识
            f.write(struct.pack("<I", len(data_buffer)))  # 数据长度（小端序）
            f.write(data_buffer)  # 加密后的数据
    
    @staticmethod
    def _encrypt_aes_cbc(data: bytes, encryption_key: bytes) -> bytes:
        """使用AES-CBC模式加密数据
        
        Args:
            data: 要加密的原始数据
            encryption_key: 32字节的AES密钥
            
        Returns:
            bytes: IV + 加密后的数据（IV在前16字节）
        """
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend
        import os

        # 生成16字节随机初始化向量
        iv = os.urandom(16)

        # 创建AES-CBC加密器
        cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # 使用PKCS7填充数据到128位边界
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        # 执行加密
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # 返回IV + 加密数据
        return iv + encrypted
    
    @staticmethod
    def _serialize_table(table: ConfigTable) -> bytes:
        """将配置表序列化为字节流
        
        序列化格式：
        1. 数据行数（4字节无符号整数）
        2. 每行数据（按列顺序存储值）
        
        Args:
            table: 要序列化的配置表
            
        Returns:
            bytes: 序列化后的字节数据
        """
        import io
        
        buffer = io.BytesIO()
        buffer.write(struct.pack("<I", len(table.data)))
        for row in table.data:
            for col in table.columns:
                value = row.get(col.name)
                BinaryExporter._write_value(buffer, value, col.type)
        
        return buffer.getvalue()

    @staticmethod
    def _write_value(buffer, value: Any, value_type: str):
        """将值写入缓冲区
        
        格式：1字节标志位 + 值数据
        - 标志位：0表示null值，1表示有效值
        
        Args:
            buffer: 字节缓冲区
            value: 要写入的值
            value_type: 值的类型字符串
        """
        # 写入null标志
        if value is None:
            buffer.write(struct.pack("<B", 0))  # null标志
            return

        buffer.write(struct.pack("<B", 1))  # 有效值标志

        # 根据类型写入具体数据
        if value_type == "int":
            buffer.write(struct.pack("<i", int(value)))  # 4字节有符号整数
        elif value_type == "float":
            buffer.write(struct.pack("<f", float(value)))  # 4字节浮点数
        elif value_type == "string":
            BinaryExporter._write_string(buffer, str(value))
        elif value_type == "bool":
            buffer.write(struct.pack("<B", 1 if value else 0))  # 1字节布尔值
        elif value_type.startswith("List"):
            BinaryExporter._write_list(buffer, value, value_type[4:-1])
        elif value_type.startswith("Dictionary"):
            BinaryExporter._write_dict(buffer, value, value_type[11:-1].split(","))
        else:
            # 未知类型转为字符串处理
            BinaryExporter._write_string(buffer, str(value))

    @staticmethod
    def _write_string(buffer, s: str):
        """将字符串写入缓冲区
        
        格式：4字节长度 + UTF-8编码的字符串数据
        
        Args:
            buffer: 字节缓冲区
            s: 要写入的字符串
        """
        encoded = s.encode("utf-8")
        buffer.write(struct.pack("<I", len(encoded)))  # 字符串长度（小端序）
        buffer.write(encoded)  # UTF-8编码的字符串数据

    @staticmethod
    def _write_list(buffer, lst: List, value_type: str):
        """将列表写入缓冲区
        
        格式：4字节长度 + 每个元素的数据

        Args:
            buffer: 字节缓冲区
            lst: 要写入的列表
            value_type: 元素的类型字符串
        """
        buffer.write(struct.pack("<I", len(lst)))
        for item in lst:
            BinaryExporter._write_value(buffer, item, value_type)

    @staticmethod
    def _write_dict(buffer, d: Dict, kv_type: List[str]):
        """将字典写入缓冲区
        
        格式：4字节长度 + 每个键值对的数据
        
        Args:
            buffer: 字节缓冲区
            d: 要写入的字典
            kv_type: 键和值的类型字符串
        """
        key_type = kv_type[0]
        value_type = kv_type[1]
        buffer.write(struct.pack("<I", len(d)))
        for key, value in d.items():
            BinaryExporter._write_value(buffer, key, key_type)
            BinaryExporter._write_value(buffer, value, value_type)
