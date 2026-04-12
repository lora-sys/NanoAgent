# Google 风格文档字符串示例

"""
模块名称

简短描述（一行）。

详细描述（可选）：
可以有多行，提供更多上下文和说明。

Examples:
    使用示例::

        >>> from core.example import ExampleClass
        >>> example = ExampleClass(param1="value")
        >>> result = example.do_something()

Attributes:
    attr1 (str): 属性 1 描述
    attr2 (int): 属性 2 描述
"""


def example_function(
    param1: str,
    param2: int,
    param3: Optional[Dict[str, Any]] = None
) -> bool:
    """函数简短描述（一行）。

    详细描述（可选）：
    提供更多关于函数功能、用途的说明。

    Args:
        param1: 参数 1 描述
        param2: 参数 2 描述
        param3: 参数 3 描述。默认为 None.

    Returns:
        返回值描述

    Raises:
        ValueError: 当 param1 为空时
        KeyError: 当 param3 中缺少必需键时

    Example:
        >>> result = example_function("value", 42)
        >>> print(result)
        True

    Note:
        注意事项或重要提示

    See Also:
        related_function: 相关函数说明
    """
    pass


class ExampleClass:
    """类简短描述。

    详细描述：
    提供类的功能、用途说明。

    Attributes:
        attr1: 属性 1 描述
        attr2: 属性 2 描述

    Example:
        >>> example = ExampleClass("value")
        >>> example.do_something()
    """

    def __init__(self, param1: str):
        """初始化 ExampleClass。

        Args:
            param1: 参数 1 描述
        """
        self.attr1 = param1
        self.attr2 = 0

    def do_something(self) -> bool:
        """方法简短描述。

        详细描述：
        说明方法的功能和用途。

        Returns:
            返回值描述

        Raises:
            RuntimeError: 当操作失败时

        Example:
            >>> example = ExampleClass("value")
            >>> example.do_something()
            True
        """
        return True
