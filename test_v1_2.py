#!/usr/bin/env python3
"""
网络设备自动化助手 v1.2 功能测试脚本
"""

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")

    try:
        from config import Config
        print("  ✅ Config 模块导入成功")

        from serial_manager import SerialManager
        print("  ✅ SerialManager 模块导入成功")

        from auto_login_manager import AutoLoginManager
        print("  ✅ AutoLoginManager 模块导入成功")

        from interactive_terminal import InteractiveTerminal
        print("  ✅ InteractiveTerminal 模块导入成功")

        from device_detector import DeviceDetector
        print("  ✅ DeviceDetector 模块导入成功")

        from command_manager import CommandManager
        print("  ✅ CommandManager 模块导入成功")

        return True
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_config_v1_2():
    """测试 v1.2 配置功能"""
    print("\n⚙️ 测试 v1.2 配置...")

    try:
        from config import Config
        config = Config()

        # 测试自动登录配置
        auto_login_config = config.get("auto_login")
        if auto_login_config:
            print("  ✅ 自动登录配置存在")
            print(f"    - 启用状态: {auto_login_config.get('enabled', False)}")
            print(f"    - 超时时间: {auto_login_config.get('timeout', 30)}秒")
        else:
            print("  ❌ 自动登录配置缺失")
            return False

        # 测试终端配置
        terminal_config = config.get("terminal")
        if terminal_config:
            print("  ✅ 终端配置存在")
            print(f"    - 本地回显: {terminal_config.get('local_echo', False)}")
            line_ending = terminal_config.get('line_ending', '\r\n')
            print(f"    - 行结束符: {repr(line_ending)}")
            print(f"    - 字体: {terminal_config.get('font_family', 'Consolas')}")
        else:
            print("  ❌ 终端配置缺失")
            return False

        return True
    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")
        return False

def test_interactive_terminal():
    """测试交互式终端"""
    print("\n🖥️ 测试交互式终端...")

    try:
        from config import Config
        from serial_manager import SerialManager
        from interactive_terminal import InteractiveTerminal
        import tkinter as tk

        # 创建测试环境
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        config = Config()
        serial_manager = SerialManager(config)

        # 创建交互式终端
        terminal = InteractiveTerminal(root, config, serial_manager)
        print("  ✅ 交互式终端创建成功")

        # 测试基本方法
        terminal.activate()
        print("  ✅ 终端激活成功")

        terminal.deactivate()
        print("  ✅ 终端停用成功")

        terminal.clear()
        print("  ✅ 终端清空成功")

        # 测试配置
        terminal.configure_terminal(local_echo=True, line_ending="\n")
        print("  ✅ 终端配置成功")

        # 清理
        terminal.destroy()
        root.destroy()

        return True
    except Exception as e:
        print(f"  ❌ 交互式终端测试失败: {e}")
        return False

def test_serial_manager_v1_2():
    """测试串口管理器 v1.2 功能"""
    print("\n📡 测试串口管理器 v1.2...")

    try:
        from config import Config
        from serial_manager import SerialManager

        config = Config()
        serial_manager = SerialManager(config)

        # 测试新增的原始数据发送方法
        if hasattr(serial_manager, 'send_raw_data'):
            print("  ✅ send_raw_data 方法存在")
        else:
            print("  ❌ send_raw_data 方法缺失")
            return False

        # 测试端口获取
        ports = serial_manager.get_available_ports()
        print(f"  ✅ 检测到 {len(ports)} 个COM端口")

        return True
    except Exception as e:
        print(f"  ❌ 串口管理器测试失败: {e}")
        return False

def test_main_program():
    """测试主程序"""
    print("\n🚀 测试主程序...")

    try:
        # 只测试导入，不启动GUI
        import main
        print("  ✅ 主程序模块导入成功")

        # 检查版本号
        if hasattr(main, 'NetworkDeviceAssistant'):
            print("  ✅ NetworkDeviceAssistant 类存在")
        else:
            print("  ❌ NetworkDeviceAssistant 类缺失")
            return False

        return True
    except Exception as e:
        print(f"  ❌ 主程序测试失败: {e}")
        return False

def show_v1_2_features():
    """显示 v1.2 新特性"""
    print("\n🎉 网络设备自动化助手 v1.2 新特性:")
    print("=" * 60)

    print("\n🖥️ SecureCRT 风格交互式终端:")
    print("  • 实时按键捕捉和发送")
    print("  • 统一的交互界面")
    print("  • 智能光标管理")
    print("  • 输入/输出区域分离")
    print("  • ANSI 转义码支持")
    print("  • 特殊按键处理 (Tab, ?, Ctrl+C, 退格)")

    print("\n🔐 自动登录功能:")
    print("  • 智能提示符检测")
    print("  • 自动用户名密码输入")
    print("  • 多设备兼容")
    print("  • 可配置响应")
    print("  • 登录状态显示")

    print("\n🎛️ 双模式操作:")
    print("  • 交互式模式 (SecureCRT 风格)")
    print("  • 传统模式 (原有方式)")
    print("  • 运行时无缝切换")

    print("\n🔧 技术改进:")
    print("  • 多线程架构优化")
    print("  • 本地回显控制")
    print("  • 智能退格处理")
    print("  • 配置系统扩展")

def main():
    """主测试函数"""
    print("🧪 网络设备自动化助手 v1.2 功能测试")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("v1.2 配置", test_config_v1_2),
        ("交互式终端", test_interactive_terminal),
        ("串口管理器 v1.2", test_serial_manager_v1_2),
        ("主程序", test_main_program),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！v1.2 功能准备就绪。")
        show_v1_2_features()

        print("\n🚀 启动程序:")
        print("  运行 'python main.py' 启动网络设备自动化助手 v1.2")

        return True
    else:
        print("⚠️ 部分测试失败，请检查代码。")
        return False

if __name__ == "__main__":
    main()
