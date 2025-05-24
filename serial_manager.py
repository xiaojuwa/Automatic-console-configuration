"""
串口通信管理模块
"""
import serial
import serial.tools.list_ports
import time
import threading
from typing import List, Optional, Callable
import re

class SerialManager:
    """串口管理类"""
    
    def __init__(self, config):
        self.config = config
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.read_thread: Optional[threading.Thread] = None
        self.stop_reading = False
        self.data_callback: Optional[Callable] = None
        
    def get_available_ports(self) -> List[str]:
        """获取可用的COM端口列表"""
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except Exception as e:
            print(f"获取COM端口失败: {e}")
            return []
    
    def detect_baudrate(self, port: str, baudrates: List[int] = None) -> Optional[int]:
        """自动检测波特率"""
        if baudrates is None:
            baudrates = self.config.get("baudrates", [9600, 19200, 38400, 57600, 115200])
        
        timeout = self.config.get("timeout", 3)
        common_prompts = self.config.get("common_prompts", [">", "#", "]", "$", "%"])
        
        for baudrate in baudrates:
            try:
                # 尝试连接
                test_serial = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=1,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                
                time.sleep(0.5)  # 等待连接稳定
                
                # 清空缓冲区
                test_serial.flushInput()
                test_serial.flushOutput()
                
                # 发送回车尝试获取提示符
                test_serial.write(b'\r\n')
                time.sleep(1)
                
                # 读取响应
                response = ""
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if test_serial.in_waiting > 0:
                        data = test_serial.read(test_serial.in_waiting)
                        try:
                            response += data.decode('utf-8', errors='ignore')
                        except:
                            response += data.decode('gbk', errors='ignore')
                    time.sleep(0.1)
                
                test_serial.close()
                
                # 检查响应是否包含常见提示符
                if response.strip():
                    for prompt in common_prompts:
                        if prompt in response:
                            return baudrate
                    
                    # 检查是否包含可读文本（非乱码）
                    if self._is_readable_text(response):
                        return baudrate
                        
            except Exception as e:
                print(f"测试波特率 {baudrate} 失败: {e}")
                continue
        
        return None
    
    def _is_readable_text(self, text: str) -> bool:
        """检查文本是否可读（非乱码）"""
        if not text.strip():
            return False
        
        # 计算可打印字符的比例
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        ratio = printable_chars / len(text)
        
        # 如果可打印字符比例大于80%，认为是可读文本
        return ratio > 0.8
    
    def connect(self, port: str, baudrate: int) -> bool:
        """连接到指定端口和波特率"""
        try:
            if self.is_connected:
                self.disconnect()
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            self.is_connected = True
            self.stop_reading = False
            
            # 启动读取线程
            self.read_thread = threading.Thread(target=self._read_data, daemon=True)
            self.read_thread.start()
            
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.stop_reading = True
        self.is_connected = False
        
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        
        self.serial_connection = None
    
    def send_command(self, command: str) -> bool:
        """发送命令"""
        if not self.is_connected or not self.serial_connection:
            return False
        
        try:
            # 确保命令以换行符结尾
            if not command.endswith('\n') and not command.endswith('\r\n'):
                command += '\r\n'
            
            self.serial_connection.write(command.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"发送命令失败: {e}")
            return False
    
    def _read_data(self):
        """读取数据的线程函数"""
        buffer = ""
        
        while not self.stop_reading and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    
                    # 尝试不同的编码
                    try:
                        text = data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text = data.decode('gbk')
                        except UnicodeDecodeError:
                            text = data.decode('utf-8', errors='ignore')
                    
                    buffer += text
                    
                    # 如果有回调函数，调用它
                    if self.data_callback:
                        self.data_callback(text)
                
                time.sleep(0.01)  # 避免过度占用CPU
                
            except Exception as e:
                print(f"读取数据错误: {e}")
                break
    
    def set_data_callback(self, callback: Callable):
        """设置数据接收回调函数"""
        self.data_callback = callback
