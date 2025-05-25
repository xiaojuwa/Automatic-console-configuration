"""
配置文件管理模块
"""
import json
import os
from typing import Dict, List, Any

class Config:
    """配置管理类"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "baudrates": [9600, 19200, 38400, 57600, 115200],
            "timeout": 3,
            "device_patterns": {
                "ZTE": ["ZTE", "ZXR", "ZXUN"],
                "Huawei": ["Huawei", "VRP", "HUAWEI"],
                "H3C": ["H3C", "Comware", "HP"]
            },
            "common_prompts": [">", "#", "]", "$", "%"],
            "identification_commands": [
                "display version",
                "show version",
                "show system",
                "display device"
            ],
            "log_directory": "logs",
            "commands_directory": "commands",
            "auto_login": {
                "enabled": False,
                "username": "",
                "password": "",
                "enable_password": "",
                "timeout": 30,
                "prompts": {
                    "username": ["Username:", "login:", "User:", "用户名:"],
                    "password": ["Password:", "password:", "密码:"],
                    "enable": [">"],
                    "enable_password": ["Password:", "password:", "密码:"],
                    "success": ["#", "]"],
                    "more": ["More", "--More--", "---- More ----", "Press any key to continue"]
                },
                "responses": {
                    "more": " "
                }
            },
            "terminal": {
                "local_echo": False,
                "line_ending": "\r\n",
                "font_family": "Consolas",
                "font_size": 10,
                "bg_color": "black",
                "fg_color": "green",
                "cursor_color": "green",
                "buffer_size": 10000,
                "auto_scroll": True
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value

    def ensure_directories(self):
        """确保必要的目录存在"""
        for dir_key in ["log_directory", "commands_directory"]:
            directory = self.get(dir_key)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
