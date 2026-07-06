"""forge_memory.context_pack 单元测试。"""

import unittest

from forge_memory.context_pack import _extract_keywords


class TestExtractKeywords(unittest.TestCase):
    def test_english_keywords(self):
        keywords = _extract_keywords("fix the login page")
        assert "login" in keywords

    def test_chinese_keywords(self):
        keywords = _extract_keywords("修改登录页面")
        assert "login" in keywords or "auth" in keywords

    def test_mixed(self):
        keywords = _extract_keywords("修改 share 功能的 bug")
        assert "share" in keywords
        assert "fix" in keywords or "bug" in keywords

    def test_empty(self):
        keywords = _extract_keywords("")
        assert keywords == []

    def test_no_duplicates(self):
        keywords = _extract_keywords("login login login")
        assert keywords.count("login") == 1


if __name__ == "__main__":
    unittest.main()
