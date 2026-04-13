"""
kakao2notion — Convert KakaoTalk messages to organized Notion pages
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .parser import parse_kakaotalk_messages
from .vectorizer import Vectorizer
from .clusterer import KNNClusterer
from .merger import MessageMerger
from .notion_client import NotionClient

__all__ = [
    "parse_kakaotalk_messages",
    "Vectorizer",
    "KNNClusterer",
    "MessageMerger",
    "NotionClient",
]
