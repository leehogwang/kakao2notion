"""Merge semantically similar messages"""

import numpy as np
from typing import List, Tuple
from .parser import Message
from .vectorizer import Vectorizer


class MessageMerger:
    """Merge messages that belong together semantically"""

    def __init__(self, vectorizer: Vectorizer, similarity_threshold: float = 0.7):
        """
        Initialize merger

        Args:
            vectorizer: Fitted vectorizer instance
            similarity_threshold: Minimum similarity to merge (0-1)
        """
        self.vectorizer = vectorizer
        self.similarity_threshold = similarity_threshold

    def merge_messages(self, messages: List[Message]) -> List[Message]:
        """
        Merge messages that are semantically similar and consecutive

        Args:
            messages: List of messages

        Returns:
            List of merged messages
        """
        if len(messages) <= 1:
            return messages

        # Vectorize all messages
        texts = [m.content for m in messages]
        vectors = self.vectorizer.transform(texts)

        # Calculate pairwise similarities
        similarities = self.vectorizer.get_pairwise_similarities(vectors)

        # Find groups of similar consecutive messages
        merged = []
        skip_indices = set()

        for i in range(len(messages)):
            if i in skip_indices:
                continue

            current_group = [messages[i]]
            current_texts = [messages[i].content]

            # Look ahead for similar messages
            j = i + 1
            while j < len(messages):
                if similarities[i][j] >= self.similarity_threshold:
                    current_group.append(messages[j])
                    current_texts.append(messages[j].content)
                    skip_indices.add(j)
                    j += 1
                elif j == i + 1:
                    # Only merge consecutive messages
                    break
                else:
                    break

            # Create merged message if group size > 1
            if len(current_group) > 1:
                merged_message = self._create_merged_message(current_group)
                merged.append(merged_message)
            else:
                merged.append(messages[i])

        return merged

    def _create_merged_message(self, messages: List[Message]) -> Message:
        """Create a merged message from a group"""
        # Combine content with line breaks
        combined_content = "\n".join(m.content for m in messages)

        # Use first message's metadata
        first_msg = messages[0]

        return Message(
            content=combined_content,
            sender=first_msg.sender,
            timestamp=first_msg.timestamp,
            chat_name=first_msg.chat_name,
            original_id=f"merged_{first_msg.original_id}",
        )

    def find_message_groups(
        self,
        messages: List[Message],
        max_gap: int = 3
    ) -> List[List[int]]:
        """
        Find groups of messages that likely belong together

        Args:
            messages: List of messages
            max_gap: Maximum number of messages between groups

        Returns:
            List of message index groups
        """
        if len(messages) <= 1:
            return [[0]]

        texts = [m.content for m in messages]
        vectors = self.vectorizer.transform(texts)
        similarities = self.vectorizer.get_pairwise_similarities(vectors)

        groups = []
        current_group = [0]

        for i in range(1, len(messages)):
            # Check similarity with last message in current group
            last_idx = current_group[-1]

            if similarities[last_idx][i] >= self.similarity_threshold:
                current_group.append(i)
            elif i - last_idx <= max_gap:
                # Check if similar to any message in group
                is_similar = False
                for group_idx in current_group:
                    if similarities[group_idx][i] >= self.similarity_threshold * 0.8:
                        current_group.append(i)
                        is_similar = True
                        break

                if not is_similar:
                    groups.append(current_group)
                    current_group = [i]
            else:
                groups.append(current_group)
                current_group = [i]

        if current_group:
            groups.append(current_group)

        return groups
