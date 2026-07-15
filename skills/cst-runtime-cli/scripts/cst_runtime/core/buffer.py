import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class Command:
    """Represents a single VBA operation for batch execution."""
    name: str
    vba_script: str
    timestamp: float = field(default_factory=time.time)

class CommandBuffer:
    """Manages a buffered list of VBA commands for batch execution."""
    def __init__(self) -> None:
        self.commands: List[Command] = []

    def append(self, name: str, vba_script: str) -> None:
        self.commands.append(Command(name=name, vba_script=vba_script))

    def get_vba_script(self) -> str:
        # 移除 VBA 注释，直接拼接指令，并在末尾补一个换行符
        scripts = [cmd.vba_script for cmd in self.commands if cmd.vba_script.strip()]
        if not scripts:
            return ""
        return "\n".join(scripts) + "\n"
    
    def get_summary_name(self) -> str:
        names = [cmd.name for cmd in self.commands if cmd.name]
        if not names:
            return "Batch Execution"
        
        summary = ", ".join(names[:3])
        if len(names) > 3:
            summary += f" and {len(names) - 3} more"
        return f"Batch: {summary}"

# 全局映射：将 session_id (即标准化后的项目路径) 映射到其专属的 CommandBuffer
_buffers: Dict[str, CommandBuffer] = {}

def begin_batch(session_id: str) -> None:
    """为特定的 session 开启批量缓冲模式。"""
    _buffers[session_id] = CommandBuffer()

def is_batch_mode(session_id: str) -> bool:
    """检查特定 session 是否处于批量缓冲模式。"""
    return session_id in _buffers

def append_to_batch(session_id: str, name: str, lines: List[str]) -> None:
    """向缓冲池追加指令。"""
    buffer = _buffers.get(session_id)
    if buffer:
        buffer.append(name=name, vba_script="\n".join(lines))

def pop_batch(session_id: str) -> Tuple[str, str]:
    """取出并清除特定 session 的缓冲区内容，返回 (History Name, VBA Script)。"""
    buffer = _buffers.pop(session_id, None)
    if not buffer:
        return "", ""
    return buffer.get_summary_name(), buffer.get_vba_script()

