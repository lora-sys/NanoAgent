"""NanoAgent CLI 界面"""

import os
import sys
import time
from loguru import logger
from typing import Optional

# 终端颜色检测
def _supports_color() -> bool:
    """检测终端是否支持颜色"""
    # 检查NO_COLOR环境变量
    if os.environ.get('NO_COLOR'):
        return False
    
    # 检查是否在TTY中
    if not sys.stdout.isatty():
        return False
    
    # 检查TERM环境变量
    term = os.environ.get('TERM', '')
    if term in ('dumb', 'emacs'):
        return False
    
    # 检查COLORTERM
    if os.environ.get('COLORTERM'):
        return True
    
    # 常见的支持颜色的TERM值
    color_terms = ['xterm', 'xterm-256color', 'vt100', 'vt220', 'linux', 'screen', 
                   'tmux', 'tmux-256color', 'rxvt', 'rxvt-unicode', 'gnome-terminal']
    return any(term.startswith(t) for t in color_terms)

# 根据终端支持情况设置颜色常量
if _supports_color():
    YOU_COLOR = "\033[94m"      # 蓝色 - 用户输入
    ASSISTANT_COLOR = "\033[92m" # 绿色 - AI助手输出
    SYSTEM_COLOR = "\033[96m"    # 青色 - 系统消息
    TOOL_COLOR = "\033[93m"      # 黄色 - 工具调用
    ERROR_COLOR = "\033[91m"     # 红色 - 错误消息
    SUCCESS_COLOR = "\033[92m"   # 绿色 - 成功消息
    WARNING_COLOR = "\033[93m"   # 黄色 - 警告消息
    RESET_COLOR = "\033[0m"      # 重置颜色
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
else:
    # 不支持颜色时使用空字符串
    YOU_COLOR = ASSISTANT_COLOR = SYSTEM_COLOR = ""
    TOOL_COLOR = ERROR_COLOR = SUCCESS_COLOR = WARNING_COLOR = ""
    RESET_COLOR = BOLD = UNDERLINE = ""


def _fingerprint(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()[:16]


class CLIInterface:
    """命令行界面"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._start_time = None
        self._current_step = 0
        self._initialized = True

    def _is_interactive(self) -> bool:
        """检测是否在交互模式"""
        return sys.stdin.isatty() and not os.environ.get("NANOAGENT_TEST")

    def display_phase(self, phase: str, step: Optional[int] = None):
        if step:
            self._current_step = step
            print(f"\n{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}\n{SYSTEM_COLOR}🔄 {phase} (Step {step}){RESET_COLOR}\n{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}\n")
        else:
            print(f"\n{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}\n{SYSTEM_COLOR}🔄 {phase}{RESET_COLOR}\n{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}\n")

    def display_thinking(self, content: str):
        print(f"{ASSISTANT_COLOR}💭 Thinking ({self._elapsed():.1f}s): {content[:100]}...{RESET_COLOR}")

    def display_action(self, action_type: str, details: str):
        if action_type == "tool_call":
            print(f"\n{TOOL_COLOR}🔧 Executing ({self._elapsed():.1f}s): {details}{RESET_COLOR}")
        elif action_type == "content":
            print(f"\n{ASSISTANT_COLOR}📝 Output ({self._elapsed():.1f}s): {details[:200]}...{RESET_COLOR}")
        else:
            print(f"\n{SYSTEM_COLOR}📋 {details}{RESET_COLOR}")

    def display_result(self, result: str, success: bool = True):
        icon = "✅" if success else "❌"
        color = SUCCESS_COLOR if success else ERROR_COLOR
        print(f"{color}{icon} {result}{RESET_COLOR}\n{'-' * 60}")

    def display_error(self, error: str):
        print(f"{ERROR_COLOR}❌ Error ({self._elapsed():.1f}s): {error}{RESET_COLOR}\n{'-' * 60}")

    def display_progress(self, current: int, total: int, message: str = ""):
        self._current_step = current
        pct = int((current / max(total, 1)) * 100)
        filled = int(20 * current / max(total, 1))
        bar = "█" * filled + "░" * (20 - filled)
        print(f"\n{SYSTEM_COLOR}[{bar}] {current}/{total} ({pct}%) {message}{RESET_COLOR}")

    def display_question(self, question: str, options: Optional[list] = None) -> str:
        if not self._is_interactive():
            logger.info(f"非交互模式，跳过用户提问: {question}")
            return "继续执行"
        print(f"\n{YOU_COLOR}{'=' * 60}{RESET_COLOR}")
        print(f"{YOU_COLOR}🤔 Agent 需要你的帮助：{RESET_COLOR}")
        print(f"{YOU_COLOR}{'=' * 60}{RESET_COLOR}\n\n{YOU_COLOR}问题：{question}{RESET_COLOR}\n")
        if options:
            print(f"{SYSTEM_COLOR}可选答案：{RESET_COLOR}")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
        print(f"\n{YOU_COLOR}{'=' * 60}{RESET_COLOR}\n")
        answer = input(f"{YOU_COLOR}请输入你的回答：{RESET_COLOR}").strip()
        if options and answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(options):
                answer = options[idx]
        logger.info(f"用户回答：长度={len(answer)}, 指纹={_fingerprint(answer)}")
        return answer

    def print_dashboard(self, stage_name, step_info, artifacts, last_action):
        print(f"\n{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}")
        print(f" {SYSTEM_COLOR}🚀 当前阶段: {stage_name:<15} │ ⏱️ 耗时: {self._elapsed():.1f}s{RESET_COLOR}")
        print(f" {SYSTEM_COLOR}📍 步骤信息: {step_info}{RESET_COLOR}")
        print(f"{SYSTEM_COLOR}{'-' * 60}{RESET_COLOR}")
        if artifacts:
            print(f" {SYSTEM_COLOR}📂 已创建文件:{RESET_COLOR}")
            for f in artifacts[-5:]:
                print(f"    {TOOL_COLOR}• {f}{RESET_COLOR}")
        print(f" {TOOL_COLOR}🔧 最近动作: {last_action[:50]}...{RESET_COLOR}")
        print(f"{SYSTEM_COLOR}{'=' * 60}{RESET_COLOR}\n")

    def display_completion(self, summary: str):
        elapsed = self.stop_timing()
        print(f"\n{SUCCESS_COLOR}{'=' * 60}{RESET_COLOR}")
        print(f"{SUCCESS_COLOR}🎉 任务完成{RESET_COLOR}")
        print(f"{SUCCESS_COLOR}{'=' * 60}{RESET_COLOR}\n\n{ASSISTANT_COLOR}{summary}{RESET_COLOR}")
        print(f"\n{SYSTEM_COLOR}⏱️ 总耗时：{elapsed:.1f}秒{RESET_COLOR}")
        print(f"{SYSTEM_COLOR}📊 步骤数：{self._current_step}{RESET_COLOR}")
        print(f"{SUCCESS_COLOR}{'=' * 60}{RESET_COLOR}\n")

    def display_header(self):
        print(f"{BOLD}{SYSTEM_COLOR}{'=' * 70}{RESET_COLOR}")
        print(f"{BOLD}{SYSTEM_COLOR}NanoAgent - 智能任务执行系统{RESET_COLOR}")
        print(f"{BOLD}{SYSTEM_COLOR}{'=' * 70}{RESET_COLOR}")
        self.start_timing()

    def display_footer(self):
        elapsed = self.stop_timing()
        print(f"\n{SUCCESS_COLOR}{'=' * 70}{RESET_COLOR}")
        print(f"{SUCCESS_COLOR}✅ 执行完成 - 耗时：{elapsed:.1f}秒{RESET_COLOR}")
        print(f"{SUCCESS_COLOR}{'=' * 70}{RESET_COLOR}")

    def start_timing(self):
        self._start_time = time.time()

    def stop_timing(self) -> float:
        if self._start_time:
            e = time.time() - self._start_time
            self._start_time = None
            return e
        return 0.0

    def _elapsed(self) -> float:
        return time.time() - self._start_time if self._start_time else 0.0


_cli_instance: Optional[CLIInterface] = None


def get_cli() -> CLIInterface:
    global _cli_instance
    if _cli_instance is None:
        _cli_instance = CLIInterface()
    return _cli_instance
