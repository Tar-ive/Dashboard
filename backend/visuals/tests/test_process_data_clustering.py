#!/usr/bin/env python3
"""
Test script to verify the updated process_data.py clustering functionality
"""

import json
import numpy as np
from process_data import compute_clusters


def test_process_data_clustering():
    """Test the compute_clusters function from process_data.py"""
    print("🧪 Testing compute_clusters function from process_data.py...")
    
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
        
        # Test the compute_clusters function
        cluster_labels, cluster_info = compute_clusters(
            coordinates, 
            data_ids=data_ids, 
            save_model=True, 
            save_results=True
        )
        
        print(f"   📊 Cluster labels shape: {cluster_labels.shape}")
        print(f"   📊 Cluster info keys: {list(cluster_info.keys()) if cluster_info else 'None'}")
        
        # Verify cluster labels
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        print(f"   📊 Found {n_clusters} clusters with {n_noise} noise points")
        
        # Verify cluster info structure
        if cluster_info:
            for cluster_id, info in list(cluster_info.items())[:3]:  # Show first 3 clusters
                print(f"   📊 Cluster {cluster_id}: center={info['center']}, size={info['size']}")
        
        print("   ✅ compute_clusters function test completed successfully!")
        
        return cluster_labels, cluster_info
        
    except FileNotFoundError:
        print("   ❌ UMAP coordinates file not found. Run UMAP processing first.")
        return None, None
    except Exception as e:
        print(f"   ❌ Error during compute_clusters test: {e}")
        raise


if __name__ == "__main__":
    test_process_data_clustering()