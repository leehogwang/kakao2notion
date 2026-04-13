"""Configuration management for kakao2notion"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv


class Config(BaseModel):
    """Configuration schema for kakao2notion"""

    # Notion credentials
    notion_api_key: str = Field(default="", description="Notion API token")
    notion_database_id: Optional[str] = Field(default=None, description="Notion database ID (optional)")

    # KakaoTalk settings
    kakaotalk_export_format: str = Field(
        default="json",
        description="Format of KakaoTalk export (json, txt)"
    )

    # Clustering settings
    n_clusters: int = Field(default=5, description="Number of clusters for KNN")
    similarity_threshold: float = Field(
        default=0.7,
        description="Similarity threshold for merging messages (0-1)"
    )

    # LLM settings
    use_llm_for_categories: bool = Field(
        default=True,
        description="Use LLM to generate category names"
    )
    llm_provider: str = Field(
        default="codex",
        description="LLM provider (codex, claude, gemini)"
    )
    llm_model: Optional[str] = Field(default=None, description="Specific model to use")

    # Processing settings
    batch_size: int = Field(default=10, description="Batch size for processing")
    max_workers: int = Field(default=4, description="Max threads for parallel processing")

    class Config:
        env_file = ".env"
        case_sensitive = False


class ConfigManager:
    """Manage configuration loading and persistence"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".kakao2notion" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        load_dotenv()
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """Load configuration from file or environment"""
        # Try loading from file first
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Config(**data)

        # Fall back to environment variables
        return Config(
            notion_api_key=os.getenv("NOTION_API_KEY", ""),
            notion_database_id=os.getenv("NOTION_DATABASE_ID"),
            llm_provider=os.getenv("LLM_PROVIDER", "codex"),
            llm_model=os.getenv("LLM_MODEL"),
        )

    def save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config.model_dump(), f, indent=2)

    def update_config(self, **kwargs) -> None:
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

    @property
    def notion_api_key(self) -> str:
        return self.config.notion_api_key

    @property
    def notion_database_id(self) -> Optional[str]:
        return self.config.notion_database_id
