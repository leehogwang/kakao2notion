"""LLM integration for category naming and description"""

import subprocess
import json
import re
from typing import Optional, Tuple, List
from pathlib import Path
from .parser import Message


class LLMProvider:
    """Base class for LLM providers"""

    def generate_category_name(
        self,
        messages: List[Message],
        existing_names: List[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate category name and description from messages

        Args:
            messages: Messages in this cluster
            existing_names: Already used category names

        Returns:
            (category_name, description)
        """
        raise NotImplementedError


class CodexProvider(LLMProvider):
    """Use Codex CLI for LLM operations"""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Codex provider

        Args:
            model: Specific model to use (e.g., "codex")
        """
        self.model = model or "default"
        self._check_codex_installed()

    def _check_codex_installed(self) -> bool:
        """Check if codex CLI is installed and authenticated"""
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raise RuntimeError(
                "Codex CLI not found or not in PATH. "
                "Install from: https://github.com/openai/codex"
            )

    def generate_category_name(
        self,
        messages: List[Message],
        existing_names: List[str] = None,
    ) -> Tuple[str, str]:
        """Generate category using Codex"""
        # Prepare message content
        sample_messages = messages[:5]  # Use first 5 as sample
        message_text = "\n".join(f"- {m.content[:200]}" for m in sample_messages)

        prompt = f"""다음 메시지들을 보고 한국어로 간단한 카테고리 이름(3-5글자)을 하나 지어줘.
그리고 카테고리 설명(한 문장)도 같이 제시해.

메시지들:
{message_text}

응답 형식:
카테고리 이름: [이름]
설명: [설명]"""

        try:
            result = subprocess.run(
                ["codex", "-c", 'service_tier="fast"', "-"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return self._parse_llm_response(result.stdout, existing_names)
            else:
                return self._fallback_category_name(messages, existing_names)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            print(f"Codex call failed: {e}")
            return self._fallback_category_name(messages, existing_names)

    def _parse_llm_response(
        self,
        response: str,
        existing_names: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Parse LLM response to extract name and description"""
        lines = response.strip().split("\n")

        name = "Uncategorized"
        description = "Items grouped by similarity"

        for line in lines:
            if "카테고리 이름" in line or "이름" in line:
                name = line.split(":")[-1].strip()
            elif "설명" in line:
                description = line.split(":")[-1].strip()

        # Ensure name is unique
        existing_names = existing_names or []
        if name in existing_names:
            name = f"{name}_{len(existing_names)}"

        return name, description

    def _fallback_category_name(
        self,
        messages: List[Message],
        existing_names: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Fallback to simple keyword extraction"""
        existing_names = existing_names or []

        # Extract common keywords
        all_text = " ".join(m.content for m in messages[:5])
        common_words = self._extract_keywords(all_text)

        name = common_words[0] if common_words else "Category"
        while name in existing_names:
            name = f"{name}_{len(existing_names)}"

        description = f"{len(messages)} items in category"
        return name, description

    def _extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """Simple keyword extraction"""
        # Split on common delimiters and filter short words
        words = re.findall(r"\b[가-힣]{2,}\b", text)
        # Count word frequencies
        from collections import Counter
        word_counts = Counter(words)
        return [word for word, _ in word_counts.most_common(top_k)]


class ClaudeProvider(LLMProvider):
    """Use Claude API for LLM operations"""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Claude provider

        Args:
            model: Claude model ID (e.g., "claude-3-haiku-20240307")
        """
        self.model = model or "claude-3-haiku-20240307"
        try:
            from anthropic import Anthropic
            self.client = Anthropic()
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

    def generate_category_name(
        self,
        messages: List[Message],
        existing_names: List[str] = None,
    ) -> Tuple[str, str]:
        """Generate category using Claude"""
        sample_messages = messages[:5]
        message_text = "\n".join(f"- {m.content[:200]}" for m in sample_messages)

        prompt = f"""다음 메시지들을 분석하고 한국어로 간단한 카테고리 이름(3-5글자)을 지어줘.
그리고 카테고리 설명(한 문장)도 함께 제시해.

메시지들:
{message_text}

응답 형식:
카테고리 이름: [이름]
설명: [설명]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return self._parse_llm_response(
                response.content[0].text,
                existing_names
            )

        except Exception as e:
            print(f"Claude API call failed: {e}")
            return self._fallback_category_name(messages, existing_names)

    def _parse_llm_response(
        self,
        response: str,
        existing_names: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Parse Claude response"""
        lines = response.strip().split("\n")

        name = "Uncategorized"
        description = "Items grouped by similarity"

        for line in lines:
            if "이름" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    name = parts[-1].strip()
            elif "설명" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    description = parts[-1].strip()

        existing_names = existing_names or []
        if name in existing_names:
            name = f"{name}_{len(existing_names)}"

        return name, description

    def _fallback_category_name(
        self,
        messages: List[Message],
        existing_names: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Fallback implementation"""
        existing_names = existing_names or []
        name = "Category"
        while name in existing_names:
            name = f"Category_{len(existing_names)}"
        return name, f"{len(messages)} items"


def get_llm_provider(
    provider: str = "codex",
    model: Optional[str] = None,
) -> LLMProvider:
    """
    Get LLM provider instance

    Args:
        provider: Provider name (codex, claude)
        model: Model specification

    Returns:
        LLMProvider instance
    """
    if provider == "codex":
        return CodexProvider(model)
    elif provider == "claude":
        return ClaudeProvider(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
