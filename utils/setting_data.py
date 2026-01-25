from configparser import ConfigParser
from pathlib import Path
from enum import Enum

class MetaDataKey(str, Enum):
    PROJECT_NAME = "PROJECT_NAME"
    VIRTUAL_DATA_CONFIG_ROOT = "VIRTUAL_DATA_CONFIG_ROOT"

class PathKey(str, Enum):
    DATA_CONFIG_DIR = "DATA_CONFIG_DIR"
    CODE_EXPORT_DIR = "CODE_EXPORT_DIR"

class SettingData(ConfigParser):
    """数据配置解析器"""

    _instance = None

    def __init__(self, setting):
        super().__init__()
        self.cwd = Path(__file__).parent.parent.absolute()
        setting_path = Path(setting)
        if not setting_path.exists() or not setting_path.is_file():
            setting_path = self.cwd / "setting.ini"
        self.read(setting_path)

    @staticmethod
    def get_instance():
        if SettingData._instance is None:
            SettingData._instance = SettingData("./setting.ini")
        return SettingData._instance
    
    def get_metadata(self, option: str) -> str:
        """获取元数据"""
        if self.has_option("METADATA", option) is False:
            return None
        
        return self['METADATA'][option]

    def get_path(self, option: str) -> Path:
        """获取绝对路径"""
        if self.has_option("PATH", option) is False:
            return None

        path_value = Path(self['PATH'][option])
        return self.cwd / path_value

if __name__ == "__main__":
    # ONLY FOR TEST
    item_config_dir = SettingData.get_instance().get_path(PathKey.DATA_CONFIG_DIR)
    print(item_config_dir, item_config_dir.exists())