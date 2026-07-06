"""forge_memory.utils 单元测试。"""

import unittest
from pathlib import Path

from forge_memory.scanner import classify_file, module_key
from forge_memory.utils import (
    branch_context_path,
    content_hash,
    sanitize_branch_name,
    slugify,
    stable_id,
)


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("foo/bar.baz") == "foo-bar-baz"

    def test_empty(self):
        assert slugify("") == "item"

    def test_consecutive_dashes(self):
        assert slugify("a---b") == "a-b"


class TestStableId(unittest.TestCase):
    def test_deterministic(self):
        a = stable_id("file", "src/main.ts", "main.ts")
        b = stable_id("file", "src/main.ts", "main.ts")
        assert a == b

    def test_format(self):
        sid = stable_id("mod", "src/agent", "agent")
        assert sid.startswith("mod-")
        assert len(sid) > 10


class TestClassifyFile(unittest.TestCase):
    def test_source(self):
        assert classify_file(Path("lib/main.dart")) == "source"

    def test_test(self):
        assert classify_file(Path("test/main_test.dart")) == "test"

    def test_config(self):
        assert classify_file(Path("package.json")) == "config"

    def test_document(self):
        assert classify_file(Path("README.md")) == "document"

    def test_other(self):
        assert classify_file(Path("image.png")) == "other"


class TestModuleKey(unittest.TestCase):
    def test_nested(self):
        assert module_key("lib/pages/home.dart") == "lib/pages"

    def test_root(self):
        assert module_key("main.dart") == "."


class TestContentHash(unittest.TestCase):
    def test_deterministic(self):
        h1 = content_hash(b"hello")
        h2 = content_hash(b"hello")
        assert h1 == h2

    def test_different(self):
        h1 = content_hash(b"hello")
        h2 = content_hash(b"world")
        assert h1 != h2


class TestSanitizeBranchName(unittest.TestCase):
    def test_slash(self):
        assert sanitize_branch_name("feature/fix") == "feature_fix"

    def test_long(self):
        result = sanitize_branch_name("a" * 100)
        assert len(result) == 64

    def test_empty(self):
        assert sanitize_branch_name("") == "unknown"


class TestBranchContextPath(unittest.TestCase):
    def test_path(self):
        root = Path("/tmp/project")
        p = branch_context_path(root, "main")
        assert str(p) == "/tmp/project/.project-context/branches/main"

    def test_with_slash(self):
        root = Path("/tmp/project")
        p = branch_context_path(root, "feature/fix")
        assert "feature_fix" in str(p)


if __name__ == "__main__":
    unittest.main()
