"""FileSummaryAgent 的基础测试，使用 mock client 避免真实 API 请求。"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from send_file_agent import FileSummaryAgent, MODEL, ObsidianFileSummaryRunner


def make_mock_client(summary: str = "这是模拟总结。") -> Mock:
    """创建一个符合 OpenAI SDK 调用链形状的 mock client。"""
    message = Mock(content=summary)
    choice = Mock(message=message)
    response = Mock(choices=[choice])

    client = Mock()
    client.chat.completions.create.return_value = response
    return client


class FileSummaryAgentTest(unittest.TestCase):
    """验证 Agent 会先读文件，再把文件内容发送给 DeepSeek 客户端。"""

    def test_summarize_file_sends_content_to_deepseek(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "note.txt"
            note.write_text("Agent 工具函数负责读取文件。", encoding="utf-8")
            client = make_mock_client()
            agent = FileSummaryAgent(client=client, root_dir=root)

            summary = agent.summarize_file("note.txt")

            self.assertEqual(summary, "这是模拟总结。")
            client.chat.completions.create.assert_called_once()

            request = client.chat.completions.create.call_args.kwargs
            self.assertEqual(request["model"], MODEL)
            self.assertFalse(request["stream"])
            self.assertIn("Agent 工具函数负责读取文件。", request["messages"][1]["content"])

    def test_read_file_error_stops_before_api_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = make_mock_client()
            agent = FileSummaryAgent(client=client, root_dir=temp_dir)

            with self.assertRaises(ValueError) as context:
                agent.summarize_file("missing.txt")

            self.assertIn("读取文件失败", str(context.exception))
            client.chat.completions.create.assert_not_called()

    def test_runner_reads_absolute_target_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            note = root / "obsidian-note.md"
            note.write_text("这是一篇 Obsidian 笔记。", encoding="utf-8")
            client = make_mock_client("运行类总结结果。")
            runner = ObsidianFileSummaryRunner(target_file=note, client=client)

            summary = runner.run()

            self.assertEqual(summary, "运行类总结结果。")
            request = client.chat.completions.create.call_args.kwargs
            self.assertIn("这是一篇 Obsidian 笔记。", request["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
