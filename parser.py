"""Parse KakaoTalk message exports"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """Represents a single KakaoTalk message"""

    content: str
    sender: Optional[str] = None
    timestamp: Optional[datetime] = None
    chat_name: Optional[str] = None
    original_id: Optional[str] = None  # For tracking original position


def parse_kakaotalk_json(file_path: Path) -> List[Message]:
    """
    Parse KakaoTalk messages from JSON export

    Expected format:
    {
        "chatName": "chat room name",
        "messages": [
            {
                "text": "message content",
                "sender": "sender name",
                "time": "2024-01-01 12:00:00"
            }
        ]
    }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []
    chat_name = data.get("chatName", "Unknown Chat")

    for idx, msg_data in enumerate(data.get("messages", [])):
        try:
            timestamp = None
            if "time" in msg_data:
                try:
                    timestamp = datetime.fromisoformat(msg_data["time"])
                except (ValueError, TypeError):
                    # Try common KakaoTalk timestamp format
                    try:
                        timestamp = datetime.strptime(
                            msg_data["time"], "%Y-%m-%d %H:%M:%S"
                        )
                    except (ValueError, TypeError):
                        pass

            message = Message(
                content=msg_data.get("text", "").strip(),
                sender=msg_data.get("sender"),
                timestamp=timestamp,
                chat_name=chat_name,
                original_id=f"{chat_name}_{idx}",
            )

            if message.content:  # Only add non-empty messages
                messages.append(message)
        except (KeyError, ValueError) as e:
            print(f"Warning: Failed to parse message {idx}: {e}")
            continue

    return messages


def parse_kakaotalk_txt(file_path: Path) -> List[Message]:
    """
    Parse KakaoTalk messages from text export

    Expected format:
    [2024-01-01 12:00:00] Sender: Message content
    [2024-01-01 12:01:00] Sender: Another message
    """
    messages = []
    pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.+)"

    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                timestamp_str, sender, content = match.groups()
                try:
                    timestamp = datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    timestamp = None

                message = Message(
                    content=content.strip(),
                    sender=sender.strip(),
                    timestamp=timestamp,
                    original_id=f"txt_{idx}",
                )
                messages.append(message)

    return messages


def parse_kakaotalk_messages(
    file_path: Path,
    format: str = "auto",
) -> List[Message]:
    """
    Parse KakaoTalk messages from file

    Args:
        file_path: Path to the export file
        format: Export format (json, txt, or auto)

    Returns:
        List of parsed Message objects
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if format == "auto":
        format = "json" if file_path.suffix.lower() == ".json" else "txt"

    if format == "json":
        return parse_kakaotalk_json(file_path)
    elif format == "txt":
        return parse_kakaotalk_txt(file_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def messages_to_dict(messages: List[Message]) -> List[dict]:
    """Convert Message objects to dictionaries"""
    return [asdict(m) for m in messages]
