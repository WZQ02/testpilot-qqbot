import json
import os
import logging
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, file_path, default_key=None):
        self.file_path = file_path
        self.default_key = default_key
        self.data = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.file_path):
            logger.warning(f"未找到配置文件: {self.file_path}。 返回空目录。")
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if self.default_key and self.default_key in data:
                    return data[self.default_key]
                return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析出错 {self.file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"配置文件加载出错 {self.file_path}: {e}")
            return {}

    def _write_config(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                if self.default_key:
                    json.dump({self.default_key: self.data}, f, ensure_ascii=False, indent=4)
                else:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"配置文件写入出错 {self.file_path}: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self._write_config()

    def update(self, new_data):
        # self.data.update(new_data)
        self.data = new_data
        self._write_config()

    def all(self):
        return self.data

    def reload(self):
        self.data = self._load_config()
