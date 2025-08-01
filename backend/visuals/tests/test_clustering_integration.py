#!/usr/bin/env python3
"""
Test script to verify HDBSCAN clustering integration with existing UMAP coordinates
"""

import json
import numpy as np
from clustering_processor import ClusteringProcessor


def test_clustering_with_real_data():
    """Test clustering with the actual UMAP coordinates from the project"""
    print("🧪 Testing HDBSCAN clustering with real UMAP coordinates...")
    
    # Load existing UMAP coordinates
    try:
        with open('data/umap_coordinates.json', 'r') as f:
            umap_data = json.load(f)
        
        print(f"   📥 Loaded {len(umap_data['coordinates'])} UMAP coordinates")
        
        # Extract coordinates and IDs
        coordinates = []
        data_ids = []
        
        for coord in umap_data['coordinates']:
            coordinates.append([coord['x'], coord['y']])
            data_ids.append(coord['id'])
        
        coordinates = np.array(coordinates, dtype=np.float32)
        
        print(f"   📊 Coordinate ranges: X=[{coordinates[:, 0].min():.3f}, {coordinates[:, 0].max():.3f}], Y=[{coordinates[:, 1].min():.3f}, {coordinates[:, 1].max():.3f}]")
        
        # Initialize clustering processor
        processor = ClusteringProcessor(
            min_cluster_size=15,
            min_samples=None,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        # Perform clustering
        cluster_labels = processor.fit_predict(coordinates)
        
        # Get cluster information
        cluster_info = processor.get_cluster_info()
        cluster_centers = processor.calculate_cluster_centers()
        cluster_sizes = processor.get_cluster_sizes()
        
        print(f"   📊 Cluster centers ({len(cluster_centers)} clusters):")
        for cluster_id, center in cluster_centers.items():
            size = cluster_sizes[cluster_id]
            print(f"      Cluster {cluster_id}: center=({center[0]:.3f}, {center[1]:.3f}), size={size}")
        
        # Save clustering results
        processor.save_cluster_results(coordinates, data_ids, 'data/test_clustering_results.json')
        
        # Test model saving
        processor.save_model('models/test_hdbscan_model.pkl')
        
        print("   ✅ Clustering integration test completed successfully!")
        
        return cluster_labels, cluster_info
        
    except FileNotFoundError:
        print("   ❌ UMAP coordinates file not found. Run UMAP processing first.")
        return None, None
    except Exception as e:
        print(f"   ❌ Error during clustering integration test: {e}")
        raise


if __name__ == "__main__":
    test_clustering_with_real_data()