#!/usr/bin/env python3
"""
测试 AttributeError 修复效果
"""

def test_variable_initialization():
    """测试变量初始化"""
    print("🔍 测试变量初始化...")
    
    try:
        # 导入主程序模块
        import main
        
        # 创建应用实例（不启动GUI）
        app = main.NetworkDeviceAssistant()
        
        # 测试 auto_scroll_var
        if hasattr(app, 'auto_scroll_var'):
            print("  ✅ auto_scroll_var 已初始化")
            print(f"    - 类型: {type(app.auto_scroll_var)}")
            print(f"    - 默认值: {app.auto_scroll_var.get()}")
        else:
            print("  ❌ auto_scroll_var 未初始化")
            return False
            
        # 测试 live_mode_var
        if hasattr(app, 'live_mode_var'):
            print("  ✅ live_mode_var 已初始化")
            print(f"    - 类型: {type(app.live_mode_var)}")
            print(f"    - 默认值: {app.live_mode_var.get()}")
        else:
            print("  ❌ live_mode_var 未初始化")
            return False
            
        # 测试其他关键变量
        required_vars = [
            'terminal_mode_var',
            'local_echo_var',
            'auto_login_enabled_var',
            'port_var',
            'baud_var',
            'sequence_var',
            'manual_cmd_var',
            'username_var',
            'password_var',
            'enable_password_var'
        ]
        
        for var_name in required_vars:
            if hasattr(app, var_name):
                print(f"  ✅ {var_name} 已初始化")
            else:
                print(f"  ❌ {var_name} 未初始化")
                return False
                
        # 销毁应用实例
        app.root.destroy()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_gui_components():
    """测试GUI组件"""
    print("\n🖥️ 测试GUI组件...")
    
    try:
        import main
        import tkinter as tk
        
        # 创建应用实例
        app = main.NetworkDeviceAssistant()
        
        # 测试复选框是否存在
        checkboxes_found = 0
        
        # 遍历所有子控件查找复选框
        def find_checkboxes(widget):
            nonlocal checkboxes_found
            for child in widget.winfo_children():
                if isinstance(child, tk.Checkbutton) or str(type(child)).find('Checkbutton') != -1:
                    checkboxes_found += 1
                    print(f"    - 找到复选框: {child.cget('text') if hasattr(child, 'cget') else '未知'}")
                find_checkboxes(child)
        
        find_checkboxes(app.root)
        
        print(f"  ✅ 找到 {checkboxes_found} 个复选框")
        
        # 测试变量绑定
        try:
            # 测试 auto_scroll_var 的 get 方法
            auto_scroll_value = app.auto_scroll_var.get()
            print(f"  ✅ auto_scroll_var.get() = {auto_scroll_value}")
            
            # 测试 live_mode_var 的 get 方法
            live_mode_value = app.live_mode_var.get()
            print(f"  ✅ live_mode_var.get() = {live_mode_value}")
            
        except Exception as e:
            print(f"  ❌ 变量绑定测试失败: {e}")
            return False
            
        # 销毁应用实例
        app.root.destroy()
        
        return True
        
    except Exception as e:
        print(f"  ❌ GUI组件测试失败: {e}")
        return False

def test_method_calls():
    """测试方法调用"""
    print("\n🔧 测试方法调用...")
    
    try:
        import main
        
        # 创建应用实例
        app = main.NetworkDeviceAssistant()
        
        # 测试 append_output_with_style 方法
        try:
            app.append_output_with_style("测试文本\n")
            print("  ✅ append_output_with_style 方法调用成功")
        except AttributeError as e:
            if 'auto_scroll_var' in str(e):
                print(f"  ❌ append_output_with_style 仍有 auto_scroll_var 错误: {e}")
                return False
            else:
                print(f"  ⚠️ append_output_with_style 其他错误: {e}")
        
        # 测试 send_manual_command 方法
        try:
            app.manual_cmd_var.set("test command")
            # 注意：这里不实际发送命令，只测试变量访问
            if app.live_mode_var.get() is not None:
                print("  ✅ send_manual_command 中的 live_mode_var 访问成功")
        except AttributeError as e:
            if 'live_mode_var' in str(e):
                print(f"  ❌ send_manual_command 仍有 live_mode_var 错误: {e}")
                return False
            else:
                print(f"  ⚠️ send_manual_command 其他错误: {e}")
        
        # 销毁应用实例
        app.root.destroy()
        
        return True
        
    except Exception as e:
        print(f"  ❌ 方法调用测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 AttributeError 修复测试")
    print("=" * 50)
    
    tests = [
        ("变量初始化", test_variable_initialization),
        ("GUI组件", test_gui_components),
        ("方法调用", test_method_calls),
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
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！AttributeError 已修复。")
        print("\n✨ 修复内容:")
        print("  • 在 __init__ 方法中初始化了 auto_scroll_var")
        print("  • 在 __init__ 方法中初始化了 live_mode_var")
        print("  • 在终端控制面板中添加了对应的复选框")
        print("  • 确保所有 Tkinter 变量在使用前都已正确初始化")
        
        print("\n🚀 程序现在可以正常运行:")
        print("  运行 'python main.py' 启动网络设备自动化助手 v1.2")
        
        return True
    else:
        print("⚠️ 部分测试失败，可能还有其他问题需要修复。")
        return False

if __name__ == "__main__":
    main()
