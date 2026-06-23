"""只负责读取文件并发送给 DeepSeek 总结的最小 Agent。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI


MODEL = "deepseek-v4-flash"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
READ_FILE_AGENT_DIR = PROJECT_ROOT / "01-read-file-agent"
DEFAULT_OBSIDIAN_FILE = Path(
    "/Users/shitou/WWWLLL/obsidian-workspace/obsidian-workspace/"
    "00-收件箱/01-anthropic-sdk-json-output.md"
)

# 01-read-file-agent 目录名不是合法 Python 包名，所以先加入模块搜索路径。
if str(READ_FILE_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(READ_FILE_AGENT_DIR))

from read_file_tool import read_file  # noqa: E402


def create_client() -> OpenAI:
    """创建 DeepSeek 官方 OpenAI 兼容客户端，密钥只从环境变量读取。"""
    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


class FileSummaryAgent:
    """一个只有单一职责的 Agent：读取文件，然后请求 DeepSeek 总结。"""

    def __init__(
        self,
        *,
        client: Any | None = None,
        root_dir: str | Path = PROJECT_ROOT,
        model: str = MODEL,
    ) -> None:
        """初始化 Agent，可传入 mock client 方便测试时避免真实 API 请求。"""
        self._client = client
        self.root_dir = Path(root_dir)
        self.model = model

    @property
    def client(self) -> Any:
        """延迟创建客户端，确保只有真正请求模型时才读取 API Key。"""
        if self._client is None:
            self._client = create_client()
        return self._client

    def summarize_file(self, file_path: str) -> str:
        """调用 read_file 工具读取文件，再把内容发送给 DeepSeek 总结。"""
        tool_result = read_file(file_path, root_dir=self.root_dir)

        if not tool_result["ok"]:
            raise ValueError(f"读取文件失败: {tool_result['error']}")

        content = tool_result["content"]
        if not content:
            raise ValueError("文件内容为空，无法总结")

        return self._summarize_content(
            file_path=str(tool_result["path"]),
            content=content,
            truncated=bool(tool_result["truncated"]),
        )

    def _summarize_content(
        self,
        *,
        file_path: str,
        content: str,
        truncated: bool,
    ) -> str:
        """把文件内容包装成提示词，并调用 DeepSeek Chat Completions。"""
        truncation_note = (
            "注意：文件内容因为过长已经被截断，请只总结已提供的部分。"
            if truncated
            else "文件内容完整。"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个文件内容总结助手。"
                        "请只根据用户提供的文件内容总结，不要编造文件中没有的信息。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"文件路径：{file_path}\n"
                        f"{truncation_note}\n\n"
                        "请用中文总结下面文件的主要内容，并列出 3 个以内的要点：\n\n"
                        f"{content}"
                    ),
                },
            ],
            stream=False,
        )

        summary = response.choices[0].message.content
        if not summary:
            raise ValueError("DeepSeek 返回了空内容")

        return summary


def summarize_file(file_path: str, *, root_dir: str | Path = PROJECT_ROOT) -> str:
    """函数式入口：创建 Agent 并总结指定文件。"""
    agent = FileSummaryAgent(root_dir=root_dir)
    return agent.summarize_file(file_path)


class ObsidianFileSummaryRunner:
    """运行类：读取固定 Obsidian 笔记，并交给 FileSummaryAgent 总结。"""

    def __init__(
        self,
        *,
        target_file: str | Path = DEFAULT_OBSIDIAN_FILE,
        client: Any | None = None,
        model: str = MODEL,
    ) -> None:
        """保存运行参数，client 可用于测试时注入 mock，避免真实请求。"""
        self.target_file = Path(target_file).expanduser()
        self.client = client
        self.model = model

    def run(self) -> str:
        """执行完整流程：定位文件目录、调用读取工具、请求 DeepSeek 总结。"""
        target = self.target_file.resolve()
        agent = FileSummaryAgent(
            client=self.client,
            root_dir=target.parent,
            model=self.model,
        )
        return agent.summarize_file(target.name)
