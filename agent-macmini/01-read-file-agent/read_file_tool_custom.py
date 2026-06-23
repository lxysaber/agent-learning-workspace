import json
from pathlib import Path
from typing import Any

def _error(message: str, *, path: str | None = None) -> dict[str, Any]:
    """统一返回错误结构，方便 Agent 后续判断是否继续。"""
    return {
        "tool": "read_file",
        "ok": False,
        "path": path,
        "content": None,
        "truncated": False,
        "error": message,
    }

def _safe_resolve(root_dir: str | Path, file_path: str) -> Path:
    """把用户传入的相对路径解析到允许目录内，避免读取目录外文件。"""
    root = Path(root_dir).resolve()
    candidate = (root / file_path).resolve()

    if not candidate.is_relative_to(root):
        raise ValueError("文件路径超出允许目录")
    
    return candidate

def read_file(
    file_path: str,
    *,
    root_dir: str | Path = ".",
    encoding: str = "utf-8",
    max_chars: int = 8_000,
) -> dict[str, Any]:
    """读取文本文件，并返回适合 Agent 消费的结构化结果。

    这个函数就是 Agent 的一个“工具”。它不直接替 Agent 做推理，只负责：
    1. 校验参数；
    2. 限制读取范围；
    3. 执行文件读取；
    4. 把成功或失败都包装成稳定的 dict。
    """
    if not file_path.strip():
        return _error("file_path 不能为空", path=file_path)
    
    if Path(file_path).is_absolute():
        return _error("只允许传入相对路径", path=file_path)
    
    if max_chars < 0:
        return _error("max_chars 必须大于 0", path=file_path)
    
    try:
        target_path = _safe_resolve(root_dir, file_path)
    except ValueError as exc:
        return _error(str(exc), path=file_path)
    
    if not target_path.exists():
        return _error("文件不存在", path=str(target_path))
    
    if not target_path.is_file():
         return _error("目标路径不是文件", path=str(target_path))
    
    try:
        content = target_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
         return _error(f"无法使用 {encoding} 解码文件", path=str(target_path))
    except OSError as exc:
         return _error(f"读取文件失败: {exc}", path=str(target_path))

    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars]
          
    return {
        "tool": "read_file",
        "ok": True,
        "path": str(target_path),
        "content": content,
        "truncated": truncated,
        "error": None,
    }

def agent_step(user_message: str, *, root_dir: str | Path = ".") -> dict[str, Any]:
    """一个极小的 Agent 分发器，用来演示如何调用 read_file 工具。

    真正的 Agent 通常会由模型决定是否调用工具；这里先不用模型，只用
    一个简单命令格式让调用链路变得可见：read <相对文件路径>
    """
    command = user_message.strip()
    prefix = "read "

    if not command.startswith(prefix):
        return {
            "ok": False,
            "error": "目前只支持命令格式: read <相对文件路径>",
        }
    file_path = command.removeprefix(prefix).strip()
    return read_file(file_path, root_dir=root_dir)

def main() -> None:
    """运行示例：读取同目录下的 sample_note.txt。"""
    current_dir = Path(__file__).parent
    result = agent_step("read sample_note.txt", root_dir=current_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()