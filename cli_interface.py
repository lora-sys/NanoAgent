"""
NanoAgent CLI 界面 - 全局实时编排器

特性：
- 全局单例模式
- 实时显示 Agent 状态
- 简洁的用户输入
- 清晰的输出展示
- 资源节省（最小化 UI 开销）
- 模块化设计
"""
import threading
from loguru import logger
from typing import Optional, Callable
from queue import Queue
import time

class CLIInterface:
    """命令行界面 - 全局实时编排器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self.input_queue = Queue()
        self.input_callback: Optional[Callable] = None
        self.is_running = False
        self._start_time = None
        self._current_step = 0
        self._total_steps = 0
        self._initialized = True
        logger.info("🖥️ CLI 实时编排器已初始化")
    
    def display_phase(self, phase: str, step: Optional[int] = None):
        """显示当前阶段"""
        if step:
            self._current_step = step
            print(f"\n{'='*60}")
            print(f"🔄 {phase} (Step {step})")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f"🔄 {phase}")
            print(f"{'='*60}\n")
    
    def display_thinking(self, content: str):
        """显示 Agent 思考过程"""
        elapsed = self._get_elapsed_time()
        print(f"💭 Thinking ({elapsed:.1f}s): {content[:100]}...")
    
    def display_action(self, action_type: str, details: str):
        """显示 Agent 执行的动作"""
        elapsed = self._get_elapsed_time()
        if action_type == "tool_call":
            print(f"\n🔧 Executing ({elapsed:.1f}s): {details}")
        elif action_type == "content":
            print(f"\n📝 Output ({elapsed:.1f}s): {details[:200]}...")
        else:
            print(f"\n📋 {details}")
    
    def display_result(self, result: str, success: bool = True):
        """显示执行结果"""
        icon = "✅" if success else "❌"
        print(f"{icon} {result}")
        print("-"*60)
    
    def _get_elapsed_time(self) -> float:
        """获取已用时间"""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0
    
    def start_timing(self):
        """开始计时"""
        self._start_time = time.time()
    
    def stop_timing(self) -> float:
        """停止计时并返回耗时"""
        if self._start_time:
            elapsed = time.time() - self._start_time
            self._start_time = None
            return elapsed
        return 0.0
    
    def display_error(self, error: str):
        """显示错误信息"""
        elapsed = self._get_elapsed_time()
        print(f"❌ Error ({elapsed:.1f}s): {error}")
        print("-"*60)
    
    def display_progress(self, current: int, total: int, message: str = ""):
        """显示进度条"""
        self._current_step = current
        self._total_steps = total
        percentage = int((current / total) * 100)
        bar_length = 20
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n[{bar}] {current}/{total} ({percentage}%) {message}")
    
    def display_question(self, question: str, options: Optional[list] = None) -> str:
        """显示问题并获取用户回答"""
        print(f"\n{'='*60}")
        print("🤔 Agent 需要你的帮助：")
        print(f"{'='*60}")
        print(f"\n问题：{question}\n")
        
        if options:
            print("可选答案：")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            print()
        
        print(f"{'='*60}\n")
        
        # 获取用户输入
        answer = input("请输入你的回答：").strip()
        
        # 如果有选项，检查是否输入了选项编号
        if options and answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(options):
                answer = options[idx]
        
        logger.info(f"用户回答：{answer[:50]}...")
        return answer
    
    def display_decision(self, analysis: str, action: str, risk: str = "low") -> str:
        """显示决策审批界面"""
        # 截断长文本
        analysis_short = analysis[:200] + "..." if len(analysis) > 200 else analysis
        action_short = action[:100] + "..." if len(action) > 100 else action
        
        print(f"\n{'='*50}")
        print("⚠️  需要人类审批的决策")
        print(f"{'='*50}")
        print(f"\n分析：{analysis_short}")
        print(f"\n建议：{action_short}")
        print(f"风险：{risk}")
        print(f"{'='*50}\n")
        
        choice = input("批准？[y/n]: ").strip().lower()
        result = "approved" if choice == 'y' else "rejected"
        
        logger.info(f"决策结果：{result}")
        return result
    
    def display_intervention(self, reason: str, current_state: str, options: Optional[list] = None) -> str:
        """显示干预请求界面"""
        print(f"\n{'='*60}")
        print("🚨 需要人类干预")
        print(f"{'='*60}")
        print(f"\n原因：{reason}")
        print(f"\n当前状态：\n{current_state[:500]}")
        
        if options:
            print("\n可能的解决方案：")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
        
        print(f"\n{'='*60}")
        
        # 获取人类纠正
        print("\n请提供纠正或指导：")
        correction = input("> ").strip()
        
        logger.info(f"人类干预已提供：{correction[:50]}...")
        return correction
    
    def display_escalation(self, reason: str, level: str, context: str) -> str:
        """显示升级策略界面"""
        # 根据级别显示不同警示
        if level == "critical":
            icon = "🚨"
            alert = "CRITICAL - 需要立即处理"
        elif level == "warning":
            icon = "⚠️"
            alert = "WARNING - 需要注意"
        else:
            icon = "ℹ️"
            alert = "INFO - 仅供参考"
        
        print(f"\n{'='*60}")
        print(f"{icon} Agent 任务升级 - {alert}")
        print(f"{'='*60}")
        print(f"\n原因：{reason}")
        print(f"\n上下文：\n{context[:500]}")
        print(f"\n{'='*60}\n")
        
        # 获取人类处理
        human_action = input("请提供解决方案或指导：").strip()
        
        logger.info(f"任务已升级（级别={level}）：{reason[:50]}...")
        return human_action
    
    def display_completion(self, summary: str):
        """显示任务完成界面"""
        elapsed = self.stop_timing()
        print(f"\n{'='*60}")
        print("🎉 任务完成")
        print(f"{'='*60}")
        print(f"\n{summary}")
        print(f"\n⏱️ 总耗时：{elapsed:.1f}秒")
        print(f"📊 步骤数：{self._current_step}")
        print(f"{'='*60}\n")
    
    def display_monitor(self, action: str, step_id: str, output: str, context: Optional[str] = None) -> str:
        """显示监控界面"""
        if action == "log_review":
            print(f"\n{'='*60}")
            print(f"📋 日志审查请求 - 步骤 {step_id}")
            print(f"{'='*60}")
            print(f"输出：\n{output[:500]}")
            if context:
                print(f"\n上下文：\n{context[:300]}")
            print(f"\n{'='*60}")
            
            feedback = input("是否需要干预？[y/n]: ").strip().lower()
            return "intervention_requested" if feedback == 'y' else "continue"
        elif action == "realtime_check":
            print(f"\n⚡ 实时监控 - 步骤 {step_id}")
            print(f"输出长度：{len(output)} 字符")
            return "monitored"
        else:
            return f"Unknown action: {action}"
    
    def display_feedback(self, feedback_type: str, step_id: str, content: str, question: Optional[str] = None) -> str:
        """显示反馈收集界面"""
        print(f"\n{'='*60}")
        print(f"📝 收集人类反馈 - {feedback_type.upper()}")
        print(f"{'='*60}")
        print(f"\n步骤：{step_id}")
        print(f"\n内容：\n{content[:400]}")
        
        if question:
            print(f"\n问题：{question}")
        
        print(f"\n{'='*60}\n")
        
        # 获取反馈
        user_feedback = input("请提供反馈：").strip()
        
        logger.info(f"反馈已收集（类型={feedback_type}）：{user_feedback[:50]}...")
        return user_feedback
    
    def display_header(self):
        """显示系统头部信息"""
        print("="*70)
        print("NanoAgent - 智能任务执行系统")
        print("="*70)
        print()
        self.start_timing()
    
    def display_footer(self):
        """显示系统尾部信息"""
        elapsed = self.stop_timing()
        print()
        print("="*70)
        print(f"✅ 执行完成 - 耗时：{elapsed:.1f}秒")
        print("="*70)
        print()
        print("💡 提示：")
        print("  - 查看 agent_workspace/ 目录查看生成的文件")
        print("  - 查看 nanoagent.log 获取详细日志")
        print("  - 查看 agent_workspace/human_feedback.jsonl 查看反馈记录")
        print()


# 全局 CLI 实例
_cli_instance: Optional[CLIInterface] = None

def get_cli() -> CLIInterface:
    """获取全局 CLI 实例（单例模式）"""
    global _cli_instance
    if _cli_instance is None:
        _cli_instance = CLIInterface()
    return _cli_instance

def set_cli_interface(cli: CLIInterface):
    """设置全局 CLI 实例（用于测试或自定义）"""
    global _cli_instance
    _cli_instance = cli
