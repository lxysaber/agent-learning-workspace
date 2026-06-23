"""read_file 工具函数的基础测试。"""

from pathlib import Path
import tempfile
import unittest

from read_file_tool import read_file


class ReadFileToolTest(unittest.TestCase):
    """验证 read_file 的成功路径和关键安全边界。"""

    def test_read_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "note.txt"
            note.write_text("hello agent", encoding="utf-8")

            result = read_file("note.txt", root_dir=root)

            self.assertTrue(result["ok"])
            self.assertEqual(result["content"], "hello agent")

    def test_reject_parent_directory_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            result = read_file("../outside.txt", root_dir=root)

            self.assertFalse(result["ok"])
            self.assertIn("超出允许目录", result["error"])

    def test_missing_file_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = read_file("missing.txt", root_dir=temp_dir)

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "文件不存在")


if __name__ == "__main__":
    unittest.main()
