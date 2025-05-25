"""
交互式终端模拟器模块
实现 SecureCRT 风格的交互式终端功能
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import re
import time
from typing import Callable, Optional


class InteractiveTerminal:
    """交互式终端模拟器类"""

    def __init__(self, parent, config, serial_manager):
        self.parent = parent
        self.config = config
        self.serial_manager = serial_manager

        # 终端配置
        self.terminal_config = config.get("terminal", {})
        self.local_echo = self.terminal_config.get("local_echo", False)
        self.line_ending = self.terminal_config.get("line_ending", "\r\n")

        # 状态管理
        self.is_active = False
        self.input_start_mark = "input_start"
        self.output_end_mark = "output_end"

        # 数据队列
        self.data_queue = queue.Queue()

        # 回调函数
        self.log_callback: Optional[Callable] = None

        # 创建终端界面
        self.create_terminal_widget()

        # 绑定事件
        self.bind_events()

        # 启动数据处理线程
        self.start_data_processor()

    def create_terminal_widget(self):
        """创建终端控件"""
        # 创建主框架
        self.terminal_frame = tk.Frame(self.parent)

        # 创建文本控件
        self.text_widget = scrolledtext.ScrolledText(
            self.terminal_frame,
            wrap=tk.CHAR,
            font=('Consolas', 10),
            bg='black',
            fg='green',
            insertbackground='green',
            selectbackground='darkgreen',
            state=tk.NORMAL
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签
        self.configure_text_tags()

        # 初始化标记
        self.text_widget.mark_set(self.input_start_mark, tk.END)
        self.text_widget.mark_set(self.output_end_mark, tk.END)

    def configure_text_tags(self):
        """配置文本标签样式"""
        # 输出文本（只读）
        self.text_widget.tag_configure("output", foreground="green")

        # 用户输入文本
        self.text_widget.tag_configure("input", foreground="yellow")

        # 错误信息
        self.text_widget.tag_configure("error", foreground="red")

        # 成功信息
        self.text_widget.tag_configure("success", foreground="lightgreen")

        # 时间戳
        self.text_widget.tag_configure("timestamp", foreground="cyan")

        # 只读区域
        self.text_widget.tag_configure("readonly", foreground="green")

    def bind_events(self):
        """绑定键盘和鼠标事件"""
        # 绑定所有按键事件
        self.text_widget.bind('<KeyPress>', self.on_key_press)
        self.text_widget.bind('<Button-1>', self.on_mouse_click)
        self.text_widget.bind('<Control-c>', self.on_ctrl_c)
        self.text_widget.bind('<Control-z>', self.on_ctrl_z)

        # 阻止某些默认行为
        self.text_widget.bind('<BackSpace>', self.on_backspace)
        self.text_widget.bind('<Delete>', self.on_delete)
        self.text_widget.bind('<Return>', self.on_return)
        self.text_widget.bind('<Tab>', self.on_tab)

        # 阻止粘贴到只读区域
        self.text_widget.bind('<Control-v>', self.on_paste)

    def on_key_press(self, event):
        """处理按键事件"""
        if not self.is_active:
            return "break"

        # 获取当前光标位置
        current_pos = self.text_widget.index(tk.INSERT)
        input_start_pos = self.text_widget.index(self.input_start_mark)

        # 检查是否在可输入区域
        if self.text_widget.compare(current_pos, "<", input_start_pos):
            # 在只读区域，移动光标到输入区域
            self.text_widget.mark_set(tk.INSERT, tk.END)
            return "break"

        # 处理可打印字符
        if len(event.char) == 1 and event.char.isprintable():
            char = event.char

            # 发送字符到设备
            if self.serial_manager.is_connected:
                self.serial_manager.send_raw_data(char.encode('utf-8'))

            # 本地回显（如果启用）
            if self.local_echo:
                self.insert_text(char, "input")

            return "break"

        # 处理特殊键
        return self.handle_special_keys(event)

    def handle_special_keys(self, event):
        """处理特殊按键"""
        if event.keysym == 'Return':
            return self.on_return(event)
        elif event.keysym == 'BackSpace':
            return self.on_backspace(event)
        elif event.keysym == 'Delete':
            return self.on_delete(event)
        elif event.keysym == 'Tab':
            return self.on_tab(event)
        elif event.keysym == 'question':
            # 问号键，用于命令帮助
            if self.serial_manager.is_connected:
                self.serial_manager.send_raw_data(b'?')
            if self.local_echo:
                self.insert_text('?', "input")
            return "break"

        # 允许其他按键的默认行为
        return None

    def on_return(self, event):
        """处理回车键"""
        if not self.is_active:
            return "break"

        # 发送回车到设备
        if self.serial_manager.is_connected:
            self.serial_manager.send_raw_data(self.line_ending.encode('utf-8'))

        # 本地回显
        if self.local_echo:
            self.insert_text('\n', "input")

        return "break"

    def on_backspace(self, event):
        """处理退格键"""
        if not self.is_active:
            return "break"

        current_pos = self.text_widget.index(tk.INSERT)
        input_start_pos = self.text_widget.index(self.input_start_mark)

        # 检查是否可以删除
        if self.text_widget.compare(current_pos, ">", input_start_pos):
            # 发送退格到设备
            if self.serial_manager.is_connected:
                self.serial_manager.send_raw_data(b'\x08')  # 或 b'\x7f'

            # 本地删除（如果启用本地回显）
            if self.local_echo:
                self.text_widget.delete(f"{current_pos}-1c", current_pos)

        return "break"

    def on_delete(self, event):
        """处理删除键"""
        # 在终端模式下通常不处理Delete键
        return "break"

    def on_tab(self, event):
        """处理Tab键"""
        if not self.is_active:
            return "break"

        # 发送Tab到设备（用于命令补全）
        if self.serial_manager.is_connected:
            self.serial_manager.send_raw_data(b'\t')

        return "break"

    def on_ctrl_c(self, event):
        """处理Ctrl+C"""
        if not self.is_active:
            return "break"

        # 发送中断信号
        if self.serial_manager.is_connected:
            self.serial_manager.send_raw_data(b'\x03')

        return "break"

    def on_ctrl_z(self, event):
        """处理Ctrl+Z"""
        if not self.is_active:
            return "break"

        # 发送挂起信号
        if self.serial_manager.is_connected:
            self.serial_manager.send_raw_data(b'\x1a')

        return "break"

    def on_mouse_click(self, event):
        """处理鼠标点击"""
        if not self.is_active:
            return

        # 允许在输入区域点击
        click_pos = self.text_widget.index(f"@{event.x},{event.y}")
        input_start_pos = self.text_widget.index(self.input_start_mark)

        if self.text_widget.compare(click_pos, "<", input_start_pos):
            # 点击在只读区域，移动到输入区域末尾
            self.text_widget.mark_set(tk.INSERT, tk.END)
            return "break"

    def on_paste(self, event):
        """处理粘贴事件"""
        if not self.is_active:
            return "break"

        try:
            # 获取剪贴板内容
            clipboard_text = self.text_widget.clipboard_get()

            # 逐字符发送（模拟真实输入）
            for char in clipboard_text:
                if self.serial_manager.is_connected:
                    self.serial_manager.send_raw_data(char.encode('utf-8'))
                    time.sleep(0.01)  # 小延时避免过快

            return "break"
        except tk.TclError:
            # 剪贴板为空或无法访问
            return "break"

    def start_data_processor(self):
        """启动数据处理线程"""
        self.data_thread = threading.Thread(target=self._process_data, daemon=True)
        self.data_thread.start()

    def _process_data(self):
        """数据处理线程"""
        while True:
            try:
                # 从队列获取数据
                data = self.data_queue.get(timeout=0.1)
                if data is None:  # 退出信号
                    break

                # 在主线程中更新GUI
                self.parent.after(0, self._update_display, data)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"数据处理错误: {e}")

    def _update_display(self, data):
        """在主线程中更新显示"""
        if not data:
            return

        # 处理ANSI转义序列
        processed_data = self.process_ansi_sequences(data)

        # 插入数据到终端
        self.insert_output(processed_data)

        # 更新输入起始标记
        self.text_widget.mark_set(self.input_start_mark, tk.END)

        # 自动滚动到底部
        self.text_widget.see(tk.END)

        # 记录日志
        if self.log_callback:
            self.log_callback(data)

    def process_ansi_sequences(self, data):
        """处理ANSI转义序列"""
        # 简单的ANSI序列处理
        # 移除常见的ANSI转义序列
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        # 处理退格字符
        processed = data

        # 处理 \b (退格)
        while '\b' in processed:
            pos = processed.find('\b')
            if pos > 0:
                # 删除退格前的一个字符和退格字符本身
                processed = processed[:pos-1] + processed[pos+1:]
            else:
                # 如果退格在开头，只删除退格字符
                processed = processed[1:]

        # 移除ANSI转义序列
        processed = ansi_escape.sub('', processed)

        return processed

    def insert_output(self, text):
        """插入输出文本"""
        if not text:
            return

        # 保存当前状态
        current_state = self.text_widget.cget('state')
        self.text_widget.config(state=tk.NORMAL)

        # 插入文本
        self.text_widget.insert(tk.END, text, "output")

        # 标记为只读
        start_pos = f"{tk.END}-{len(text)}c"
        self.text_widget.tag_add("readonly", start_pos, tk.END)

        # 恢复状态
        self.text_widget.config(state=current_state)

    def insert_text(self, text, tag=None):
        """插入文本（通用方法）"""
        if not text:
            return

        current_state = self.text_widget.cget('state')
        self.text_widget.config(state=tk.NORMAL)

        if tag:
            self.text_widget.insert(tk.END, text, tag)
        else:
            self.text_widget.insert(tk.END, text)

        self.text_widget.config(state=current_state)

    def receive_data(self, data):
        """接收来自串口的数据"""
        if data:
            self.data_queue.put(data)

    def activate(self):
        """激活终端"""
        self.is_active = True
        self.text_widget.focus_set()
        self.text_widget.mark_set(tk.INSERT, tk.END)

    def deactivate(self):
        """停用终端"""
        self.is_active = False

    def clear(self):
        """清空终端"""
        current_state = self.text_widget.cget('state')
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.mark_set(self.input_start_mark, tk.END)
        self.text_widget.mark_set(self.output_end_mark, tk.END)
        self.text_widget.config(state=current_state)

    def get_widget(self):
        """获取终端控件"""
        return self.terminal_frame

    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback

    def configure_terminal(self, **kwargs):
        """配置终端参数"""
        if 'local_echo' in kwargs:
            self.local_echo = kwargs['local_echo']
        if 'line_ending' in kwargs:
            self.line_ending = kwargs['line_ending']

    def get_current_line(self):
        """获取当前输入行"""
        input_start_pos = self.text_widget.index(self.input_start_mark)
        current_pos = self.text_widget.index(tk.END)

        if self.text_widget.compare(current_pos, ">", input_start_pos):
            return self.text_widget.get(input_start_pos, current_pos)
        return ""

    def set_prompt(self, prompt):
        """设置命令提示符"""
        self.insert_output(prompt)
        self.text_widget.mark_set(self.input_start_mark, tk.END)

    def destroy(self):
        """销毁终端"""
        self.is_active = False
        self.data_queue.put(None)  # 发送退出信号
        if hasattr(self, 'data_thread'):
            self.data_thread.join(timeout=1)
