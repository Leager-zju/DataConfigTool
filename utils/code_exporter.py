import os
from pathlib import Path
import stat
from utils import ConfigTable
from .setting_data import MetaDataKey, SettingData

class CodeExporter:

    @staticmethod
    def export_code_file(file_path : Path, table: ConfigTable):
        if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
            try:
                os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IWUSR)
            except Exception as e:
                print(f"修改权限失败: {e}")
                return

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                f"""
using System.Collections.Generic;
using System.IO;

namespace {SettingData.get_instance().get_metadata(MetaDataKey.PROJECT_NAME)}.Config
{{
    {CodeExporter._makeConfigData(table)}

    public class {table.table_name} : IConfig
    {{
        private readonly Dictionary<int, {table.table_name}_DATA> _datas = [];

        public string FileName {{ get => "{SettingData.get_instance().get_metadata(MetaDataKey.VIRTUAL_DATA_CONFIG_ROOT)}/{table.table_name}/{table.table_name}.yaml"; set => throw new System.InvalidOperationException(); }}

        public void LoadFromFile() => BinaryConfigReader.ReadEncryptedFile(FileName, ParseData);
        public {table.table_name}_DATA GetData(int id) => _datas[id];
        public Dictionary<int, {table.table_name}_DATA> GetAllDatas() => _datas;

        private void ParseData(BinaryReader reader)
        {{
            uint rowCount = reader.ReadUInt32();
            for (int i = 0; i < rowCount; i++)
            {{
                var id = (int)BinaryConfigReader.ReadValue(reader, ValueType.INT);
                var rowData = new {table.table_name}_DATA
                {{
{CodeExporter._makeDataParse(table)}
                }};

                _datas.Add(id, rowData);
            }}
        }}
    }}
}}
                """
            )

        os.chmod(file_path, stat.S_IREAD)
    
    @staticmethod
    def _makeConfigData(table: ConfigTable):
        s = f"public struct {table.table_name}_DATA\n    {{\n"
        for col in table.columns:
            s += f"        public {col.type} {col.name};\n"
        s += "    }"
        return s

    @staticmethod
    def _makeDataParse(table: ConfigTable):
        s = ""
        for col in table.columns:
            if col.type == "string":
                s += f"                    {col.name} = BinaryConfigReader.ReadString(reader),\n"
            elif col.type == "int":
                s += f"                    {col.name} = (int)BinaryConfigReader.ReadValue(reader, ValueType.INT),\n"
            elif col.type == "float":
                s += f"                    {col.name} = (float)BinaryConfigReader.ReadValue(reader, ValueType.FLOAT),\n"
            elif col.type == "bool":
                s += f"                    {col.name} = (bool)BinaryConfigReader.ReadValue(reader, ValueType.BOOL),\n"
            elif col.type.startswith("List"):
                s += f"                    {col.name} = BinaryConfigReader.ReadValue(reader, ValueType.LIST) as {col.type},\n"
            elif col.type.startswith("Dictionary"):
                s += f"                    {col.name} = BinaryConfigReader.ReadValue(reader, ValueType.DICT) as {col.type},\n"
            else:
                s += f"                    {col.name} = BinaryConfigReader.ReadString(reader),\n"
        return s