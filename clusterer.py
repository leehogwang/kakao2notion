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

    def __init__(self, n_clusters: int = None, random_state: Optional[int] = None, auto_optimal: bool = False):
        """
        Initialize clusterer

        Args:
            n_clusters: Number of clusters (if None and auto_optimal=True, will be calculated)
            random_state: Random seed for reproducibility
            auto_optimal: Automatically find optimal number of clusters
        """
        self.n_clusters = n_clusters if n_clusters is not None else 5
        self.random_state = random_state
        self.auto_optimal = auto_optimal
        self.labels = None
        self.centers = None
        self.clusters = None
        self.silhouette_score = None
        self.optimal_k_history = None

    def fit(self, vectors: np.ndarray) -> "KNNClusterer":
        """
        Cluster vectors using k-means

        Args:
            vectors: Vector matrix (n_samples, n_features)

        Returns:
            Self for chaining
        """
        from sklearn.cluster import KMeans

        # Auto-calculate optimal clusters if requested
        if self.auto_optimal:
            self.n_clusters = self.find_optimal_clusters(vectors)

        kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        self.labels = kmeans.fit_predict(vectors)
        self.centers = kmeans.cluster_centers_

        # Calculate silhouette score
        from sklearn.metrics import silhouette_score
        self.silhouette_score = silhouette_score(vectors, self.labels)

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

    def find_optimal_clusters(
        self,
        vectors: np.ndarray,
        min_clusters: int = 2,
        max_clusters: Optional[int] = None,
        method: str = "silhouette"
    ) -> int:
        """
        Find optimal number of clusters using multiple methods

        Args:
            vectors: Vector matrix (n_samples, n_features)
            min_clusters: Minimum clusters to test
            max_clusters: Maximum clusters to test (default: sqrt(n_samples))
            method: Method to use ('silhouette', 'elbow', 'davies_bouldin', 'calinski')

        Returns:
            Optimal number of clusters
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import (
            silhouette_score,
            davies_bouldin_score,
            calinski_harabasz_score,
        )

        n_samples = len(vectors)

        # Set max clusters
        if max_clusters is None:
            max_clusters = max(3, min(15, int(np.sqrt(n_samples))))

        # Ensure valid range
        min_clusters = max(2, min_clusters)
        max_clusters = max(min_clusters + 1, max_clusters)

        scores = {}
        self.optimal_k_history = {}

        for k in range(min_clusters, max_clusters + 1):
            kmeans = KMeans(
                n_clusters=k,
                random_state=self.random_state,
                n_init=10,
            )
            labels = kmeans.fit_predict(vectors)

            if method == "silhouette":
                score = silhouette_score(vectors, labels)
                scores[k] = score
                self.optimal_k_history[k] = {
                    "score": score,
                    "method": "silhouette",
                    "interpretation": "Higher is better (max 1.0)"
                }

            elif method == "davies_bouldin":
                score = davies_bouldin_score(vectors, labels)
                scores[k] = -score  # Negate for consistency (lower is better)
                self.optimal_k_history[k] = {
                    "score": score,
                    "method": "davies_bouldin",
                    "interpretation": "Lower is better"
                }

            elif method == "calinski":
                score = calinski_harabasz_score(vectors, labels)
                scores[k] = score
                self.optimal_k_history[k] = {
                    "score": score,
                    "method": "calinski_harabasz",
                    "interpretation": "Higher is better"
                }

            elif method == "elbow":
                score = kmeans.inertia_
                scores[k] = -score  # Negate for consistency
                self.optimal_k_history[k] = {
                    "score": score,
                    "method": "elbow (inertia)",
                    "interpretation": "Lower is better"
                }

        # Find optimal k
        optimal_k = max(scores.items(), key=lambda x: x[1])[0]

        return optimal_k

    def find_optimal_clusters_ensemble(
        self,
        vectors: np.ndarray,
        min_clusters: int = 2,
        max_clusters: Optional[int] = None,
    ) -> Tuple[int, dict]:
        """
        Find optimal clusters using ensemble of methods

        Args:
            vectors: Vector matrix
            min_clusters: Minimum clusters
            max_clusters: Maximum clusters

        Returns:
            (optimal_k, results_dict)
        """
        results = {}

        # Try each method
        for method in ["silhouette", "davies_bouldin", "calinski", "elbow"]:
            try:
                k = self.find_optimal_clusters(
                    vectors,
                    min_clusters=min_clusters,
                    max_clusters=max_clusters,
                    method=method,
                )
                results[method] = k
            except Exception as e:
                print(f"Warning: Method '{method}' failed: {e}")
                continue

        # Vote on best k
        if results:
            from collections import Counter
            votes = Counter(results.values())
            optimal_k = votes.most_common(1)[0][0]
        else:
            optimal_k = 5  # Fallback

        return optimal_k, results

    def estimate_optimal_clusters_by_size(self, n_samples: int) -> int:
        """
        Quick estimate of optimal clusters based on data size

        Uses rule of thumb: sqrt(n/2)

        Args:
            n_samples: Number of samples

        Returns:
            Estimated optimal number of clusters
        """
        k = max(2, int(np.sqrt(n_samples / 2)))
        return k

    def get_cluster_quality_report(self) -> dict:
        """Get quality metrics for current clustering"""
        if self.silhouette_score is None:
            return {"error": "Clustering not fitted yet"}

        return {
            "n_clusters": self.n_clusters,
            "silhouette_score": round(self.silhouette_score, 3),
            "cluster_sizes": self.get_cluster_sizes(),
            "quality_interpretation": self._interpret_silhouette(self.silhouette_score),
        }

    def _interpret_silhouette(self, score: float) -> str:
        """Interpret silhouette score"""
        if score > 0.7:
            return "Excellent - Strong structure"
        elif score > 0.5:
            return "Good - Reasonable structure"
        elif score > 0.25:
            return "Fair - Weak structure"
        else:
            return "Poor - No clear structure"
