"""forge_memory.impact 单元测试。"""

import unittest

from forge_memory.impact import _import_matches_file, target_path_stem


class TestTargetPathStem(unittest.TestCase):
    def test_dart(self):
        assert target_path_stem("lib/foo/bar.dart") == "lib/foo/bar"

    def test_ts(self):
        assert target_path_stem("src/main.ts") == "src/main"

    def test_no_ext(self):
        assert target_path_stem("Makefile") == "Makefile"


class TestImportMatchesFile(unittest.TestCase):
    def test_dart_package_import(self):
        imp = "package:facesong_flutter/common/utils/share_util.dart"
        file_path = "lib/common/utils/share_util.dart"
        file_stem = "lib/common/utils/share_util"
        assert _import_matches_file(imp, file_path, file_stem) is True

    def test_dart_package_no_match(self):
        imp = "package:facesong_flutter/common/utils/platform_util.dart"
        file_path = "lib/common/utils/share_util.dart"
        file_stem = "lib/common/utils/share_util"
        assert _import_matches_file(imp, file_path, file_stem) is False

    def test_relative_import(self):
        imp = "../utils/share_util.dart"
        file_path = "lib/common/utils/share_util.dart"
        file_stem = "lib/common/utils/share_util"
        assert _import_matches_file(imp, file_path, file_stem) is True

    def test_relative_import_no_match(self):
        imp = "../utils/platform_util.dart"
        file_path = "lib/common/utils/share_util.dart"
        file_stem = "lib/common/utils/share_util"
        assert _import_matches_file(imp, file_path, file_stem) is False

    def test_empty_stem(self):
        assert _import_matches_file("anything", ".env", "") is False

    def test_dart_core_import(self):
        imp = "dart:io"
        file_path = "lib/common/utils/share_util.dart"
        file_stem = "lib/common/utils/share_util"
        assert _import_matches_file(imp, file_path, file_stem) is False


if __name__ == "__main__":
    unittest.main()
