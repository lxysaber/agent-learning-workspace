"""命令行入口：读取指定文件，并让 DeepSeek 总结内容。"""

from __future__ import annotations

from send_file_agent import ObsidianFileSummaryRunner


def main() -> None:
    """运行固定 Obsidian 文件总结任务。"""
    runner = ObsidianFileSummaryRunner()
    summary = runner.run()
    print(summary)


if __name__ == "__main__":
    main()
