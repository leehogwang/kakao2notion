"""Vectorization of messages using embeddings"""

import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path
import json


class Vectorizer:
    """Convert text messages to vector embeddings"""

    def __init__(self, model_type: str = "tfidf"):
        """
        Initialize vectorizer

        Args:
            model_type: Type of vectorization (tfidf, sbert)
        """
        self.model_type = model_type
        self.vectorizer = None
        self.vocabulary = None

        if model_type == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                stop_words=None,  # Korean doesn't have built-in stopwords
            )
        elif model_type == "sbert":
            try:
                from sentence_transformers import SentenceTransformer
                self.vectorizer = SentenceTransformer("distiluse-base-multilingual-cased-v2")
            except ImportError:
                print("sentence-transformers not installed. Falling back to TF-IDF")
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.vectorizer = TfidfVectorizer(max_features=1000)
                self.model_type = "tfidf"

    def fit(self, texts: List[str]) -> np.ndarray:
        """
        Fit vectorizer on texts and return vectors

        Args:
            texts: List of text messages

        Returns:
            Vector matrix (n_samples, n_features)
        """
        if self.model_type == "tfidf":
            vectors = self.vectorizer.fit_transform(texts).toarray()
            self.vocabulary = self.vectorizer.get_feature_names_out()
            return vectors
        elif self.model_type == "sbert":
            vectors = self.vectorizer.encode(texts, convert_to_numpy=True)
            return vectors

    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Transform texts to vectors using fitted vectorizer

        Args:
            texts: List of text messages

        Returns:
            Vector matrix (n_samples, n_features)
        """
        if self.model_type == "tfidf":
            if self.vectorizer is None:
                raise ValueError("Vectorizer not fitted. Call fit() first.")
            vectors = self.vectorizer.transform(texts).toarray()
            return vectors
        elif self.model_type == "sbert":
            vectors = self.vectorizer.encode(texts, convert_to_numpy=True)
            return vectors

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """
        Fit vectorizer and return vectors in one step

        Args:
            texts: List of text messages

        Returns:
            Vector matrix (n_samples, n_features)
        """
        return self.fit(texts)

    def get_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get_pairwise_similarities(
        self, vectors: np.ndarray
    ) -> np.ndarray:
        """
        Calculate pairwise similarities between all vectors

        Args:
            vectors: Matrix of vectors (n_samples, n_features)

        Returns:
            Pairwise similarity matrix (n_samples, n_samples)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity(vectors)

    def save(self, path: Path) -> None:
        """Save vectorizer to disk"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self.model_type == "tfidf":
            import pickle
            with open(path / "vectorizer.pkl", "wb") as f:
                pickle.dump(self.vectorizer, f)
            if self.vocabulary is not None:
                with open(path / "vocabulary.json", "w") as f:
                    json.dump(self.vocabulary.tolist(), f)

    def load(self, path: Path) -> None:
        """Load vectorizer from disk"""
        path = Path(path)

        if self.model_type == "tfidf":
            import pickle
            with open(path / "vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            try:
                with open(path / "vocabulary.json", "r") as f:
                    self.vocabulary = np.array(json.load(f))
            except FileNotFoundError:
                pass
