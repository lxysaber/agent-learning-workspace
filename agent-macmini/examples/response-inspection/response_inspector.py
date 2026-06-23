import json
from collections.abc import Iterable
from typing import Any


class ResponseInspector:
    """将模型 SDK 响应转换为便于观察和复用的紧凑结构。"""

    def __init__(self, omitted_fields: Iterable[str] | None = None) -> None:
        # 默认过滤搜索工具返回的巨大加密载荷，也允许调用方追加其他字段。
        self.omitted_fields = {"encrypted_content"}
        if omitted_fields:
            self.omitted_fields.update(omitted_fields)

    def to_plain(self, value: Any) -> Any:
        """递归转换 SDK 对象，生成能够被 JSON 序列化的普通数据。"""
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, list):
            return [self.to_plain(item) for item in value]
        if isinstance(value, tuple):
            return [self.to_plain(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self.to_plain(item)
                for key, item in value.items()
                if key not in self.omitted_fields
            }
        if hasattr(value, "model_dump"):
            return self.to_plain(value.model_dump())
        return str(value)

    def summarize_block(self, block: Any) -> dict[str, Any]:
        """按内容块类型提取最值得研究的字段。"""
        block_type = getattr(block, "type", type(block).__name__)
        summary: dict[str, Any] = {"type": block_type}

        if block_type == "thinking":
            summary["thinking"] = getattr(block, "thinking", "")
        elif block_type == "server_tool_use":
            summary.update(
                {
                    "id": getattr(block, "id", None),
                    "name": getattr(block, "name", None),
                    "input": self.to_plain(getattr(block, "input", None)),
                }
            )
        elif block_type == "web_search_tool_result":
            summary["tool_use_id"] = getattr(block, "tool_use_id", None)
            summary["results"] = [
                {
                    "title": getattr(result, "title", None),
                    "url": getattr(result, "url", None),
                    "page_age": getattr(result, "page_age", None),
                }
                for result in getattr(block, "content", [])
            ]
        elif block_type == "text":
            summary["text"] = getattr(block, "text", "")
            summary["citations"] = self.to_plain(
                getattr(block, "citations", None)
            )
        else:
            # 未知块保留普通字段，便于发现 SDK 新增的响应类型。
            summary["class_name"] = type(block).__name__
            summary["data"] = self.to_plain(block)

        return summary

    def summarize_response(self, response: Any) -> dict[str, Any]:
        """将完整响应整理为包含元数据和内容块的字典。"""
        content = getattr(response, "content", [])
        return {
            "id": getattr(response, "id", None),
            "model": getattr(response, "model", None),
            "stop_reason": getattr(response, "stop_reason", None),
            "usage": self.to_plain(getattr(response, "usage", None)),
            "content": [
                {"index": index, **self.summarize_block(block)}
                for index, block in enumerate(content)
            ],
        }

    def inspect_types(self, response: Any) -> list[str]:
        """按原始调试格式返回响应对象和各内容块的类型地图。"""
        content = getattr(response, "content", [])
        lines = [
            str(type(response)),
            str(type(content)),
        ]
        lines.extend(
            f"{index} {type(block).__name__} {getattr(block, 'type', None)}"
            for index, block in enumerate(content)
        )
        return lines

    def format_json(self, response: Any, indent: int = 2) -> str:
        """返回过滤敏感大字段后的格式化 JSON 字符串。"""
        return json.dumps(
            self.summarize_response(response),
            ensure_ascii=False,
            indent=indent,
        )

    def print_response(self, response: Any, indent: int = 2) -> None:
        """依次打印类型地图和紧凑 JSON。"""
        print("\n".join(self.inspect_types(response)))
        print(self.format_json(response, indent=indent))
