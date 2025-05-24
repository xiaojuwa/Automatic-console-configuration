"""
命令管理模块
"""
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class CommandManager:
    """命令管理类"""
    
    def __init__(self, config, serial_manager):
        self.config = config
        self.serial_manager = serial_manager
        self.commands_dir = config.get("commands_directory", "commands")
        self.ensure_commands_directory()
        
    def ensure_commands_directory(self):
        """确保命令目录存在"""
        if not os.path.exists(self.commands_dir):
            os.makedirs(self.commands_dir, exist_ok=True)
    
    def get_command_files(self) -> List[str]:
        """获取所有命令文件列表"""
        try:
            files = []
            for file in os.listdir(self.commands_dir):
                if file.endswith('.json'):
                    files.append(file[:-5])  # 移除.json扩展名
            return sorted(files)
        except Exception as e:
            print(f"获取命令文件列表失败: {e}")
            return []
    
    def load_command_sequence(self, name: str) -> Optional[Dict[str, Any]]:
        """加载命令序列"""
        file_path = os.path.join(self.commands_dir, f"{name}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载命令序列失败: {e}")
            return None
    
    def save_command_sequence(self, name: str, sequence: Dict[str, Any]) -> bool:
        """保存命令序列"""
        file_path = os.path.join(self.commands_dir, f"{name}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sequence, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存命令序列失败: {e}")
            return False
    
    def delete_command_sequence(self, name: str) -> bool:
        """删除命令序列"""
        file_path = os.path.join(self.commands_dir, f"{name}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除命令序列失败: {e}")
            return False
    
    def create_default_sequences(self):
        """创建默认命令序列"""
        default_sequences = {
            "基本信息查询": {
                "description": "查询设备基本信息",
                "commands": [
                    {"command": "display version", "delay": 2, "description": "显示版本信息"},
                    {"command": "display device", "delay": 2, "description": "显示设备信息"},
                    {"command": "display interface brief", "delay": 2, "description": "显示接口简要信息"}
                ],
                "vendor": "通用"
            },
            "华为基本配置": {
                "description": "华为设备基本配置查询",
                "commands": [
                    {"command": "display version", "delay": 2, "description": "显示版本"},
                    {"command": "display current-configuration", "delay": 3, "description": "显示当前配置"},
                    {"command": "display interface brief", "delay": 2, "description": "显示接口状态"},
                    {"command": "display ip routing-table", "delay": 2, "description": "显示路由表"}
                ],
                "vendor": "Huawei"
            },
            "中兴基本配置": {
                "description": "中兴设备基本配置查询",
                "commands": [
                    {"command": "show version", "delay": 2, "description": "显示版本"},
                    {"command": "show running-config", "delay": 3, "description": "显示运行配置"},
                    {"command": "show interface status", "delay": 2, "description": "显示接口状态"},
                    {"command": "show ip route", "delay": 2, "description": "显示路由表"}
                ],
                "vendor": "ZTE"
            },
            "华三基本配置": {
                "description": "华三设备基本配置查询",
                "commands": [
                    {"command": "display version", "delay": 2, "description": "显示版本"},
                    {"command": "display current-configuration", "delay": 3, "description": "显示当前配置"},
                    {"command": "display interface brief", "delay": 2, "description": "显示接口状态"},
                    {"command": "display ip routing-table", "delay": 2, "description": "显示路由表"}
                ],
                "vendor": "H3C"
            }
        }
        
        # 保存默认序列
        for name, sequence in default_sequences.items():
            if not os.path.exists(os.path.join(self.commands_dir, f"{name}.json")):
                self.save_command_sequence(name, sequence)
    
    def execute_command_sequence(self, sequence_name: str, progress_callback=None, output_callback=None) -> bool:
        """执行命令序列"""
        sequence = self.load_command_sequence(sequence_name)
        if not sequence:
            return False
        
        if not self.serial_manager.is_connected:
            if output_callback:
                output_callback("错误: 设备未连接\n")
            return False
        
        commands = sequence.get("commands", [])
        total_commands = len(commands)
        
        if output_callback:
            output_callback(f"开始执行命令序列: {sequence_name}\n")
            output_callback(f"描述: {sequence.get('description', '无描述')}\n")
            output_callback(f"总共 {total_commands} 个命令\n")
            output_callback("-" * 50 + "\n")
        
        # 设置输出回调
        response_buffer = []
        
        def collect_output(data):
            response_buffer.append(data)
            if output_callback:
                output_callback(data)
        
        original_callback = self.serial_manager.data_callback
        self.serial_manager.set_data_callback(collect_output)
        
        try:
            for i, cmd_info in enumerate(commands, 1):
                command = cmd_info.get("command", "")
                delay = cmd_info.get("delay", 1)
                description = cmd_info.get("description", "")
                
                if output_callback:
                    output_callback(f"\n[{i}/{total_commands}] 执行命令: {command}\n")
                    if description:
                        output_callback(f"描述: {description}\n")
                
                # 更新进度
                if progress_callback:
                    progress = int((i - 1) / total_commands * 100)
                    progress_callback(progress)
                
                # 发送命令
                if self.serial_manager.send_command(command):
                    # 等待响应
                    time.sleep(delay)
                else:
                    if output_callback:
                        output_callback(f"错误: 发送命令失败 - {command}\n")
                    return False
            
            # 最终进度
            if progress_callback:
                progress_callback(100)
            
            if output_callback:
                output_callback(f"\n命令序列执行完成: {sequence_name}\n")
                output_callback("=" * 50 + "\n")
            
            return True
            
        except Exception as e:
            if output_callback:
                output_callback(f"执行命令序列时发生错误: {e}\n")
            return False
        finally:
            # 恢复原始回调
            self.serial_manager.set_data_callback(original_callback)
    
    def validate_command_sequence(self, sequence: Dict[str, Any]) -> List[str]:
        """验证命令序列格式"""
        errors = []
        
        if "commands" not in sequence:
            errors.append("缺少 'commands' 字段")
            return errors
        
        commands = sequence["commands"]
        if not isinstance(commands, list):
            errors.append("'commands' 必须是列表")
            return errors
        
        for i, cmd in enumerate(commands):
            if not isinstance(cmd, dict):
                errors.append(f"命令 {i+1}: 必须是字典格式")
                continue
            
            if "command" not in cmd:
                errors.append(f"命令 {i+1}: 缺少 'command' 字段")
            
            if "delay" in cmd and not isinstance(cmd["delay"], (int, float)):
                errors.append(f"命令 {i+1}: 'delay' 必须是数字")
        
        return errors
