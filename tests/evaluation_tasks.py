"""评估任务集 - 基于 Anthropic 最佳实践的真实场景任务

遵循原则：
- 基于真实世界场景
- 多步骤工具调用
- 可验证的结果
- 不同难度级别
"""

from core.evaluation import EvaluationTask, TaskDifficulty, VerificationType


def get_evaluation_tasks() -> list:
    """获取完整的评估任务集"""
    return [
        # 基础任务 (1-2次工具调用)
        create_basic_file_reading_task(),
        create_basic_directory_listing_task(),
        create_basic_command_execution_task(),
        # 中等任务 (3-5次工具调用)
        create_project_structure_analysis_task(),
        create_code_search_task(),
        create_file_comparison_task(),
        # 高级任务 (6-10次工具调用)
        create_complex_project_analysis_task(),
        create_multi_file_documentation_task(),
        create_comprehensive_code_review_task(),
        # 专家任务 (10+次工具调用)
        create_system_audit_task(),
        create_refactoring_analysis_task(),
    ]


# ==================== 基础任务 ====================


def create_basic_file_reading_task() -> EvaluationTask:
    """基础文件读取任务"""
    return EvaluationTask(
        name="basic_file_reading",
        description="读取并分析项目 README 文件",
        prompt="读取 README.md 文件，总结项目的核心特性和快速开始方法",
        difficulty=TaskDifficulty.BASIC,
        verification_type=VerificationType.CONTAINS,
        expected_result=["特性", "快速开始", "README"],
        expected_tools=["read_file"],
        metadata={
            "category": "file_operations",
            "real_world_scenario": "开发者快速了解项目",
        },
    )


def create_basic_directory_listing_task() -> EvaluationTask:
    """基础目录列表任务"""
    return EvaluationTask(
        name="basic_directory_listing",
        description="列出项目目录结构",
        prompt="列出 examples/ 目录的所有文件，并按类型分类",
        difficulty=TaskDifficulty.BASIC,
        verification_type=VerificationType.CONTAINS,
        expected_result=["examples", "文件", "目录"],
        expected_tools=["list_files"],
        metadata={"category": "file_operations", "real_world_scenario": "项目结构探索"},
    )


def create_basic_command_execution_task() -> EvaluationTask:
    """基础命令执行任务"""
    return EvaluationTask(
        name="basic_command_execution",
        description="执行系统命令获取环境信息",
        prompt="运行命令获取当前工作目录和 Python 版本",
        difficulty=TaskDifficulty.BASIC,
        verification_type=VerificationType.CONTAINS,
        expected_result=["目录", "Python", "版本"],
        expected_tools=["run_bash"],
        metadata={"category": "system_operations", "real_world_scenario": "环境检查"},
    )


# ==================== 中等任务 ====================


def create_project_structure_analysis_task() -> EvaluationTask:
    """项目结构分析任务"""
    return EvaluationTask(
        name="project_structure_analysis",
        description="分析项目的整体结构和组织方式",
        prompt="分析 nanoagent 项目的整体结构：1) 列出所有顶级目录，2) 读取核心模块的文件，3) 总结项目的架构设计",
        difficulty=TaskDifficulty.INTERMEDIATE,
        verification_type=VerificationType.CONTAINS,
        expected_result=["core", "架构", "模块", "结构"],
        expected_tools=["list_files", "read_file"],
        metadata={
            "category": "project_analysis",
            "real_world_scenario": "新成员加入项目时的架构理解",
        },
    )


def create_code_search_task() -> EvaluationTask:
    """代码搜索任务"""
    return EvaluationTask(
        name="code_search",
        description="在项目中搜索特定代码模式",
        prompt="在 core/ 目录中搜索所有包含 'class' 定义的 Python 文件，并列出每个文件中的类名",
        difficulty=TaskDifficulty.INTERMEDIATE,
        verification_type=VerificationType.CONTAINS,
        expected_result=["class", "Python", "文件", "类名"],
        expected_tools=["list_files", "read_file"],
        metadata={
            "category": "code_analysis",
            "real_world_scenario": "代码重构前的模式搜索",
        },
    )


def create_file_comparison_task() -> EvaluationTask:
    """文件比较任务"""
    return EvaluationTask(
        name="file_comparison",
        description="比较相似文件的功能差异",
        prompt="比较 chain.py 和 chain_enhanced.py 这两个文件，分析它们的功能差异和增强特性",
        difficulty=TaskDifficulty.INTERMEDIATE,
        verification_type=VerificationType.CONTAINS,
        expected_result=["chain", "差异", "增强", "功能"],
        expected_tools=["read_file"],
        metadata={"category": "code_analysis", "real_world_scenario": "理解代码演进"},
    )


# ==================== 高级任务 ====================


def create_complex_project_analysis_task() -> EvaluationTask:
    """复杂项目分析任务"""
    return EvaluationTask(
        name="complex_project_analysis",
        description="全面分析项目的技术栈和依赖关系",
        prompt="对 nanoagent 项目进行全面分析：1) 检查 pyproject.toml 了解依赖，2) 分析 core/ 目录的所有模块，3) 检查 examples/ 了解使用方式，4) 总结项目的技术架构和设计模式",
        difficulty=TaskDifficulty.ADVANCED,
        verification_type=VerificationType.CONTAINS,
        expected_result=["依赖", "架构", "设计模式", "技术栈"],
        expected_tools=["read_file", "list_files"],
        metadata={
            "category": "project_analysis",
            "real_world_scenario": "技术选型和架构评估",
        },
    )


def create_multi_file_documentation_task() -> EvaluationTask:
    """多文件文档生成任务"""
    return EvaluationTask(
        name="multi_file_documentation",
        description="基于多个源文件生成 API 文档",
        prompt="为 core/ 目录中的主要模块生成 API 文档：1) 分析 agent.py 的公共接口，2) 分析 router.py 的路由功能，3) 分析 chain.py 的链式执行，4) 整理成结构化的文档",
        difficulty=TaskDifficulty.ADVANCED,
        verification_type=VerificationType.CONTAINS,
        expected_result=["API", "接口", "文档", "模块"],
        expected_tools=["read_file", "list_files"],
        metadata={"category": "documentation", "real_world_scenario": "自动化文档生成"},
    )


def create_comprehensive_code_review_task() -> EvaluationTask:
    """综合代码审查任务"""
    return EvaluationTask(
        name="comprehensive_code_review",
        description="对核心模块进行全面的代码审查",
        prompt="对 core/agent.py 进行代码审查：1) 检查代码质量和结构，2) 分析错误处理机制，3) 评估工具调用逻辑，4) 提供改进建议",
        difficulty=TaskDifficulty.ADVANCED,
        verification_type=VerificationType.CONTAINS,
        expected_result=["代码质量", "错误处理", "改进", "审查"],
        expected_tools=["read_file"],
        metadata={"category": "code_review", "real_world_scenario": "代码质量保证"},
    )


# ==================== 专家任务 ====================


def create_system_audit_task() -> EvaluationTask:
    """系统审计任务"""
    return EvaluationTask(
        name="system_audit",
        description="对整个项目进行全面的架构和代码审计",
        prompt="对 nanoagent 项目进行全面审计：1) 分析项目结构和模块依赖，2) 检查核心模块的实现质量，3) 评估测试覆盖范围，4) 分析工具系统的设计，5) 检查配置和文档完整性，6) 提供详细的审计报告",
        difficulty=TaskDifficulty.EXPERT,
        verification_type=VerificationType.CONTAINS,
        expected_result=["审计", "架构", "质量", "报告"],
        expected_tools=["list_files", "read_file", "run_bash"],
        metadata={"category": "system_audit", "real_world_scenario": "项目健康度检查"},
    )


def create_refactoring_analysis_task() -> EvaluationTask:
    """重构分析任务"""
    return EvaluationTask(
        name="refactoring_analysis",
        description="分析代码并提供重构建议",
        prompt="分析 nanoagent 框架的重构机会：1) 检查所有核心模块的代码质量，2) 识别重复代码和可优化的部分，3) 分析模块间的耦合度，4) 评估异步实现的效率，5) 提供具体的重构建议和优先级",
        difficulty=TaskDifficulty.EXPERT,
        verification_type=VerificationType.CONTAINS,
        expected_result=["重构", "优化", "耦合", "建议"],
        expected_tools=["list_files", "read_file"],
        metadata={"category": "refactoring", "real_world_scenario": "代码质量改进"},
    )


# ==================== 工具特定任务 ====================


def create_tool_specific_tasks() -> list:
    """创建工具特定的测试任务"""
    return [
        EvaluationTask(
            name="read_file_stress_test",
            description="测试读取多个文件的能力",
            prompt="依次读取 core/ 目录下的所有 .py 文件，并统计每个文件的行数",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["文件", "行数", "core"],
            expected_tools=["list_files", "read_file"],
        ),
        EvaluationTask(
            name="list_files_recursive_test",
            description="测试递归列出目录的能力",
            prompt="递归列出 tests/ 目录的所有文件和子目录",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["tests", "文件", "目录"],
            expected_tools=["list_files"],
        ),
        EvaluationTask(
            name="run_bash_complex_test",
            description="测试执行复杂命令的能力",
            prompt="运行命令序列：1) 检查 Git 状态，2) 列出最近3次提交，3) 统计代码行数",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["Git", "提交", "代码"],
            expected_tools=["run_bash"],
        ),
    ]


# ==================== 边界情况任务 ====================


def create_edge_case_tasks() -> list:
    """创建边界情况测试任务"""
    return [
        EvaluationTask(
            name="error_recovery_test",
            description="测试错误恢复能力",
            prompt="尝试读取一个不存在的文件，然后列出当前目录的文件作为恢复",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.TOOL_CALLS,
            expected_result=["read_file", "list_files"],
            expected_tools=["read_file", "list_files"],
        ),
        EvaluationTask(
            name="empty_directory_test",
            description="测试处理空目录的能力",
            prompt="检查 agent_workspace/ 目录的内容，如果为空则创建一个测试文件",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["目录", "文件"],
            expected_tools=["list_files"],
        ),
    ]


def get_all_evaluation_tasks() -> dict:
    """获取所有评估任务，按类别分组"""
    return {
        "basic": [
            task
            for task in get_evaluation_tasks()
            if task.difficulty == TaskDifficulty.BASIC
        ],
        "intermediate": [
            task
            for task in get_evaluation_tasks()
            if task.difficulty == TaskDifficulty.INTERMEDIATE
        ],
        "advanced": [
            task
            for task in get_evaluation_tasks()
            if task.difficulty == TaskDifficulty.ADVANCED
        ],
        "expert": [
            task
            for task in get_evaluation_tasks()
            if task.difficulty == TaskDifficulty.EXPERT
        ],
        "tool_specific": create_tool_specific_tasks(),
        "edge_cases": create_edge_case_tasks(),
    }


if __name__ == "__main__":
    # 打印所有任务的摘要
    all_tasks = get_all_evaluation_tasks()

    print("📊 评估任务集概览")
    print("=" * 80)

    for category, tasks in all_tasks.items():
        print(f"\n📁 {category.upper()} ({len(tasks)} 个任务)")
        for task in tasks:
            print(f"  - {task.name}: {task.description}")

    print(f"\n📊 总计: {sum(len(tasks) for tasks in all_tasks.values())} 个评估任务")
