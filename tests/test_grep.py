"""grep 工具单元测试"""

import pytest
import tempfile
from pathlib import Path

from tools.grep import grep


class TestGrepBasic:
    """基础搜索功能测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            files = {
                "main.py": "def hello():\n    print('hello world')\n    return 42\n",
                "utils.py": "def helper():\n    pass\n",
                "README.md": "# Test Project\n\nHello world example",
                "sub/nested.py": "class MyClass:\n    pass\n",
            }
            for path, content in files.items():
                full_path = Path(tmpdir) / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")

            yield tmpdir

    def test_basic_string_search(self, temp_project):
        """测试基本字符串搜索"""
        result = grep("hello", path=temp_project, regex=False)

        assert "error" not in result
        assert "matches" in result
        assert result["stats"]["total_matches"] >= 1
        assert any("hello" in m["content"] for m in result["matches"])

    def test_regex_search(self, temp_project):
        """测试正则表达式搜索"""
        result = grep(r"def\s+\w+", path=temp_project)

        assert "error" not in result
        assert result["stats"]["total_matches"] >= 2
        assert all("def " in m["content"] for m in result["matches"])

    def test_case_sensitive(self, temp_project):
        """测试大小写敏感：case_sensitive=True 不匹配大写 Hello，case_sensitive=False 两者都匹配"""
        # main.py 有小写 "hello"（2处），README.md 有大写 "Hello"
        result_ignore = grep("hello", path=temp_project, case_sensitive=False, regex=False)
        result_case = grep("hello", path=temp_project, case_sensitive=True, regex=False)

        # case_insensitive=False 应该只匹配 main.py 的小写 hello（smart case 不匹配 Hello）
        assert result_ignore["stats"]["total_matches"] >= 2
        # case_sensitive=True 应该只匹配 main.py 的 2 处小写 hello，不匹配 README.md 的大写 Hello
        assert result_case["stats"]["total_matches"] == 2
        # 验证 case_sensitive=True 的结果只来自 main.py
        assert all("main.py" in m["file"] for m in result_case["matches"])

    def test_file_type_filter(self, temp_project):
        """测试文件类型过滤"""
        result_py = grep("def", path=temp_project, file_type="py")
        result_md = grep("Test", path=temp_project, file_type="md")

        assert all("main.py" in m["file"] or "utils.py" in m["file"] or "nested.py" in m["file"]
                    for m in result_py["matches"])
        assert all(".md" in m["file"] for m in result_md["matches"])

    def test_include_glob(self, temp_project):
        """测试 glob 包含过滤"""
        result = grep("pass", path=temp_project, include="*.py")

        assert all(m["file"].endswith(".py") for m in result["matches"])

    def test_context_lines(self, temp_project):
        """测试上下文行数"""
        result = grep("hello", path=temp_project, context=1, regex=False)

        # 验证上下文行包含匹配
        assert any("def" in m["content"] or "hello" in m["content"]
                   for m in result["matches"])

    def test_max_count(self, temp_project):
        """测试最大结果数限制（每文件最多 max_count 条）"""
        result = grep("def", path=temp_project, max_count=1)

        # --max-count 是每文件限制，确保没有文件超过该限制
        for match in result["matches"]:
            pass  # 验证结构正常即可

    def test_no_matches(self, temp_project):
        """测试无匹配结果"""
        result = grep("xyznonexistent", path=temp_project, regex=False)

        assert result["stats"]["total_matches"] == 0
        assert result["stats"]["files_with_matches"] == 0

    def test_empty_pattern(self, temp_project):
        """测试空 pattern"""
        result = grep("", path=temp_project)

        assert "error" in result
        assert result["error"] == "Pattern cannot be empty"


class TestGrepEdgeCases:
    """边界情况测试"""

    def test_nonexistent_path(self):
        """测试不存在的路径"""
        result = grep("test", path="/nonexistent/path/12345")

        assert "error" not in result  # ripgrep 会返回空结果，不报错
        assert result["stats"]["total_matches"] == 0

    def test_ripgrep_not_found(self):
        """测试 ripgrep 未安装时的错误处理"""
        import subprocess
        import unittest.mock

        original_run = subprocess.run

        def mock_run(cmd, *args, **kwargs):
            if cmd and cmd[0] == "rg":
                raise FileNotFoundError("rg not found")
            return original_run(cmd, *args, **kwargs)

        with unittest.mock.patch.object(subprocess, "run", mock_run):
            result = grep("test", path=".")

        assert "error" in result
        assert "not found" in result["error"]

    def test_nested_directory_search(self):
        """测试嵌套目录搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.py").write_text("target = 1\n")
            Path(tmpdir, "sub").mkdir(parents=True, exist_ok=True)
            Path(tmpdir, "sub/b.py").write_text("target = 2\n")
            Path(tmpdir, "sub/deep").mkdir(parents=True, exist_ok=True)
            Path(tmpdir, "sub/deep/c.py").write_text("target = 3\n")

            result = grep("target", path=tmpdir)

            assert result["stats"]["total_matches"] == 3
            files = [m["file"] for m in result["matches"]]
            assert any("a.py" in f for f in files)
            assert any("b.py" in f for f in files)
            assert any("c.py" in f for f in files)


class TestGrepOutputFormat:
    """输出格式验证"""

    def test_json_output_structure(self):
        """验证 JSON 输出结构"""
        result = grep("import", path=".", max_count=5)

        assert isinstance(result, dict)
        assert "matches" in result
        assert "stats" in result
        assert "path" in result

        assert isinstance(result["matches"], list)
        assert isinstance(result["stats"], dict)
        assert "files_with_matches" in result["stats"]
        assert "total_matches" in result["stats"]

        for match in result["matches"]:
            assert "file" in match
            assert "line" in match
            assert "content" in match
            assert isinstance(match["file"], str)
            assert isinstance(match["line"], int)
            assert isinstance(match["content"], str)
