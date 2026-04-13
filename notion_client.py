"""Notion API integration"""

from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
import json
from notion_client import Client
from .parser import Message


class NotionClient:
    """Handle Notion API operations"""

    def __init__(self, api_key: str):
        """
        Initialize Notion client

        Args:
            api_key: Notion API token
        """
        self.client = Client(auth=api_key)
        self.api_key = api_key

    def create_parent_page(
        self,
        parent_database_id: str,
        title: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a parent category page

        Args:
            parent_database_id: Parent database ID
            title: Category title
            description: Category description

        Returns:
            Page ID of created page
        """
        page_data = {
            "parent": {"database_id": parent_database_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title,
                            }
                        }
                    ]
                },
                "Description": {
                    "rich_text": [
                        {
                            "text": {
                                "content": description or "",
                            }
                        }
                    ]
                } if description else None,
            },
        }

        # Remove None values
        page_data["properties"] = {k: v for k, v in page_data["properties"].items() if v is not None}

        response = self.client.pages.create(**page_data)
        return response["id"]

    def create_child_page(
        self,
        parent_page_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a child page under a parent

        Args:
            parent_page_id: Parent page ID
            title: Page title
            content: Page content
            metadata: Additional metadata

        Returns:
            Page ID of created page
        """
        page_data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title[:100],  # Notion limits title length
                            }
                        }
                    ]
                },
            },
        }

        response = self.client.pages.create(**page_data)
        page_id = response["id"]

        # Add content as block
        if content:
            self._add_page_content(page_id, content)

        return page_id

    def _add_page_content(self, page_id: str, content: str) -> None:
        """Add content blocks to a page"""
        # Split content into paragraphs
        paragraphs = content.split("\n")

        blocks = []
        for para in paragraphs:
            if para.strip():
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": para,
                                    },
                                }
                            ],
                        },
                    }
                )

        if blocks:
            self.client.blocks.children.append(page_id, children=blocks)

    def create_hierarchy(
        self,
        parent_database_id: str,
        categories: Dict[str, List[Message]],
    ) -> None:
        """
        Create full Notion hierarchy: categories → messages

        Args:
            parent_database_id: Parent database ID
            categories: Dict mapping category names to message lists
        """
        for category_name, messages in categories.items():
            # Create category page
            category_id = self.create_parent_page(
                parent_database_id,
                category_name,
                description=f"{len(messages)} items",
            )

            # Create message pages under category
            for msg in messages:
                title = msg.content[:100] if msg.content else "Untitled"
                self.create_child_page(
                    category_id,
                    title=title,
                    content=msg.content,
                    metadata={
                        "sender": msg.sender,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    },
                )

    def get_database_pages(self, database_id: str) -> List[Dict]:
        """Get all pages in a database"""
        response = self.client.databases.query(database_id=database_id)
        return response.get("results", [])

    def update_page_property(
        self,
        page_id: str,
        property_name: str,
        value: str,
    ) -> None:
        """Update a page property"""
        self.client.pages.update(
            page_id=page_id,
            properties={
                property_name: {
                    "rich_text": [
                        {
                            "text": {
                                "content": value,
                            }
                        }
                    ]
                }
            },
        )

    def test_connection(self) -> bool:
        """Test if API connection works"""
        try:
            self.client.users.me()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
