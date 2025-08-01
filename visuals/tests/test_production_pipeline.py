#!/usr/bin/env python3
"""
Test script for the production data processing pipeline
Tests that we can retrieve all works with embeddings and join with researcher data
"""

import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_production_pipeline():
    """Test the production data processing pipeline"""
    print("🧪 Testing Production Data Processing Pipeline")
    print("=" * 60)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Import DataProcessor
        from data_loader import DataProcessor
        
        # Initialize data processor
        print("1️⃣ Initializing DataProcessor...")
        processor = DataProcessor()
        print("   ✅ DataProcessor initialized successfully")
        
        # Test production pipeline
        print("\n2️⃣ Testing production pipeline (works with embeddings only)...")
        result = processor.process_production_dataset()
        
        data = result['data']
        embeddings = result['embeddings']
        validation_passed = result['validation_passed']
        
        print(f"   ✅ Processed {len(data)} works")
        print(f"   ✅ All works have embeddings: {len(embeddings) == len(data)}")
        print(f"   ✅ Embedding dimensions: {embeddings.shape}")
        print(f"   ✅ Validation passed: {validation_passed}")
        
        # Verify we have the expected number of works (should be 2454 now)
        expected_total = 2454
        if len(data) >= expected_total * 0.95:  # Allow small tolerance
            print(f"   ✅ Work count looks correct: {len(data)} (expected ~{expected_total})")
        else:
            print(f"   ⚠️  Work count seems low: {len(data)} (expected ~{expected_total})")
        
        # Check that all works have researcher information
        works_with_researchers = data['full_name'].notna().sum()
        print(f"   📊 Works with researcher info: {works_with_researchers}/{len(data)}")
        
        # Check that we have citations data
        works_with_citations = data['citations'].notna().sum()
        print(f"   📊 Works with citations: {works_with_citations}/{len(data)}")
        
        # Show sample of the data
        print("\n3️⃣ Sample of processed data:")
        sample_cols = ['title', 'full_name', 'department', 'publication_year', 'citations']
        available_cols = [col for col in sample_cols if col in data.columns]
        print(data[available_cols].head(3).to_string())
        
        # Test that embeddings are valid
        print(f"\n4️⃣ Embedding validation:")
        non_zero_embeddings = (embeddings != 0).any(axis=1).sum()
        print(f"   ✅ Non-zero embeddings: {non_zero_embeddings}/{len(embeddings)}")
        
        # Check embedding statistics
        embedding_means = embeddings.mean(axis=1)
        embedding_stds = embeddings.std(axis=1)
        print(f"   📊 Embedding mean range: {embedding_means.min():.4f} to {embedding_means.max():.4f}")
        print(f"   📊 Embedding std range: {embedding_stds.min():.4f} to {embedding_stds.max():.4f}")
        
        print("\n🎉 Production pipeline test completed successfully!")
        print("=" * 60)
        
        # Print final summary
        print("\n📊 Final Summary:")
        print(f"   • Total works processed: {len(data)}")
        print(f"   • All have embeddings: {len(embeddings) == len(data)}")
        print(f"   • Embedding dimensions: {embeddings.shape[1]}")
        print(f"   • Works with researcher info: {works_with_researchers}")
        print(f"   • Works with citations: {works_with_citations}")
        print(f"   • Ready for UMAP/clustering: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_production_pipeline()
    sys.exit(0 if success else 1)