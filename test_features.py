#!/usr/bin/env python3
"""
测试新功能的脚本
"""

def test_imports():
    """测试所有模块是否能正常导入"""
    try:
        from config import Config
        print("✓ Config 模块导入成功")

        from auto_login_manager import AutoLoginManager
        print("✓ AutoLoginManager 模块导入成功")

        from serial_manager import SerialManager
        print("✓ SerialManager 模块导入成功")

        from device_detector import DeviceDetector
        print("✓ DeviceDetector 模块导入成功")

        from command_manager import CommandManager
        print("✓ CommandManager 模块导入成功")

        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_config():
    """测试配置功能"""
    try:
        from config import Config
        config = Config()

        # 测试自动登录配置
        auto_login_config = config.get("auto_login")
        if auto_login_config:
            print("✓ 自动登录配置存在")
            print(f"  - 启用状态: {auto_login_config.get('enabled', False)}")
            print(f"  - 超时时间: {auto_login_config.get('timeout', 30)}秒")
            print(f"  - 用户名提示符数量: {len(auto_login_config.get('prompts', {}).get('username', []))}")
            print(f"  - 密码提示符数量: {len(auto_login_config.get('prompts', {}).get('password', []))}")
        else:
            print("✗ 自动登录配置不存在")
            return False

        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_auto_login_manager():
    """测试自动登录管理器"""
    try:
        from config import Config
        from serial_manager import SerialManager
        from auto_login_manager import AutoLoginManager

        config = Config()
        serial_manager = SerialManager(config)
        auto_login_manager = AutoLoginManager(config, serial_manager)

        print("✓ AutoLoginManager 创建成功")

        # 测试配置更新
        auto_login_manager.update_login_config(
            username="test_user",
            password="test_pass",
            enable_password="test_enable",
            enabled=False
        )
        print("✓ 登录配置更新成功")

        # 测试状态获取
        status = auto_login_manager.get_status()
        print(f"✓ 状态获取成功: {status}")

        return True
    except Exception as e:
        print(f"✗ AutoLoginManager 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试新功能...")
    print("=" * 50)

    tests = [
        ("模块导入", test_imports),
        ("配置功能", test_config),
        ("自动登录管理器", test_auto_login_manager),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n测试 {test_name}:")
        print("-" * 30)
        if test_func():
            passed += 1
            print(f"✓ {test_name} 测试通过")
        else:
            print(f"✗ {test_name} 测试失败")

    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！新功能准备就绪。")
        return True
    else:
        print("❌ 部分测试失败，请检查代码。")
        return False

if __name__ == "__main__":
    main()
