"""
配置系统测试
验证配置加载和访问功能
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import ConfigManager, get_config_manager, reset_config_manager

def test_basic_loading():
    """测试基本配置加载"""
    print("🧪 测试基本配置加载...")
    
    # 重置配置管理器
    reset_config_manager()
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 检查主配置
    main_config = config.get_main_config()
    assert "general" in main_config, "主配置缺少 general 节"
    assert "modules" in main_config, "主配置缺少 modules 节"
    
    # 检查模块配置
    assert "core" in config.module_configs, "缺少 core 模块配置"
    assert "llm" in config.module_configs, "缺少 llm 模块配置"
    assert "cache" in config.module_configs, "缺少 cache 模块配置"
    
    print("✅ 基本配置加载测试通过")

def test_config_access():
    """测试配置访问"""
    print("🧪 测试配置访问...")
    
    config = get_config_manager()
    
    # 测试 get 方法
    log_level = config.get("core", "logging.level")
    assert log_level is not None, "无法获取日志级别"
    
    max_steps = config.get("core", "agent.max_steps")
    assert max_steps is not None, "无法获取 max_steps"
    
    # 测试默认值
    nonexistent = config.get("core", "nonexistent.key", "default_value")
    assert nonexistent == "default_value", "默认值功能失败"
    
    # 测试 get_module_config
    core_config = config.get_module_config("core")
    assert isinstance(core_config, dict), "get_module_config 返回类型错误"
    assert "logging" in core_config, "core 配置缺少 logging 节"
    
    print("✅ 配置访问测试通过")

def test_env_var_resolution():
    """测试环境变量解析"""
    print("🧪 测试环境变量解析...")
    
    # 设置测试环境变量
    os.environ["TEST_VAR"] = "test_value"
    
    # 创建测试配置文件
    test_config_path = Path("test_config.toml")
    test_config_path.write_text('''
[test]
value = "${TEST_VAR}"
''')
    
    config = ConfigManager()
    test_value = config._load_toml_file("test_config.toml")
    
    assert test_value["test"]["value"] == "test_value", "环境变量解析失败"
    
    # 清理
    test_config_path.unlink()
    del os.environ["TEST_VAR"]
    
    print("✅ 环境变量解析测试通过")

def test_validation():
    """测试配置验证"""
    print("🧪 测试配置验证...")
    
    config = get_config_manager()
    
    # 验证配置并断言结果
    is_valid = config.validate()
    
    # 由于我们有完整的配置，应该通过验证
    assert is_valid, "配置验证失败：配置不完整或无效"
    print("✅ 配置验证测试通过")

def test_singleton():
    """测试单例模式"""
    print("🧪 测试单例模式...")
    
    reset_config_manager()
    
    # 获取两个实例
    config1 = get_config_manager()
    config2 = get_config_manager()
    
    # 应该是同一个实例
    assert config1 is config2, "单例模式失败"
    
    print("✅ 单例模式测试通过")

def test_reload():
    """测试配置重载"""
    print("🧪 测试配置重载...")
    
    config = get_config_manager()
    
    # 获取原始配置
    original_max_steps = config.get("core", "agent.max_steps")
    
    # 重载配置
    config.reload()
    
    # 验证重载后配置仍然可用
    reloaded_max_steps = config.get("core", "agent.max_steps")
    assert reloaded_max_steps == original_max_steps, "配置重载失败"
    
    print("✅ 配置重载测试通过")

def test_missing_config():
    """测试缺失配置的处理"""
    print("🧪 测试缺失配置处理...")
    
    config = get_config_manager()
    
    # 测试获取不存在的模块
    missing_module = config.get_module_config("nonexistent_module")
    assert missing_module == {}, "缺失模块应该返回空字典"
    
    # 测试获取不存在的配置项
    missing_config = config.get("core", "nonexistent.key")
    assert missing_config is None, "缺失配置项应该返回 None"
    
    print("✅ 缺失配置处理测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 开始运行配置系统测试")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_loading,
        test_config_access,
        test_env_var_resolution,
        test_validation,
        test_singleton,
        test_reload,
        test_missing_config
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)