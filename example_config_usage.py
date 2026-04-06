"""
配置系统使用示例
演示如何使用新的 TOML 配置系统
"""
from core.config import get_config_manager

def example_basic_usage():
    """基本配置使用示例"""
    print("=" * 60)
    print("🔧 配置系统使用示例")
    print("=" * 60)
    
    # 获取配置管理器实例
    config = get_config_manager()
    
    # 获取主配置
    main_config = config.get_main_config()
    print(f"📋 主配置: {main_config['general']['version']}")
    
    # 获取模块配置
    core_config = config.get_module_config("core")
    print(f"⚙️  核心配置: max_steps={core_config['agent']['max_steps']}")
    
    # 获取嵌套配置项
    log_level = config.get("core", "logging.level", "INFO")
    print(f"📝 日志级别: {log_level}")
    
    # LLM 配置
    llm_config = config.get_module_config("llm")
    provider = llm_config["provider"]["name"]
    model = llm_config["clients"]["openai"]["model"]
    print(f"🤖 LLM: {provider}/{model}")
    
    # 缓存配置
    cache_ttl = config.get("cache", "storage.default_ttl_hours", 24)
    print(f"💾 缓存TTL: {cache_ttl} 小时")
    
    print()

def example_env_vars():
    """环境变量替换示例"""
    print("=" * 60)
    print("🔑 环境变量替换")
    print("=" * 60)
    
    config = get_config_manager()
    
    # 获取包含环境变量的配置
    llm_config = config.get_module_config("llm")
    api_key = llm_config["clients"]["openai"]["api_key"]
    
    print(f"🔑 API Key: {api_key}")
    print(f"📝 如果设置了 OPENAI_API_KEY 环境变量，会被替换")
    print(f"📝 否则保持原始值: {api_key}")
    print()

def example_validation():
    """配置验证示例"""
    print("=" * 60)
    print("✅ 配置验证")
    print("=" * 60)
    
    config = get_config_manager()
    
    # 验证配置
    is_valid = config.validate()
    
    if is_valid:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败，请检查配置文件")
    
    print()

def example_theme_config():
    """主题配置示例"""
    print("=" * 60)
    print("🎨 主题配置")
    print("=" * 60)
    
    config = get_config_manager()
    theme_config = config.get_module_config("theme")
    
    print(f"🖼️  UI 设置:")
    print(f"   - Emoji: {theme_config['ui']['emoji']}")
    print(f"   - 颜色: {theme_config['ui']['color']}")
    print(f"   - ASCII Art: {theme_config['ui']['ascii_art']}")
    
    print(f"\n📊 显示设置:")
    print(f"   - 最大行长度: {theme_config['display']['max_line_length']}")
    print(f"   - 截断长度: {theme_config['display']['truncate_length']}")
    
    print(f"\n🌈 颜色配置:")
    colors = theme_config['colors']
    print(f"   - 成功: {colors['success']}")
    print(f"   - 错误: {colors['error']}")
    print(f"   - 警告: {colors['warning']}")
    
    print()

def example_executor_config():
    """执行器配置示例"""
    print("=" * 60)
    print("⚡ 执行器配置")
    print("=" * 60)
    
    config = get_config_manager()
    executor_config = config.get_module_config("executor")
    
    print(f"📋 阶段配置:")
    for phase_name, phase_config in executor_config["phases"].items():
        enabled = phase_config["enabled"]
        timeout = phase_config["timeout"]
        print(f"   - {phase_name}: enabled={enabled}, timeout={timeout}s")
    
    print(f"\n🎯 完成检测:")
    completion = executor_config["completion"]
    print(f"   - 自动检测: {completion['auto_detection']}")
    print(f"   - 用户确认: {completion['user_confirmation']}")
    print(f"   - 完成阈值: {completion['completion_threshold']}")
    
    print()

def example_reload():
    """配置重载示例"""
    print("=" * 60)
    print("🔄 配置重载")
    print("=" * 60)
    
    config = get_config_manager()
    
    print("📝 修改配置文件后，调用 reload() 重新加载")
    print("   config.reload()")
    print()
    
    # 实际使用时：
    # 1. 修改配置文件
    # 2. 调用 config.reload()
    # 3. 新配置生效

def main():
    """运行所有示例"""
    try:
        example_basic_usage()
        example_env_vars()
        example_validation()
        example_theme_config()
        example_executor_config()
        example_reload()
        
        print("=" * 60)
        print("✅ 所有示例运行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()