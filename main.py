"""
网络设备自动化助手 - 主程序
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import os
import json
from datetime import datetime
from typing import Optional

from config import Config
from serial_manager import SerialManager
from device_detector import DeviceDetector
from command_manager import CommandManager

class NetworkDeviceAssistant:
    """网络设备自动化助手主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网络设备自动化助手 v1.0")
        self.root.geometry("1200x800")

        # 初始化配置和管理器
        self.config = Config()
        self.config.ensure_directories()

        self.serial_manager = SerialManager(self.config)
        self.device_detector = DeviceDetector(self.config, self.serial_manager)
        self.command_manager = CommandManager(self.config, self.serial_manager)

        # 创建默认命令序列
        self.command_manager.create_default_sequences()

        # 设置串口数据回调
        self.serial_manager.set_data_callback(self.on_serial_data_received)

        # 初始化变量
        self.current_log_file = None
        self.is_auto_scroll = True

        # 创建GUI
        self.create_gui()

        # 初始化
        self.refresh_ports()
        self.refresh_command_sequences()

    def create_gui(self):
        """创建GUI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建左侧控制面板
        self.create_control_panel(main_frame)

        # 创建右侧输出面板
        self.create_output_panel(main_frame)

        # 创建状态栏
        self.create_status_bar()

    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 连接设置区域
        conn_frame = ttk.LabelFrame(control_frame, text="连接设置", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        # COM端口选择
        ttk.Label(conn_frame, text="COM端口:").pack(anchor=tk.W)
        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill=tk.X, pady=(5, 10))

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, state="readonly")
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(port_frame, text="刷新", command=self.refresh_ports, width=8).pack(side=tk.RIGHT, padx=(5, 0))

        # 波特率选择
        ttk.Label(conn_frame, text="波特率:").pack(anchor=tk.W)
        baud_frame = ttk.Frame(conn_frame)
        baud_frame.pack(fill=tk.X, pady=(5, 10))

        self.baud_var = tk.StringVar()
        self.baud_combo = ttk.Combobox(baud_frame, textvariable=self.baud_var)
        self.baud_combo['values'] = self.config.get("baudrates")
        self.baud_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(baud_frame, text="自动检测", command=self.auto_detect_baudrate, width=8).pack(side=tk.RIGHT, padx=(5, 0))

        # 连接按钮
        button_frame = ttk.Frame(conn_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        self.connect_btn = ttk.Button(button_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(button_frame, text="设备识别", command=self.detect_device).pack(side=tk.RIGHT, padx=(5, 0))

        # 设备信息区域
        device_frame = ttk.LabelFrame(control_frame, text="设备信息", padding=10)
        device_frame.pack(fill=tk.X, pady=(0, 10))

        self.device_info_text = tk.Text(device_frame, height=6, state=tk.DISABLED)
        self.device_info_text.pack(fill=tk.BOTH, expand=True)

        # 命令序列区域
        cmd_frame = ttk.LabelFrame(control_frame, text="命令序列", padding=10)
        cmd_frame.pack(fill=tk.BOTH, expand=True)

        # 命令序列选择
        ttk.Label(cmd_frame, text="选择序列:").pack(anchor=tk.W)
        seq_frame = ttk.Frame(cmd_frame)
        seq_frame.pack(fill=tk.X, pady=(5, 10))

        self.sequence_var = tk.StringVar()
        self.sequence_combo = ttk.Combobox(seq_frame, textvariable=self.sequence_var, state="readonly")
        self.sequence_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.sequence_combo.bind('<<ComboboxSelected>>', self.on_sequence_selected)

        ttk.Button(seq_frame, text="刷新", command=self.refresh_command_sequences, width=8).pack(side=tk.RIGHT, padx=(5, 0))

        # 序列描述
        ttk.Label(cmd_frame, text="描述:").pack(anchor=tk.W)
        self.sequence_desc_text = tk.Text(cmd_frame, height=3, state=tk.DISABLED)
        self.sequence_desc_text.pack(fill=tk.X, pady=(5, 10))

        # 执行控制
        exec_frame = ttk.Frame(cmd_frame)
        exec_frame.pack(fill=tk.X, pady=(0, 10))

        self.execute_btn = ttk.Button(exec_frame, text="执行序列", command=self.execute_sequence, state=tk.DISABLED)
        self.execute_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(exec_frame, text="编辑", command=self.edit_sequence).pack(side=tk.RIGHT, padx=(5, 0))

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(cmd_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # 日志控制
        log_frame = ttk.Frame(cmd_frame)
        log_frame.pack(fill=tk.X)

        ttk.Button(log_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(log_frame, text="清空输出", command=self.clear_output).pack(side=tk.RIGHT, padx=(5, 0))

    def create_output_panel(self, parent):
        """创建右侧输出面板"""
        output_frame = ttk.LabelFrame(parent, text="输出日志", padding=10)
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建带滚动条的文本框
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # 输出控制
        output_control_frame = ttk.Frame(output_frame)
        output_control_frame.pack(fill=tk.X, pady=(10, 0))

        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_control_frame, text="自动滚动", variable=self.auto_scroll_var).pack(side=tk.LEFT)

        # 手动命令输入
        manual_frame = ttk.Frame(output_control_frame)
        manual_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        self.manual_cmd_var = tk.StringVar()
        manual_entry = ttk.Entry(manual_frame, textvariable=self.manual_cmd_var)
        manual_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        manual_entry.bind('<Return>', self.send_manual_command)

        ttk.Button(manual_frame, text="发送", command=self.send_manual_command).pack(side=tk.RIGHT, padx=(5, 0))

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # 连接状态指示器
        self.connection_status = ttk.Label(self.status_bar, text="未连接", foreground="red")
        self.connection_status.pack(side=tk.RIGHT, padx=10, pady=5)

    def refresh_ports(self):
        """刷新COM端口列表"""
        ports = self.serial_manager.get_available_ports()
        self.port_combo['values'] = ports

        if ports:
            self.port_var.set(ports[0])
            self.update_status(f"检测到 {len(ports)} 个COM端口")
        else:
            self.port_var.set("")
            self.update_status("未检测到COM端口")

    def auto_detect_baudrate(self):
        """自动检测波特率"""
        if not self.port_var.get():
            messagebox.showwarning("警告", "请先选择COM端口")
            return

        self.update_status("正在检测波特率...")
        self.root.config(cursor="wait")

        def detect():
            try:
                baudrate = self.serial_manager.detect_baudrate(self.port_var.get())
                self.root.after(0, self._on_baudrate_detected, baudrate)
            except Exception as e:
                self.root.after(0, self._on_baudrate_detect_error, str(e))

        threading.Thread(target=detect, daemon=True).start()

    def _on_baudrate_detected(self, baudrate):
        """波特率检测完成回调"""
        self.root.config(cursor="")
        if baudrate:
            self.baud_var.set(str(baudrate))
            self.update_status(f"检测到波特率: {baudrate}")
            messagebox.showinfo("成功", f"自动检测到波特率: {baudrate}")
        else:
            self.update_status("波特率检测失败")
            messagebox.showwarning("失败", "无法自动检测波特率，请手动选择")

    def _on_baudrate_detect_error(self, error):
        """波特率检测错误回调"""
        self.root.config(cursor="")
        self.update_status(f"波特率检测错误: {error}")
        messagebox.showerror("错误", f"波特率检测失败: {error}")

    def toggle_connection(self):
        """切换连接状态"""
        if self.serial_manager.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """连接设备"""
        port = self.port_var.get()
        baudrate_str = self.baud_var.get()

        if not port:
            messagebox.showwarning("警告", "请选择COM端口")
            return

        if not baudrate_str:
            messagebox.showwarning("警告", "请选择或输入波特率")
            return

        try:
            baudrate = int(baudrate_str)
        except ValueError:
            messagebox.showerror("错误", "波特率必须是数字")
            return

        self.update_status("正在连接...")

        if self.serial_manager.connect(port, baudrate):
            self.connect_btn.config(text="断开")
            self.connection_status.config(text="已连接", foreground="green")
            self.execute_btn.config(state=tk.NORMAL)
            self.update_status(f"已连接到 {port} (波特率: {baudrate})")
            self.append_output(f"[{datetime.now().strftime('%H:%M:%S')}] 连接成功: {port} @ {baudrate}\n")

            # 开始日志记录
            self.start_logging()
        else:
            messagebox.showerror("错误", "连接失败，请检查端口和波特率")
            self.update_status("连接失败")

    def disconnect(self):
        """断开连接"""
        self.serial_manager.disconnect()
        self.connect_btn.config(text="连接")
        self.connection_status.config(text="未连接", foreground="red")
        self.execute_btn.config(state=tk.DISABLED)
        self.update_status("已断开连接")
        self.append_output(f"[{datetime.now().strftime('%H:%M:%S')}] 连接已断开\n")

        # 停止日志记录
        self.stop_logging()

    def detect_device(self):
        """检测设备信息"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("警告", "请先连接设备")
            return

        self.update_status("正在识别设备...")

        def detect():
            try:
                device_info = self.device_detector.detect_device()
                self.root.after(0, self._on_device_detected, device_info)
            except Exception as e:
                self.root.after(0, self._on_device_detect_error, str(e))

        threading.Thread(target=detect, daemon=True).start()

    def _on_device_detected(self, device_info):
        """设备检测完成回调"""
        self.device_info_text.config(state=tk.NORMAL)
        self.device_info_text.delete(1.0, tk.END)

        info_text = f"厂商: {device_info['vendor']}\n"
        info_text += f"型号: {device_info['model']}\n"
        info_text += f"版本: {device_info['version']}\n"
        info_text += f"主机名: {device_info['hostname']}\n"

        self.device_info_text.insert(1.0, info_text)
        self.device_info_text.config(state=tk.DISABLED)

        self.update_status(f"设备识别完成: {device_info['vendor']} {device_info['model']}")

    def _on_device_detect_error(self, error):
        """设备检测错误回调"""
        self.update_status(f"设备识别失败: {error}")
        messagebox.showerror("错误", f"设备识别失败: {error}")

    def refresh_command_sequences(self):
        """刷新命令序列列表"""
        sequences = self.command_manager.get_command_files()
        self.sequence_combo['values'] = sequences

        if sequences:
            self.sequence_var.set(sequences[0])
            self.on_sequence_selected()

    def on_sequence_selected(self, event=None):
        """命令序列选择事件"""
        sequence_name = self.sequence_var.get()
        if not sequence_name:
            return

        sequence = self.command_manager.load_command_sequence(sequence_name)
        if sequence:
            self.sequence_desc_text.config(state=tk.NORMAL)
            self.sequence_desc_text.delete(1.0, tk.END)

            desc = sequence.get('description', '无描述')
            vendor = sequence.get('vendor', '通用')
            commands_count = len(sequence.get('commands', []))

            desc_text = f"描述: {desc}\n"
            desc_text += f"适用厂商: {vendor}\n"
            desc_text += f"命令数量: {commands_count}"

            self.sequence_desc_text.insert(1.0, desc_text)
            self.sequence_desc_text.config(state=tk.DISABLED)

    def execute_sequence(self):
        """执行命令序列"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("警告", "请先连接设备")
            return

        sequence_name = self.sequence_var.get()
        if not sequence_name:
            messagebox.showwarning("警告", "请选择命令序列")
            return

        self.execute_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)

        def execute():
            try:
                success = self.command_manager.execute_command_sequence(
                    sequence_name,
                    progress_callback=self.update_progress,
                    output_callback=self.append_output
                )
                self.root.after(0, self._on_sequence_executed, success)
            except Exception as e:
                self.root.after(0, self._on_sequence_execute_error, str(e))

        threading.Thread(target=execute, daemon=True).start()

    def _on_sequence_executed(self, success):
        """命令序列执行完成回调"""
        self.execute_btn.config(state=tk.NORMAL)
        if success:
            self.update_status("命令序列执行完成")
        else:
            self.update_status("命令序列执行失败")

    def _on_sequence_execute_error(self, error):
        """命令序列执行错误回调"""
        self.execute_btn.config(state=tk.NORMAL)
        self.update_status(f"命令序列执行错误: {error}")
        messagebox.showerror("错误", f"命令序列执行失败: {error}")

    def edit_sequence(self):
        """编辑命令序列"""
        sequence_name = self.sequence_var.get()
        if not sequence_name:
            messagebox.showwarning("警告", "请选择命令序列")
            return

        # 创建编辑窗口
        edit_window = SequenceEditWindow(self.root, self.command_manager, sequence_name)
        edit_window.show()

        # 刷新序列列表
        self.refresh_command_sequences()

    def send_manual_command(self, event=None):
        """发送手动命令"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("警告", "请先连接设备")
            return

        command = self.manual_cmd_var.get().strip()
        if not command:
            return

        self.append_output(f"[{datetime.now().strftime('%H:%M:%S')}] 发送命令: {command}\n")

        if self.serial_manager.send_command(command):
            self.manual_cmd_var.set("")
        else:
            self.append_output("错误: 命令发送失败\n")

    def on_serial_data_received(self, data):
        """串口数据接收回调"""
        self.root.after(0, self.append_output, data)

    def append_output(self, text):
        """添加输出文本"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)

        # 自动滚动
        if self.auto_scroll_var.get():
            self.output_text.see(tk.END)

        self.output_text.config(state=tk.DISABLED)

        # 写入日志文件
        if self.current_log_file:
            try:
                with open(self.current_log_file, 'a', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                print(f"写入日志文件失败: {e}")

    def clear_output(self):
        """清空输出"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

    def save_log(self):
        """保存日志"""
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("提示", "没有日志内容可保存")
            return

        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")

    def start_logging(self):
        """开始日志记录"""
        log_dir = self.config.get("log_directory", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(log_dir, f"session_{timestamp}.txt")

        # 写入会话开始标记
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== 会话开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    def stop_logging(self):
        """停止日志记录"""
        if self.current_log_file:
            try:
                with open(self.current_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== 会话结束 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            except Exception as e:
                print(f"写入会话结束标记失败: {e}")

        self.current_log_file = None

    def update_progress(self, value):
        """更新进度条"""
        self.root.after(0, self.progress_var.set, value)

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        finally:
            # 清理资源
            if self.serial_manager.is_connected:
                self.serial_manager.disconnect()
            self.stop_logging()


class SequenceEditWindow:
    """命令序列编辑窗口"""

    def __init__(self, parent, command_manager, sequence_name=None):
        self.parent = parent
        self.command_manager = command_manager
        self.sequence_name = sequence_name
        self.window = None

    def show(self):
        """显示编辑窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("编辑命令序列" if self.sequence_name else "新建命令序列")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.grab_set()

        # 加载现有序列数据
        if self.sequence_name:
            self.sequence_data = self.command_manager.load_command_sequence(self.sequence_name)
        else:
            self.sequence_data = {
                "description": "",
                "vendor": "通用",
                "commands": []
            }

        self.create_edit_gui()

    def create_edit_gui(self):
        """创建编辑界面"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 基本信息
        info_frame = ttk.LabelFrame(main_frame, text="基本信息", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # 序列名称
        ttk.Label(info_frame, text="序列名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.sequence_name or "")
        ttk.Entry(info_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # 描述
        ttk.Label(info_frame, text="描述:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value=self.sequence_data.get("description", ""))
        ttk.Entry(info_frame, textvariable=self.desc_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # 厂商
        ttk.Label(info_frame, text="适用厂商:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vendor_var = tk.StringVar(value=self.sequence_data.get("vendor", "通用"))
        vendor_combo = ttk.Combobox(info_frame, textvariable=self.vendor_var, values=["通用", "Huawei", "ZTE", "H3C"])
        vendor_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # 命令列表
        cmd_frame = ttk.LabelFrame(main_frame, text="命令列表", padding=10)
        cmd_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 命令列表控件
        list_frame = ttk.Frame(cmd_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview
        columns = ("序号", "命令", "延时", "描述")
        self.cmd_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.cmd_tree.heading(col, text=col)
            if col == "序号":
                self.cmd_tree.column(col, width=50)
            elif col == "延时":
                self.cmd_tree.column(col, width=60)
            elif col == "命令":
                self.cmd_tree.column(col, width=200)
            else:
                self.cmd_tree.column(col, width=150)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.cmd_tree.yview)
        self.cmd_tree.configure(yscrollcommand=scrollbar.set)

        self.cmd_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 命令操作按钮
        btn_frame = ttk.Frame(cmd_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="添加命令", command=self.add_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="编辑命令", command=self.edit_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除命令", command=self.delete_command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="上移", command=self.move_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="下移", command=self.move_down).pack(side=tk.LEFT, padx=(0, 5))

        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="保存", command=self.save_sequence).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_frame, text="取消", command=self.window.destroy).pack(side=tk.RIGHT)

        # 加载命令列表
        self.load_commands()

    def load_commands(self):
        """加载命令列表"""
        # 清空现有项目
        for item in self.cmd_tree.get_children():
            self.cmd_tree.delete(item)

        # 添加命令
        commands = self.sequence_data.get("commands", [])
        for i, cmd in enumerate(commands, 1):
            self.cmd_tree.insert("", tk.END, values=(
                i,
                cmd.get("command", ""),
                cmd.get("delay", 1),
                cmd.get("description", "")
            ))

    def add_command(self):
        """添加命令"""
        dialog = CommandEditDialog(self.window, "添加命令")
        result = dialog.show()

        if result:
            self.sequence_data.setdefault("commands", []).append(result)
            self.load_commands()

    def edit_command(self):
        """编辑命令"""
        selection = self.cmd_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的命令")
            return

        item = selection[0]
        index = self.cmd_tree.index(item)

        commands = self.sequence_data.get("commands", [])
        if index < len(commands):
            dialog = CommandEditDialog(self.window, "编辑命令", commands[index])
            result = dialog.show()

            if result:
                commands[index] = result
                self.load_commands()

    def delete_command(self):
        """删除命令"""
        selection = self.cmd_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的命令")
            return

        if messagebox.askyesno("确认", "确定要删除选中的命令吗？"):
            item = selection[0]
            index = self.cmd_tree.index(item)

            commands = self.sequence_data.get("commands", [])
            if index < len(commands):
                commands.pop(index)
                self.load_commands()

    def move_up(self):
        """上移命令"""
        selection = self.cmd_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.cmd_tree.index(item)

        if index > 0:
            commands = self.sequence_data.get("commands", [])
            commands[index], commands[index-1] = commands[index-1], commands[index]
            self.load_commands()

            # 重新选择移动后的项目
            new_item = self.cmd_tree.get_children()[index-1]
            self.cmd_tree.selection_set(new_item)

    def move_down(self):
        """下移命令"""
        selection = self.cmd_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.cmd_tree.index(item)

        commands = self.sequence_data.get("commands", [])
        if index < len(commands) - 1:
            commands[index], commands[index+1] = commands[index+1], commands[index]
            self.load_commands()

            # 重新选择移动后的项目
            new_item = self.cmd_tree.get_children()[index+1]
            self.cmd_tree.selection_set(new_item)

    def save_sequence(self):
        """保存序列"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入序列名称")
            return

        # 更新序列数据
        self.sequence_data["description"] = self.desc_var.get().strip()
        self.sequence_data["vendor"] = self.vendor_var.get()

        # 验证序列
        errors = self.command_manager.validate_command_sequence(self.sequence_data)
        if errors:
            messagebox.showerror("错误", "序列验证失败:\n" + "\n".join(errors))
            return

        # 保存序列
        if self.command_manager.save_command_sequence(name, self.sequence_data):
            messagebox.showinfo("成功", "序列保存成功")
            self.window.destroy()
        else:
            messagebox.showerror("错误", "序列保存失败")


class CommandEditDialog:
    """命令编辑对话框"""

    def __init__(self, parent, title, command_data=None):
        self.parent = parent
        self.title = title
        self.command_data = command_data or {}
        self.result = None
        self.window = None

    def show(self):
        """显示对话框"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry("500x300")
        self.window.transient(self.parent)
        self.window.grab_set()

        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

        self.create_dialog_gui()

        # 等待窗口关闭
        self.window.wait_window()
        return self.result

    def create_dialog_gui(self):
        """创建对话框界面"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 命令输入
        ttk.Label(main_frame, text="命令:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.command_var = tk.StringVar(value=self.command_data.get("command", ""))
        command_entry = ttk.Entry(main_frame, textvariable=self.command_var, width=50)
        command_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)
        command_entry.focus()

        # 延时设置
        ttk.Label(main_frame, text="延时(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.StringVar(value=str(self.command_data.get("delay", 2)))
        delay_entry = ttk.Entry(main_frame, textvariable=self.delay_var, width=10)
        delay_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # 描述输入
        ttk.Label(main_frame, text="描述:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value=self.command_data.get("description", ""))
        desc_entry = ttk.Entry(main_frame, textvariable=self.desc_var, width=50)
        desc_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=5)

        # 配置列权重
        main_frame.columnconfigure(1, weight=1)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side=tk.RIGHT)

        # 绑定回车键
        self.window.bind('<Return>', lambda e: self.ok_clicked())
        self.window.bind('<Escape>', lambda e: self.cancel_clicked())

    def ok_clicked(self):
        """确定按钮点击"""
        command = self.command_var.get().strip()
        if not command:
            messagebox.showwarning("警告", "请输入命令")
            return

        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                raise ValueError("延时不能为负数")
        except ValueError:
            messagebox.showerror("错误", "延时必须是有效的数字")
            return

        self.result = {
            "command": command,
            "delay": delay,
            "description": self.desc_var.get().strip()
        }

        self.window.destroy()

    def cancel_clicked(self):
        """取消按钮点击"""
        self.result = None
        self.window.destroy()


def main():
    """主程序入口"""
    try:
        app = NetworkDeviceAssistant()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
