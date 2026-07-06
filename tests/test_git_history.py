"""forge_memory.git_history 单元测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from forge_memory.git_history import append_new_commits, load_existing_commits


class TestLoadExistingCommits(unittest.TestCase):
    def test_empty(self):
        with tempfile.TemporaryDirectory() as td:
            result = load_existing_commits(Path(td))
            assert result == []

    def test_with_data(self):
        with tempfile.TemporaryDirectory() as td:
            index_dir = Path(td) / "index"
            index_dir.mkdir()
            commits_file = index_dir / "commits.jsonl"
            commits_file.write_text(
                '{"hash": "abc", "short_hash": "abc", "author": "test", "date": "2026-01-01", "message": "init"}\n',
                encoding="utf-8",
            )
            result = load_existing_commits(Path(td))
            assert len(result) == 1
            assert result[0]["hash"] == "abc"


class TestAppendNewCommits(unittest.TestCase):
    def test_append_new(self):
        with tempfile.TemporaryDirectory() as td:
            context = Path(td)
            (context / "index").mkdir()

            commits = [
                {"hash": "aaa", "short_hash": "aaa", "author": "a", "date": "2026-01-01", "message": "first"},
                {"hash": "bbb", "short_hash": "bbb", "author": "b", "date": "2026-01-02", "message": "second"},
            ]
            commit_files = [
                {"commit_hash": "aaa", "file_path": "a.dart", "change_type": "modified"},
                {"commit_hash": "bbb", "file_path": "b.dart", "change_type": "modified"},
            ]

            count = append_new_commits(context, commits, commit_files)
            assert count == 2

            stored = load_existing_commits(context)
            assert len(stored) == 2

    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            context = Path(td)
            (context / "index").mkdir()

            commits = [{"hash": "aaa", "short_hash": "aaa", "author": "a", "date": "2026-01-01", "message": "first"}]
            commit_files = []

            append_new_commits(context, commits, commit_files)
            count = append_new_commits(context, commits, commit_files)
            assert count == 0

            stored = load_existing_commits(context)
            assert len(stored) == 1


if __name__ == "__main__":
    unittest.main()
