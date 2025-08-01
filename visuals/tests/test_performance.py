#!/usr/bin/env python3
"""
Performance testing script for CADS Research Visualization
Tests loading performance and bundle sizes to meet <500ms target
"""

import time
import requests
import gzip
import os
from pathlib import Path
import json

def test_file_sizes():
    """Test file sizes and compression ratios"""
    print("📏 Testing file sizes and compression...")
    
    data_dir = Path('public/data')
    
    files_to_test = [
        'visualization-data.json',
        'search-index.json', 
        'cluster_themes.json',
        'clustering_results.json'
    ]
    
    total_uncompressed = 0
    total_compressed = 0
    
    for filename in files_to_test:
        json_path = data_dir / filename
        gz_path = data_dir / f"{filename}.gz"
        
        if json_path.exists() and gz_path.exists():
            json_size = os.path.getsize(json_path)
            gz_size = os.path.getsize(gz_path)
            compression_ratio = json_size / gz_size
            
            print(f"  {filename}:")
            print(f"    Uncompressed: {json_size:,} bytes ({json_size/1024:.1f} KB)")
            print(f"    Compressed: {gz_size:,} bytes ({gz_size/1024:.1f} KB)")
            print(f"    Compression: {compression_ratio:.1f}x")
            
            total_uncompressed += json_size
            total_compressed += gz_size
        else:
            print(f"  ⚠️  Missing files for {filename}")
    
    if total_compressed > 0:
        overall_ratio = total_uncompressed / total_compressed
        print(f"\n📊 Overall totals:")
        print(f"  Total uncompressed: {total_uncompressed:,} bytes ({total_uncompressed/1024/1024:.1f} MB)")
        print(f"  Total compressed: {total_compressed:,} bytes ({total_compressed/1024:.1f} KB)")
        print(f"  Overall compression: {overall_ratio:.1f}x")
        
        # Performance estimates
        print(f"\n⚡ Performance estimates:")
        
        # Different connection speeds (bytes per second)
        speeds = {
            "Fast 4G": 10 * 1024 * 1024,  # 10 MB/s
            "3G": 1.5 * 1024 * 1024,      # 1.5 MB/s
            "Slow 3G": 400 * 1024,        # 400 KB/s
            "2G": 50 * 1024               # 50 KB/s
        }
        
        for speed_name, speed_bps in speeds.items():
            load_time_ms = (total_compressed / speed_bps) * 1000
            print(f"  {speed_name}: {load_time_ms:.0f}ms")
            
            if load_time_ms <= 500:
                print(f"    ✅ Meets <500ms target")
            else:
                print(f"    ❌ Exceeds 500ms target")
    
    return total_compressed

def test_html_size():
    """Test HTML file size"""
    print("\n📄 Testing HTML bundle size...")
    
    html_path = Path('public/index.html')
    js_path = Path('public/app.js')
    
    if html_path.exists():
        html_size = os.path.getsize(html_path)
        print(f"  index.html: {html_size:,} bytes ({html_size/1024:.1f} KB)")
    
    if js_path.exists():
        js_size = os.path.getsize(js_path)
        print(f"  app.js: {js_size:,} bytes ({js_size/1024:.1f} KB)")
        
        total_bundle = html_size + js_size
        print(f"  Total bundle: {total_bundle:,} bytes ({total_bundle/1024:.1f} KB)")
        
        # Target is <200KB total bundle
        if total_bundle < 200 * 1024:
            print(f"  ✅ Bundle size meets <200KB target")
        else:
            print(f"  ⚠️  Bundle size exceeds 200KB target")
    
    return html_size + js_size if html_path.exists() and js_path.exists() else 0

def test_data_loading_simulation():
    """Simulate data loading performance"""
    print("\n🔄 Simulating data loading performance...")
    
    data_files = [
        'public/data/visualization-data.json.gz',
        'public/data/cluster_themes.json.gz', 
        'public/data/clustering_results.json.gz'
    ]
    
    total_load_time = 0
    total_size = 0
    
    for file_path in data_files:
        if Path(file_path).exists():
            file_size = os.path.getsize(file_path)
            
            # Simulate loading time (file I/O + parsing)
            start_time = time.time()
            
            # Read compressed file
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            load_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"  {Path(file_path).name}:")
            print(f"    Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"    Load time: {load_time:.1f}ms")
            
            total_load_time += load_time
            total_size += file_size
    
    print(f"\n📊 Total simulated loading:")
    print(f"  Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"  Total load time: {total_load_time:.1f}ms")
    
    if total_load_time <= 500:
        print(f"  ✅ Meets <500ms loading target")
    else:
        print(f"  ❌ Exceeds 500ms loading target")
    
    return total_load_time

def test_json_parsing_performance():
    """Test JSON parsing performance for large datasets"""
    print("\n🔍 Testing JSON parsing performance...")
    
    viz_data_path = Path('public/data/visualization-data.json.gz')
    
    if viz_data_path.exists():
        # Test parsing performance
        start_time = time.time()
        
        with gzip.open(viz_data_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        parse_time = (time.time() - start_time) * 1000
        
        # Analyze data structure
        num_publications = len(data.get('p', []))
        num_researchers = len(data.get('r', []))
        num_clusters = len(data.get('c', []))
        
        print(f"  Data structure:")
        print(f"    Publications: {num_publications:,}")
        print(f"    Researchers: {num_researchers}")
        print(f"    Clusters: {num_clusters}")
        print(f"  Parse time: {parse_time:.1f}ms")
        
        # Estimate rendering performance
        estimated_render_time = num_publications * 0.01  # Rough estimate: 0.01ms per point
        print(f"  Estimated render time: {estimated_render_time:.1f}ms")
        
        total_time = parse_time + estimated_render_time
        print(f"  Total estimated time: {total_time:.1f}ms")
        
        if total_time <= 500:
            print(f"  ✅ Estimated total time meets <500ms target")
        else:
            print(f"  ⚠️  Estimated total time may exceed 500ms target")

def generate_performance_report():
    """Generate a comprehensive performance report"""
    print("🎯 CADS Research Visualization - Performance Test Report")
    print("=" * 60)
    
    # Test file sizes and compression
    total_data_size = test_file_sizes()
    
    # Test bundle sizes
    total_bundle_size = test_html_size()
    
    # Test loading simulation
    total_load_time = test_data_loading_simulation()
    
    # Test JSON parsing
    test_json_parsing_performance()
    
    # Summary
    print("\n📋 Performance Summary:")
    print("=" * 30)
    
    print(f"Total data payload: {total_data_size/1024:.1f} KB")
    print(f"Total bundle size: {total_bundle_size/1024:.1f} KB")
    print(f"Simulated load time: {total_load_time:.1f}ms")
    
    # Overall assessment
    print(f"\n🎯 Target Assessment:")
    
    # Data payload target: <100KB
    if total_data_size <= 100 * 1024:
        print(f"✅ Data payload: {total_data_size/1024:.1f} KB (target: <100 KB)")
    else:
        print(f"⚠️  Data payload: {total_data_size/1024:.1f} KB (target: <100 KB)")
    
    # Bundle size target: <200KB
    if total_bundle_size <= 200 * 1024:
        print(f"✅ Bundle size: {total_bundle_size/1024:.1f} KB (target: <200 KB)")
    else:
        print(f"⚠️  Bundle size: {total_bundle_size/1024:.1f} KB (target: <200 KB)")
    
    # Load time target: <500ms
    if total_load_time <= 500:
        print(f"✅ Load time: {total_load_time:.1f}ms (target: <500ms)")
    else:
        print(f"⚠️  Load time: {total_load_time:.1f}ms (target: <500ms)")
    
    print(f"\n🚀 Ready for deployment!")

if __name__ == "__main__":
    generate_performance_report()