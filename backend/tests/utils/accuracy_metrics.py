"""
Accuracy metrics calculation utilities for NSF Researcher Matching API tests.

This module provides functions to calculate precision, recall, F1 score,
and other accuracy metrics for evaluating matching algorithm performance.
"""

from typing import List, Set, Dict, Any, Tuple, Optional, Union
import numpy as np
from collections import defaultdict
import json


def calculate_precision(predicted: List[Any], actual: List[Any]) -> float:
    """
    Calculate precision: TP / (TP + FP).
    
    Args:
        predicted: List of predicted results
        actual: List of actual/ground truth results
    
    Returns:
        Precision score between 0.0 and 1.0
    """
    if not predicted:
        return 0.0
    
    predicted_set = set(predicted)
    actual_set = set(actual)
    
    true_positives = len(predicted_set.intersection(actual_set))
    
    return true_positives / len(predicted_set)


def calculate_recall(predicted: List[Any], actual: List[Any]) -> float:
    """
    Calculate recall: TP / (TP + FN).
    
    Args:
        predicted: List of predicted results
        actual: List of actual/ground truth results
    
    Returns:
        Recall score between 0.0 and 1.0
    """
    if not actual:
        return 1.0  # Perfect recall when there are no actual items to find
    
    predicted_set = set(predicted)
    actual_set = set(actual)
    
    true_positives = len(predicted_set.intersection(actual_set))
    
    return true_positives / len(actual_set)


def calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score: 2 * (precision * recall) / (precision + recall).
    
    Args:
        precision: Precision score
        recall: Recall score
    
    Returns:
        F1 score between 0.0 and 1.0
    """
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def calculate_jaccard_similarity(set1: Set[Any], set2: Set[Any]) -> float:
    """
    Calculate Jaccard similarity: |A ∩ B| / |A ∪ B|.
    
    Args:
        set1: First set
        set2: Second set
    
    Returns:
        Jaccard similarity between 0.0 and 1.0
    """
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def calculate_role_based_accuracy(
    predicted_teams: List[Dict[str, Any]],
    actual_teams: List[Dict[str, Any]],
    role_field: str = "role"
) -> Dict[str, float]:
    """
    Calculate accuracy metrics for role-based team matching.
    
    Args:
        predicted_teams: List of predicted team compositions
        actual_teams: List of actual team compositions
        role_field: Field name containing role information
    
    Returns:
        Dictionary with role-based accuracy metrics
    """
    role_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    
    # Group by roles
    predicted_by_role = defaultdict(set)
    actual_by_role = defaultdict(set)
    
    for team in predicted_teams:
        role = team.get(role_field, "unknown")
        researcher_id = team.get("researcher_id") or team.get("id")
        if researcher_id:
            predicted_by_role[role].add(researcher_id)
    
    for team in actual_teams:
        role = team.get(role_field, "unknown")
        researcher_id = team.get("researcher_id") or team.get("id")
        if researcher_id:
            actual_by_role[role].add(researcher_id)
    
    # Calculate metrics for each role
    all_roles = set(predicted_by_role.keys()) | set(actual_by_role.keys())
    
    results = {}
    for role in all_roles:
        predicted_set = predicted_by_role[role]
        actual_set = actual_by_role[role]
        
        tp = len(predicted_set.intersection(actual_set))
        fp = len(predicted_set - actual_set)
        fn = len(actual_set - predicted_set)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = calculate_f1_score(precision, recall)
        
        results[role] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        }
    
    return results


def calculate_ranking_metrics(
    predicted_ranking: List[Any],
    actual_ranking: List[Any],
    k: int = None
) -> Dict[str, float]:
    """
    Calculate ranking-based metrics like NDCG and MAP.
    
    Args:
        predicted_ranking: List of items in predicted order
        actual_ranking: List of items in actual/ideal order
        k: Optional cutoff for top-k evaluation
    
    Returns:
        Dictionary with ranking metrics
    """
    if k is not None:
        predicted_ranking = predicted_ranking[:k]
        actual_ranking = actual_ranking[:k]
    
    # Calculate Average Precision
    relevant_items = set(actual_ranking)
    precision_at_k = []
    relevant_found = 0
    
    for i, item in enumerate(predicted_ranking):
        if item in relevant_items:
            relevant_found += 1
            precision_at_k.append(relevant_found / (i + 1))
    
    average_precision = sum(precision_at_k) / len(relevant_items) if relevant_items else 0.0
    
    # Calculate NDCG (simplified version)
    dcg = 0.0
    for i, item in enumerate(predicted_ranking):
        if item in relevant_items:
            dcg += 1.0 / np.log2(i + 2)  # +2 because log2(1) = 0
    
    # Ideal DCG
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(actual_ranking), len(predicted_ranking))))
    
    ndcg = dcg / idcg if idcg > 0 else 0.0
    
    return {
        "average_precision": average_precision,
        "ndcg": ndcg,
        "precision_at_k": precision_at_k[-1] if precision_at_k else 0.0
    }


class AccuracyCalculator:
    """
    Comprehensive accuracy calculator for matching results.
    """
    
    def __init__(self):
        self.results = []
    
    def add_result(
        self,
        predicted: List[Any],
        actual: List[Any],
        metadata: Dict[str, Any] = None
    ):
        """
        Add a result for accuracy calculation.
        
        Args:
            predicted: Predicted results
            actual: Actual/ground truth results
            metadata: Optional metadata about the test case
        """
        result = {
            "predicted": predicted,
            "actual": actual,
            "metadata": metadata or {},
            "metrics": self._calculate_metrics(predicted, actual)
        }
        self.results.append(result)
    
    def _calculate_metrics(self, predicted: List[Any], actual: List[Any]) -> Dict[str, float]:
        """Calculate all metrics for a single result."""
        precision = calculate_precision(predicted, actual)
        recall = calculate_recall(predicted, actual)
        f1 = calculate_f1_score(precision, recall)
        jaccard = calculate_jaccard_similarity(set(predicted), set(actual))
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "jaccard_similarity": jaccard
        }
    
    def get_aggregate_metrics(self) -> Dict[str, float]:
        """
        Get aggregate metrics across all results.
        
        Returns:
            Dictionary with mean, std, min, max for each metric
        """
        if not self.results:
            return {}
        
        metrics_by_type = defaultdict(list)
        
        for result in self.results:
            for metric_name, value in result["metrics"].items():
                metrics_by_type[metric_name].append(value)
        
        aggregate = {}
        for metric_name, values in metrics_by_type.items():
            aggregate[metric_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "count": len(values)
            }
        
        return aggregate
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get detailed accuracy report.
        
        Returns:
            Comprehensive report with individual and aggregate metrics
        """
        return {
            "individual_results": self.results,
            "aggregate_metrics": self.get_aggregate_metrics(),
            "summary": {
                "total_tests": len(self.results),
                "average_precision": np.mean([r["metrics"]["precision"] for r in self.results]),
                "average_recall": np.mean([r["metrics"]["recall"] for r in self.results]),
                "average_f1": np.mean([r["metrics"]["f1_score"] for r in self.results])
            }
        }


class GroundTruthValidator:
    """
    Validator for ground truth data quality.
    """
    
    @staticmethod
    def validate_ground_truth_format(ground_truth: Dict[str, Any]) -> List[str]:
        """
        Validate ground truth data format.
        
        Args:
            ground_truth: Ground truth data to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        required_fields = ["solicitation_id", "expected_researchers", "metadata"]
        for field in required_fields:
            if field not in ground_truth:
                errors.append(f"Missing required field: {field}")
        
        # Validate expected_researchers structure
        expected_researchers = ground_truth.get("expected_researchers", [])
        if not isinstance(expected_researchers, list):
            errors.append("expected_researchers must be a list")
        else:
            for i, researcher in enumerate(expected_researchers):
                if not isinstance(researcher, dict):
                    errors.append(f"Researcher {i} must be a dictionary")
                    continue
                
                if "researcher_id" not in researcher:
                    errors.append(f"Researcher {i} missing researcher_id")
                
                if "relevance_score" in researcher:
                    score = researcher["relevance_score"]
                    if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                        errors.append(f"Researcher {i} relevance_score must be between 0.0 and 1.0")
        
        return errors
    
    @staticmethod
    def load_ground_truth_from_file(file_path: str) -> Dict[str, Any]:
        """
        Load ground truth data from JSON file.
        
        Args:
            file_path: Path to ground truth JSON file
        
        Returns:
            Ground truth data dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            errors = GroundTruthValidator.validate_ground_truth_format(data)
            if errors:
                raise ValueError(f"Invalid ground truth format: {errors}")
            
            return data
        
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to load ground truth from {file_path}: {e}")


def compare_matching_algorithms(
    algorithm_results: Dict[str, List[Any]],
    ground_truth: List[Any]
) -> Dict[str, Dict[str, float]]:
    """
    Compare multiple matching algorithms against ground truth.
    
    Args:
        algorithm_results: Dictionary mapping algorithm names to their results
        ground_truth: Ground truth results
    
    Returns:
        Dictionary with metrics for each algorithm
    """
    comparison = {}
    
    for algorithm_name, results in algorithm_results.items():
        precision = calculate_precision(results, ground_truth)
        recall = calculate_recall(results, ground_truth)
        f1 = calculate_f1_score(precision, recall)
        jaccard = calculate_jaccard_similarity(set(results), set(ground_truth))
        
        comparison[algorithm_name] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "jaccard_similarity": jaccard
        }
    
    return comparison


def calculate_score_distribution_metrics(scores: List[float]) -> Dict[str, float]:
    """
    Calculate distribution metrics for matching scores.
    
    Args:
        scores: List of matching scores
    
    Returns:
        Dictionary with distribution statistics
    """
    if not scores:
        return {}
    
    scores_array = np.array(scores)
    
    return {
        "mean": float(np.mean(scores_array)),
        "median": float(np.median(scores_array)),
        "std": float(np.std(scores_array)),
        "min": float(np.min(scores_array)),
        "max": float(np.max(scores_array)),
        "q25": float(np.percentile(scores_array, 25)),
        "q75": float(np.percentile(scores_array, 75)),
        "iqr": float(np.percentile(scores_array, 75) - np.percentile(scores_array, 25))
    }


def calculate_diversity_metrics(
    team_members: List[Dict[str, Any]],
    diversity_fields: List[str] = None
) -> Dict[str, float]:
    """
    Calculate diversity metrics for team composition.
    
    Args:
        team_members: List of team member data
        diversity_fields: Fields to consider for diversity calculation
    
    Returns:
        Dictionary with diversity metrics
    """
    if not team_members:
        return {}
    
    if diversity_fields is None:
        diversity_fields = ["institution", "department", "expertise"]
    
    diversity_metrics = {}
    
    for field in diversity_fields:
        values = []
        for member in team_members:
            if field in member:
                value = member[field]
                if isinstance(value, list):
                    values.extend(value)
                else:
                    values.append(value)
        
        if values:
            unique_values = set(values)
            diversity_metrics[f"{field}_diversity"] = len(unique_values) / len(values)
            diversity_metrics[f"{field}_unique_count"] = len(unique_values)
    
    # Overall diversity score (average of individual diversities)
    diversity_scores = [v for k, v in diversity_metrics.items() if k.endswith("_diversity")]
    if diversity_scores:
        diversity_metrics["overall_diversity"] = np.mean(diversity_scores)
    
    return diversity_metrics


def calculate_coverage_metrics(
    predicted_items: List[Any],
    all_possible_items: List[Any]
) -> Dict[str, float]:
    """
    Calculate coverage metrics for recommendation systems.
    
    Args:
        predicted_items: Items that were predicted/recommended
        all_possible_items: All items that could be recommended
    
    Returns:
        Dictionary with coverage metrics
    """
    if not all_possible_items:
        return {"coverage": 0.0}
    
    predicted_set = set(predicted_items)
    all_items_set = set(all_possible_items)
    
    coverage = len(predicted_set.intersection(all_items_set)) / len(all_items_set)
    
    return {
        "coverage": coverage,
        "predicted_count": len(predicted_set),
        "total_possible": len(all_items_set),
        "covered_count": len(predicted_set.intersection(all_items_set))
    }


def calculate_temporal_accuracy(
    predictions_by_time: Dict[str, List[Any]],
    ground_truth_by_time: Dict[str, List[Any]]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate accuracy metrics over time periods.
    
    Args:
        predictions_by_time: Dictionary mapping time periods to predictions
        ground_truth_by_time: Dictionary mapping time periods to ground truth
    
    Returns:
        Dictionary with metrics for each time period
    """
    temporal_metrics = {}
    
    all_time_periods = set(predictions_by_time.keys()) | set(ground_truth_by_time.keys())
    
    for time_period in all_time_periods:
        predicted = predictions_by_time.get(time_period, [])
        actual = ground_truth_by_time.get(time_period, [])
        
        precision = calculate_precision(predicted, actual)
        recall = calculate_recall(predicted, actual)
        f1 = calculate_f1_score(precision, recall)
        
        temporal_metrics[time_period] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "predicted_count": len(predicted),
            "actual_count": len(actual)
        }
    
    return temporal_metrics


def calculate_threshold_metrics(
    scored_predictions: List[Tuple[Any, float]],
    ground_truth: List[Any],
    thresholds: List[float] = None
) -> Dict[float, Dict[str, float]]:
    """
    Calculate metrics at different score thresholds.
    
    Args:
        scored_predictions: List of (item, score) tuples
        ground_truth: Ground truth items
        thresholds: Score thresholds to evaluate
    
    Returns:
        Dictionary mapping thresholds to metrics
    """
    if thresholds is None:
        scores = [score for _, score in scored_predictions]
        if scores:
            thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        else:
            return {}
    
    threshold_metrics = {}
    ground_truth_set = set(ground_truth)
    
    for threshold in thresholds:
        # Filter predictions by threshold
        filtered_predictions = [item for item, score in scored_predictions if score >= threshold]
        
        # Calculate metrics
        precision = calculate_precision(filtered_predictions, ground_truth)
        recall = calculate_recall(filtered_predictions, ground_truth)
        f1 = calculate_f1_score(precision, recall)
        
        threshold_metrics[threshold] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "prediction_count": len(filtered_predictions),
            "threshold": threshold
        }
    
    return threshold_metrics


class MetricsAggregator:
    """
    Aggregates metrics across multiple test runs or datasets.
    """
    
    def __init__(self):
        self.metric_collections = []
    
    def add_metrics(self, metrics: Dict[str, float], metadata: Dict[str, Any] = None):
        """
        Add a set of metrics to the aggregator.
        
        Args:
            metrics: Dictionary of metric name to value
            metadata: Optional metadata about the metrics
        """
        self.metric_collections.append({
            "metrics": metrics,
            "metadata": metadata or {}
        })
    
    def get_aggregated_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated statistics across all metric collections.
        
        Returns:
            Dictionary with aggregated statistics for each metric
        """
        if not self.metric_collections:
            return {}
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for collection in self.metric_collections:
            for metric_name, value in collection["metrics"].items():
                if isinstance(value, (int, float)):
                    metrics_by_name[metric_name].append(value)
        
        # Calculate aggregated statistics
        aggregated = {}
        for metric_name, values in metrics_by_name.items():
            if values:
                aggregated[metric_name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "median": float(np.median(values)),
                    "count": len(values)
                }
        
        return aggregated
    
    def get_confidence_intervals(self, confidence_level: float = 0.95) -> Dict[str, Tuple[float, float]]:
        """
        Calculate confidence intervals for metrics.
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
        
        Returns:
            Dictionary mapping metric names to (lower_bound, upper_bound) tuples
        """
        from scipy import stats
        
        confidence_intervals = {}
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for collection in self.metric_collections:
            for metric_name, value in collection["metrics"].items():
                if isinstance(value, (int, float)):
                    metrics_by_name[metric_name].append(value)
        
        alpha = 1 - confidence_level
        
        for metric_name, values in metrics_by_name.items():
            if len(values) > 1:
                mean = np.mean(values)
                sem = stats.sem(values)  # Standard error of the mean
                h = sem * stats.t.ppf((1 + confidence_level) / 2., len(values) - 1)
                confidence_intervals[metric_name] = (mean - h, mean + h)
        
        return confidence_intervals


def validate_metric_thresholds(
    metrics: Dict[str, float],
    thresholds: Dict[str, float]
) -> Dict[str, bool]:
    """
    Validate that metrics meet specified thresholds.
    
    Args:
        metrics: Dictionary of metric values
        thresholds: Dictionary of minimum threshold values
    
    Returns:
        Dictionary indicating whether each metric meets its threshold
    """
    validation_results = {}
    
    for metric_name, threshold in thresholds.items():
        if metric_name in metrics:
            validation_results[metric_name] = metrics[metric_name] >= threshold
        else:
            validation_results[metric_name] = False
    
    return validation_results