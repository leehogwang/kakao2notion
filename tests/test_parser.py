"""Tests for message parser"""

import json
from pathlib import Path
import tempfile
from kakao2notion.parser import parse_kakaotalk_messages, Message


def test_parse_json_messages():
    """Test parsing JSON format messages"""
    test_data = {
        "chatName": "Test Chat",
        "messages": [
            {
                "text": "Hello",
                "sender": "User1",
                "time": "2024-01-01 10:00:00"
            },
            {
                "text": "World",
                "sender": "User2",
                "time": "2024-01-01 10:01:00"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        f.flush()
        temp_path = Path(f.name)

    try:
        messages = parse_kakaotalk_messages(temp_path, format='json')

        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[0].sender == "User1"
        assert messages[1].content == "World"
        assert messages[1].sender == "User2"
    finally:
        temp_path.unlink()


def test_parse_txt_messages():
    """Test parsing text format messages"""
    test_content = """[2024-01-01 10:00:00] User1: Hello
[2024-01-01 10:01:00] User2: World
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        f.flush()
        temp_path = Path(f.name)

    try:
        messages = parse_kakaotalk_messages(temp_path, format='txt')

        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[0].sender == "User1"
        assert messages[1].content == "World"
    finally:
        temp_path.unlink()


def test_empty_messages_filtered():
    """Test that empty messages are filtered"""
    test_data = {
        "chatName": "Test",
        "messages": [
            {"text": "Hello", "sender": "User1", "time": "2024-01-01 10:00:00"},
            {"text": "", "sender": "User2", "time": "2024-01-01 10:01:00"},
            {"text": "World", "sender": "User1", "time": "2024-01-01 10:02:00"}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        f.flush()
        temp_path = Path(f.name)

    try:
        messages = parse_kakaotalk_messages(temp_path)
        assert len(messages) == 2
    finally:
        temp_path.unlink()


def test_auto_format_detection():
    """Test automatic format detection"""
    test_data = {
        "chatName": "Test",
        "messages": [
            {"text": "Hello", "sender": "User", "time": "2024-01-01 10:00:00"}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        f.flush()
        temp_path = Path(f.name)

    try:
        messages = parse_kakaotalk_messages(temp_path, format='auto')
        assert len(messages) == 1
        assert messages[0].content == "Hello"
    finally:
        temp_path.unlink()
