"""KNN-based clustering for message categorization"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Cluster:
    """Represents a cluster of messages"""

    label: int
    indices: List[int]
    center: Optional[np.ndarray] = None
    category_name: Optional[str] = None
    category_description: Optional[str] = None

    def __len__(self) -> int:
        return len(self.indices)


class KNNClusterer:
    """Cluster messages using KNN-based approach (approximation of k-means)"""

    def __init__(self, n_clusters: int = 5, random_state: Optional[int] = None):
        """
        Initialize clusterer

        Args:
            n_clusters: Number of clusters
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.labels = None
        self.centers = None
        self.clusters = None

    def fit(self, vectors: np.ndarray) -> "KNNClusterer":
        """
        Cluster vectors using k-means

        Args:
            vectors: Vector matrix (n_samples, n_features)

        Returns:
            Self for chaining
        """
        from sklearn.cluster import KMeans

        kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        self.labels = kmeans.fit_predict(vectors)
        self.centers = kmeans.cluster_centers_

        self._create_clusters()
        return self

    def _create_clusters(self) -> None:
        """Create cluster objects from labels"""
        self.clusters = []
        for cluster_id in range(self.n_clusters):
            indices = np.where(self.labels == cluster_id)[0].tolist()
            cluster = Cluster(
                label=cluster_id,
                indices=indices,
                center=self.centers[cluster_id] if self.centers is not None else None,
            )
            self.clusters.append(cluster)

    def get_clusters(self) -> List[Cluster]:
        """Get list of clusters"""
        if self.clusters is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        return self.clusters

    def get_cluster_assignments(self) -> np.ndarray:
        """Get array of cluster assignments for each message"""
        if self.labels is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        return self.labels

    def get_cluster_sizes(self) -> dict:
        """Get sizes of all clusters"""
        if self.clusters is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        return {c.label: len(c) for c in self.clusters}

    def get_messages_in_cluster(self, cluster_id: int) -> List[int]:
        """Get message indices in a specific cluster"""
        if self.clusters is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        for cluster in self.clusters:
            if cluster.label == cluster_id:
                return cluster.indices
        return []

    def set_category_name(self, cluster_id: int, name: str, description: Optional[str] = None) -> None:
        """Set category name for a cluster"""
        if self.clusters is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")

        for cluster in self.clusters:
            if cluster.label == cluster_id:
                cluster.category_name = name
                cluster.category_description = description
                break

    def get_category_names(self) -> dict:
        """Get category names for all clusters"""
        if self.clusters is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        return {c.label: c.category_name or f"Category {c.label}" for c in self.clusters}

    def find_similar_messages(
        self,
        vector: np.ndarray,
        similarity_threshold: float = 0.7,
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find messages similar to given vector

        Args:
            vector: Query vector
            similarity_threshold: Minimum similarity (0-1)
            k: Maximum number of results

        Returns:
            List of (message_index, similarity) tuples
        """
        if self.centers is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")

        from sklearn.metrics.pairwise import cosine_similarity

        # Find most similar cluster
        similarities = cosine_similarity([vector], self.centers)[0]
        most_similar_cluster = np.argmax(similarities)

        # Get messages in that cluster
        cluster_indices = self.get_messages_in_cluster(most_similar_cluster)

        results = []
        for idx in cluster_indices:
            results.append((idx, float(similarities[most_similar_cluster])))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        # Filter by threshold and limit to k
        results = [r for r in results if r[1] >= similarity_threshold][:k]

        return results

    def rebalance_clusters(self, vectors: np.ndarray, max_cluster_size: Optional[int] = None) -> None:
        """
        Rebalance clusters by adjusting n_clusters based on data size

        Args:
            vectors: Vector matrix
            max_cluster_size: Maximum allowed cluster size
        """
        n_samples = len(vectors)

        if max_cluster_size:
            new_n_clusters = max(1, n_samples // max_cluster_size)
            if new_n_clusters != self.n_clusters:
                self.n_clusters = new_n_clusters
                self.fit(vectors)
