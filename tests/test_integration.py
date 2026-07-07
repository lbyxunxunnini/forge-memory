"""集成测试：端到端工作流测试。"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path


class TestIntegration(unittest.TestCase):
    """端到端工作流测试。"""

    def setUp(self):
        """创建临时项目目录。"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.tmp_dir / "test-project"
        self.project_dir.mkdir()

        # 创建一些测试文件
        (self.project_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (self.project_dir / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")
        (self.project_dir / "README.md").write_text("# Test Project\n", encoding="utf-8")

        # 创建子目录
        src_dir = self.project_dir / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("class App: pass\n", encoding="utf-8")

    def tearDown(self):
        """清理临时目录。"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_full_workflow(self):
        """测试完整工作流：init → scan → status → context → impact → import-db。"""
        from forge_memory.init import initialize
        from forge_memory.scanner import migrate_to_branch_structure, scan
        from forge_memory.indexer import read_existing_index, write_index, write_scan_summary
        from forge_memory.grapher import write_graph
        from forge_memory.context_pack import generate_context_pack
        from forge_memory.impact import analyze_impact
        from forge_memory.sqlite_backend import import_jsonl_to_sqlite
        from forge_memory.status import get_status
        from forge_memory.utils import branch_context_path

        # 1. 初始化
        created = initialize(self.project_dir, allow_empty_root=True)
        self.assertTrue((self.project_dir / ".project-context" / "context.json").exists())

        # 2. 扫描
        branch = migrate_to_branch_structure(self.project_dir)
        branch_dir = branch_context_path(self.project_dir, branch)
        result = scan(self.project_dir)
        write_index(self.project_dir, result, branch_dir)
        write_scan_summary(self.project_dir, result, branch_dir)
        write_graph(self.project_dir, result, branch_dir)

        self.assertGreater(len(result["files"]), 0)
        self.assertGreater(len(result["nodes"]), 0)

        # 3. 状态查询
        status = get_status(self.project_dir)
        self.assertNotEqual(status.get("status"), "未扫描")
        self.assertGreater(status.get("file_count", 0), 0)

        # 4. 上下文包生成
        context_pack = generate_context_pack(self.project_dir, "测试任务")
        self.assertIn("Forge Memory Context Pack", context_pack)
        self.assertIn("测试任务", context_pack)

        # 5. 影响分析
        files = result["files"]
        if files:
            test_file = files[0]["path"]
            impact = analyze_impact(self.project_dir, test_file, branch_dir)
            self.assertIn("direct_importers", impact)

        # 6. SQLite 导入
        db_path, counts = import_jsonl_to_sqlite(branch_dir, branch)
        self.assertTrue(Path(db_path).exists())
        self.assertGreater(counts.get("files", 0), 0)

    def test_error_handling(self):
        """测试错误处理。"""
        from forge_memory.init import initialize
        from forge_memory.utils import format_error, GitError

        # 测试错误格式化
        error_msg = format_error("GitError", "未检测到 git 仓库", "请先运行 git init")
        self.assertIn("[GitError]", error_msg)
        self.assertIn("请先运行 git init", error_msg)

        # 测试异常类
        with self.assertRaises(GitError):
            raise GitError("仓库为空", "请先提交一个 commit")


if __name__ == "__main__":
    unittest.main()
