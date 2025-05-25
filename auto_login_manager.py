"""
自动登录管理模块
"""
import time
import threading
import queue
from typing import Dict, List, Optional, Callable
import re


class AutoLoginManager:
    """自动登录管理类"""
    
    def __init__(self, config, serial_manager):
        self.config = config
        self.serial_manager = serial_manager
        self.login_config = config.get("auto_login", {})
        
        # 登录状态
        self.is_logging_in = False
        self.login_success = False
        self.login_error = None
        
        # 数据缓冲区
        self.data_buffer = ""
        self.response_queue = queue.Queue()
        
        # 回调函数
        self.status_callback: Optional[Callable] = None
        self.output_callback: Optional[Callable] = None
        
        # 登录超时
        self.login_timeout = self.login_config.get("timeout", 30)
        
    def set_callbacks(self, status_callback: Callable = None, output_callback: Callable = None):
        """设置回调函数"""
        self.status_callback = status_callback
        self.output_callback = output_callback
        
    def is_enabled(self) -> bool:
        """检查自动登录是否启用"""
        return self.login_config.get("enabled", False)
        
    def update_login_config(self, username: str, password: str, enable_password: str = "", enabled: bool = True):
        """更新登录配置"""
        self.login_config.update({
            "enabled": enabled,
            "username": username,
            "password": password,
            "enable_password": enable_password
        })
        
        # 更新到主配置
        auto_login_config = self.config.get("auto_login", {})
        auto_login_config.update(self.login_config)
        self.config.set("auto_login", auto_login_config)
        self.config.save_config()
        
    def start_auto_login(self) -> bool:
        """开始自动登录过程"""
        if not self.is_enabled():
            if self.status_callback:
                self.status_callback("自动登录未启用")
            return False
            
        if not self.serial_manager.is_connected:
            if self.status_callback:
                self.status_callback("设备未连接")
            return False
            
        if self.is_logging_in:
            if self.status_callback:
                self.status_callback("正在登录中...")
            return False
            
        # 重置状态
        self.is_logging_in = True
        self.login_success = False
        self.login_error = None
        self.data_buffer = ""
        
        if self.status_callback:
            self.status_callback("开始自动登录...")
            
        if self.output_callback:
            self.output_callback(f"\n=== 开始自动登录 ===\n")
            
        # 启动登录线程
        login_thread = threading.Thread(target=self._login_process, daemon=True)
        login_thread.start()
        
        return True
        
    def _login_process(self):
        """登录处理线程"""
        try:
            # 设置临时数据回调
            original_callback = self.serial_manager.data_callback
            self.serial_manager.set_data_callback(self._on_login_data_received)
            
            start_time = time.time()
            
            # 发送初始回车以获取提示符
            self.serial_manager.send_command("")
            
            while self.is_logging_in and (time.time() - start_time) < self.login_timeout:
                try:
                    # 检查是否有新数据
                    if not self.response_queue.empty():
                        data = self.response_queue.get_nowait()
                        self.data_buffer += data
                        
                        # 检查各种提示符并响应
                        if self._check_and_respond():
                            continue
                            
                    time.sleep(0.1)
                    
                except queue.Empty:
                    continue
                    
            # 检查登录结果
            if self.is_logging_in:  # 超时
                self.login_error = "登录超时"
                if self.status_callback:
                    self.status_callback("登录超时")
                if self.output_callback:
                    self.output_callback("错误: 登录超时\n")
                    
        except Exception as e:
            self.login_error = str(e)
            if self.status_callback:
                self.status_callback(f"登录错误: {e}")
            if self.output_callback:
                self.output_callback(f"登录错误: {e}\n")
                
        finally:
            self.is_logging_in = False
            # 恢复原始回调
            self.serial_manager.set_data_callback(original_callback)
            
            if self.login_success:
                if self.status_callback:
                    self.status_callback("登录成功")
                if self.output_callback:
                    self.output_callback("=== 自动登录成功 ===\n\n")
            elif not self.login_error:
                self.login_error = "登录失败"
                if self.status_callback:
                    self.status_callback("登录失败")
                if self.output_callback:
                    self.output_callback("=== 自动登录失败 ===\n\n")
                    
    def _on_login_data_received(self, data: str):
        """登录过程中的数据接收回调"""
        self.response_queue.put(data)
        if self.output_callback:
            self.output_callback(data)
            
    def _check_and_respond(self) -> bool:
        """检查提示符并发送相应响应"""
        prompts = self.login_config.get("prompts", {})
        
        # 检查最后几行数据
        lines = self.data_buffer.split('\n')
        last_lines = '\n'.join(lines[-3:]).lower()  # 检查最后3行
        
        # 检查用户名提示
        for prompt in prompts.get("username", []):
            if prompt.lower() in last_lines:
                username = self.login_config.get("username", "")
                if username:
                    if self.output_callback:
                        self.output_callback(f"发送用户名: {username}\n")
                    self.serial_manager.send_command(username)
                    self._clear_buffer()
                    return True
                    
        # 检查密码提示
        for prompt in prompts.get("password", []):
            if prompt.lower() in last_lines and "enable" not in last_lines:
                password = self.login_config.get("password", "")
                if password:
                    if self.output_callback:
                        self.output_callback("发送密码: ****\n")
                    self.serial_manager.send_command(password)
                    self._clear_buffer()
                    return True
                    
        # 检查enable模式提示
        for prompt in prompts.get("enable", []):
            if last_lines.strip().endswith(prompt):
                if self.output_callback:
                    self.output_callback("进入特权模式\n")
                self.serial_manager.send_command("enable")
                self._clear_buffer()
                return True
                
        # 检查enable密码提示
        for prompt in prompts.get("enable_password", []):
            if prompt.lower() in last_lines and ("enable" in self.data_buffer.lower() or "privilege" in self.data_buffer.lower()):
                enable_password = self.login_config.get("enable_password", "")
                if enable_password:
                    if self.output_callback:
                        self.output_callback("发送Enable密码: ****\n")
                    self.serial_manager.send_command(enable_password)
                    self._clear_buffer()
                    return True
                    
        # 检查More提示
        for prompt in prompts.get("more", []):
            if prompt.lower() in last_lines:
                response = self.login_config.get("responses", {}).get("more", " ")
                if self.output_callback:
                    self.output_callback("发送翻页响应\n")
                self.serial_manager.send_command(response)
                self._clear_buffer()
                return True
                
        # 检查登录成功提示
        for prompt in prompts.get("success", []):
            if last_lines.strip().endswith(prompt):
                self.login_success = True
                self.is_logging_in = False
                return True
                
        return False
        
    def _clear_buffer(self):
        """清空缓冲区"""
        self.data_buffer = ""
        
    def stop_login(self):
        """停止登录过程"""
        self.is_logging_in = False
        
    def get_status(self) -> Dict[str, any]:
        """获取登录状态"""
        return {
            "is_logging_in": self.is_logging_in,
            "login_success": self.login_success,
            "login_error": self.login_error,
            "enabled": self.is_enabled()
        }
