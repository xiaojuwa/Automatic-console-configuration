"""
设备识别模块
"""
import re
import time
from typing import Dict, Optional, List

class DeviceDetector:
    """设备检测类"""
    
    def __init__(self, config, serial_manager):
        self.config = config
        self.serial_manager = serial_manager
        self.device_info = {
            "vendor": "未知",
            "model": "未知",
            "version": "未知",
            "hostname": "未知"
        }
        
    def detect_device(self) -> Dict[str, str]:
        """检测设备信息"""
        if not self.serial_manager.is_connected:
            return self.device_info
        
        # 获取识别命令列表
        identification_commands = self.config.get("identification_commands", [
            "display version",
            "show version", 
            "show system",
            "display device"
        ])
        
        # 尝试每个识别命令
        for command in identification_commands:
            response = self._execute_identification_command(command)
            if response:
                device_info = self._parse_device_info(response)
                if device_info["vendor"] != "未知":
                    self.device_info = device_info
                    break
        
        return self.device_info
    
    def _execute_identification_command(self, command: str) -> Optional[str]:
        """执行识别命令并获取响应"""
        try:
            # 清空之前的数据
            response_buffer = []
            
            def collect_response(data):
                response_buffer.append(data)
            
            # 设置临时回调
            original_callback = self.serial_manager.data_callback
            self.serial_manager.set_data_callback(collect_response)
            
            # 发送命令
            if self.serial_manager.send_command(command):
                # 等待响应
                time.sleep(3)
                
                # 恢复原始回调
                self.serial_manager.set_data_callback(original_callback)
                
                # 合并响应
                response = ''.join(response_buffer)
                return response if response.strip() else None
            
        except Exception as e:
            print(f"执行识别命令失败: {e}")
        
        return None
    
    def _parse_device_info(self, response: str) -> Dict[str, str]:
        """解析设备信息"""
        device_info = {
            "vendor": "未知",
            "model": "未知", 
            "version": "未知",
            "hostname": "未知"
        }
        
        # 获取设备模式匹配规则
        device_patterns = self.config.get("device_patterns", {})
        
        # 检测厂商
        for vendor, patterns in device_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    device_info["vendor"] = vendor
                    break
            if device_info["vendor"] != "未知":
                break
        
        # 根据厂商解析具体信息
        if device_info["vendor"] == "ZTE":
            device_info.update(self._parse_zte_info(response))
        elif device_info["vendor"] == "Huawei":
            device_info.update(self._parse_huawei_info(response))
        elif device_info["vendor"] == "H3C":
            device_info.update(self._parse_h3c_info(response))
        else:
            # 通用解析
            device_info.update(self._parse_generic_info(response))
        
        return device_info
    
    def _parse_zte_info(self, response: str) -> Dict[str, str]:
        """解析中兴设备信息"""
        info = {}
        
        # 解析型号
        model_patterns = [
            r'Product\s+Name\s*:\s*(.+)',
            r'Device\s+Type\s*:\s*(.+)',
            r'ZXR\s+(\S+)',
            r'ZXUN\s+(\S+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["model"] = match.group(1).strip()
                break
        
        # 解析版本
        version_patterns = [
            r'Software\s+Version\s*:\s*(.+)',
            r'Version\s*:\s*(.+)',
            r'ZTE\s+(\S+)\s+Version'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["version"] = match.group(1).strip()
                break
        
        # 解析主机名
        hostname_patterns = [
            r'System\s+Name\s*:\s*(.+)',
            r'Host\s+Name\s*:\s*(.+)',
            r'<(.+)>'
        ]
        
        for pattern in hostname_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["hostname"] = match.group(1).strip()
                break
        
        return info
    
    def _parse_huawei_info(self, response: str) -> Dict[str, str]:
        """解析华为设备信息"""
        info = {}
        
        # 解析型号
        model_patterns = [
            r'HUAWEI\s+(\S+)',
            r'Product\s+Name\s*:\s*(.+)',
            r'Device\s+name\s*:\s*(.+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["model"] = match.group(1).strip()
                break
        
        # 解析版本
        version_patterns = [
            r'VRP\s+\(R\)\s+software,\s+Version\s+(.+)',
            r'Software\s+Version\s+(.+)',
            r'Version\s+(.+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["version"] = match.group(1).strip()
                break
        
        # 解析主机名
        hostname_patterns = [
            r'<(.+)>',
            r'System\s+Name\s*:\s*(.+)'
        ]
        
        for pattern in hostname_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["hostname"] = match.group(1).strip()
                break
        
        return info
    
    def _parse_h3c_info(self, response: str) -> Dict[str, str]:
        """解析华三设备信息"""
        info = {}
        
        # 解析型号
        model_patterns = [
            r'H3C\s+(\S+)',
            r'Product\s+name\s*:\s*(.+)',
            r'Device\s+name\s*:\s*(.+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["model"] = match.group(1).strip()
                break
        
        # 解析版本
        version_patterns = [
            r'Comware\s+Software,\s+Version\s+(.+)',
            r'Software\s+version\s+(.+)',
            r'Version\s+(.+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["version"] = match.group(1).strip()
                break
        
        # 解析主机名
        hostname_patterns = [
            r'<(.+)>',
            r'\[(.+)\]',
            r'System\s+name\s*:\s*(.+)'
        ]
        
        for pattern in hostname_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["hostname"] = match.group(1).strip()
                break
        
        return info
    
    def _parse_generic_info(self, response: str) -> Dict[str, str]:
        """通用设备信息解析"""
        info = {}
        
        # 通用型号解析
        model_patterns = [
            r'Model\s*:\s*(.+)',
            r'Product\s*:\s*(.+)',
            r'Device\s*:\s*(.+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["model"] = match.group(1).strip()
                break
        
        # 通用版本解析
        version_patterns = [
            r'Version\s*:\s*(.+)',
            r'Software\s*:\s*(.+)',
            r'Firmware\s*:\s*(.+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                info["version"] = match.group(1).strip()
                break
        
        return info
