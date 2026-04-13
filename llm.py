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

    def __init__(self, model: Optional[str] = None, skip_auth_check: bool = False):
        """
        Initialize Codex provider

        Args:
            model: Specific model to use (e.g., "codex")
            skip_auth_check: Skip authentication check (for testing)
        """
        self.model = model or "default"
        self.is_authenticated = False
        self._check_codex_installed()
        if not skip_auth_check:
            self._check_codex_authenticated()

    def _check_codex_installed(self) -> bool:
        """Check if codex CLI is installed"""
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("Codex not found")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError) as e:
            raise RuntimeError(
                "Codex CLI not found or not in PATH. "
                "Install from: https://github.com/openai/codex\n"
                f"Error: {e}"
            )

    def _check_codex_authenticated(self) -> bool:
        """Check if codex is authenticated (has valid token)"""
        try:
            # Try to run a simple codex command that requires authentication
            result = subprocess.run(
                ["codex", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Check if output contains "authenticated" or similar indicators
                output_lower = result.stdout.lower() + result.stderr.lower()
                if "authenticated" in output_lower or "valid" in output_lower or "token" in output_lower:
                    self.is_authenticated = True
                    return True
                else:
                    # Try checking for auth file
                    self.is_authenticated = self._check_auth_file()
                    return self.is_authenticated
            else:
                # If auth status command fails, try alternative check
                self.is_authenticated = self._check_auth_file()
                return self.is_authenticated

        except (subprocess.TimeoutExpired, Exception):
            # If we can't check auth, try file-based approach
            self.is_authenticated = self._check_auth_file()
            return self.is_authenticated

    def _check_auth_file(self) -> bool:
        """Check if Codex auth token exists in config"""
        try:
            # Common Codex auth file locations
            auth_locations = [
                Path.home() / ".codex" / "auth.json",
                Path.home() / ".codex" / "config.json",
                Path.home() / ".openai" / "auth.json",
            ]

            for auth_file in auth_locations:
                if auth_file.exists():
                    try:
                        with open(auth_file, "r") as f:
                            content = f.read()
                            # Check if file contains token or auth info
                            if "token" in content.lower() or "api_key" in content.lower():
                                return True
                    except Exception:
                        continue

            return False
        except Exception:
            return False

    def get_auth_status(self) -> dict:
        """Get detailed authentication status"""
        return {
            "provider": "codex",
            "is_installed": True,  # If we got here, it's installed
            "is_authenticated": self.is_authenticated,
            "status_message": (
                "✓ Codex authenticated and ready"
                if self.is_authenticated
                else "✗ Codex not authenticated. Run: codex login"
            ),
        }

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
        self.is_authenticated = False

        try:
            from anthropic import Anthropic
            self.client = Anthropic()
            self._check_claude_authenticated()
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

    def _check_claude_authenticated(self) -> bool:
        """Check if Claude API key is available"""
        try:
            import os
            # Check environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key and len(api_key) > 10:
                self.is_authenticated = True
                return True

            # Check .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key and len(api_key) > 10:
                    self.is_authenticated = True
                    return True
            except Exception:
                pass

            # Try to call API (will raise error if no key)
            try:
                # Test with a minimal call
                self.client.messages.create(
                    model=self.model,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}],
                )
                self.is_authenticated = True
                return True
            except Exception as e:
                if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                    self.is_authenticated = False
                    return False
                # Other errors (like rate limit) mean it's authenticated
                self.is_authenticated = True
                return True

        except Exception:
            self.is_authenticated = False
            return False

    def get_auth_status(self) -> dict:
        """Get detailed authentication status"""
        return {
            "provider": "claude",
            "is_authenticated": self.is_authenticated,
            "status_message": (
                "✓ Claude API authenticated and ready"
                if self.is_authenticated
                else "✗ Claude API key not found. Set ANTHROPIC_API_KEY environment variable"
            ),
        }

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
    provider: Optional[str] = None,
    model: Optional[str] = None,
    auto_detect: bool = True,
) -> LLMProvider:
    """
    Get LLM provider instance with auto-detection

    Args:
        provider: Provider name (codex, claude). If None, auto-detect
        model: Model specification
        auto_detect: Automatically find first working provider

    Returns:
        LLMProvider instance

    Raises:
        RuntimeError: If no provider available or specified provider not working
    """
    # If provider specified, use it
    if provider:
        if provider == "codex":
            return CodexProvider(model)
        elif provider == "claude":
            return ClaudeProvider(model)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # Auto-detect available provider
    if auto_detect:
        providers_to_try = [
            ("codex", CodexProvider),
            ("claude", ClaudeProvider),
        ]

        for provider_name, provider_class in providers_to_try:
            try:
                instance = provider_class(model)
                if instance.is_authenticated:
                    return instance
            except Exception:
                continue

        # If no authenticated provider found, try anyway (may work)
        try:
            return CodexProvider(model)
        except Exception:
            try:
                return ClaudeProvider(model)
            except Exception:
                raise RuntimeError(
                    "No LLM provider available. "
                    "Please install and authenticate Codex or Claude."
                )

    raise RuntimeError("No provider specified and auto-detect disabled")


def check_llm_status(provider: Optional[str] = None) -> dict:
    """
    Check LLM provider authentication status

    Args:
        provider: Specific provider to check (codex, claude, or None for all)

    Returns:
        Dictionary with provider statuses
    """
    results = {}

    if provider is None or provider == "codex":
        try:
            codex = CodexProvider(skip_auth_check=True)
            results["codex"] = codex.get_auth_status()
        except Exception as e:
            results["codex"] = {
                "provider": "codex",
                "is_installed": False,
                "is_authenticated": False,
                "status_message": f"✗ Codex not available: {e}",
            }

    if provider is None or provider == "claude":
        try:
            claude = ClaudeProvider()
            results["claude"] = claude.get_auth_status()
        except Exception as e:
            results["claude"] = {
                "provider": "claude",
                "is_authenticated": False,
                "status_message": f"✗ Claude not available: {e}",
            }

    return results
