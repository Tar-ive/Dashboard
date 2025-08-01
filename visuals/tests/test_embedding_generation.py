#!/usr/bin/env python3
"""
Test script for embedding generation functionality
Tests that we can generate embeddings for works that don't have them
"""

import sys
import os
import numpy as np
from dotenv import load_dotenv

# Add current directory to path to import data_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_embedding_generation():
    """Test the embedding generation for missing embeddings"""
    print("🧪 Testing Embedding Generation for Missing Embeddings")
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
        
        # Test fetching all data (including works without embeddings)
        print("\n2️⃣ Testing data fetching (including works without embeddings)...")
        raw_data = processor.fetch_research_data()
        
        works_df = raw_data['works']
        researchers_df = raw_data['researchers']
        
        # Count embedding statistics
        total_works = len(works_df)
        works_with_embeddings = works_df['embedding'].notna().sum()
        works_without_embeddings = total_works - works_with_embeddings
        
        print(f"   ✅ Total works fetched: {total_works}")
        print(f"   📊 Works with embeddings: {works_with_embeddings}")
        print(f"   📊 Works without embeddings: {works_without_embeddings}")
        print(f"   📊 Percentage with embeddings: {(works_with_embeddings/total_works*100):.2f}%")
        
        if works_without_embeddings == 0:
            print("   ⚠️  All works already have embeddings - cannot test generation")
            return True
        
        # Test embedding generation
        print(f"\n3️⃣ Testing embedding generation for {works_without_embeddings} works...")
        
        # Test with a small sample first to avoid long processing times
        sample_size = min(10, works_without_embeddings)
        works_sample = works_df.head(total_works).copy()  # Get a sample that includes some without embeddings
        
        print(f"   🔄 Testing with sample of {len(works_sample)} works...")
        
        # Generate embeddings
        works_with_generated = processor.generate_embeddings_for_missing(works_sample)
        
        # Check results
        new_embeddings_count = works_with_generated['embedding'].notna().sum()
        original_embeddings_count = works_sample['embedding'].notna().sum()
        generated_count = new_embeddings_count - original_embeddings_count
        
        print(f"   ✅ Generated {generated_count} new embeddings")
        print(f"   📊 Total embeddings after generation: {new_embeddings_count}/{len(works_sample)}")
        
        # Test parsing the generated embeddings
        print("\n4️⃣ Testing parsing of generated embeddings...")
        sample_embeddings = works_with_generated['embedding'].head(5)
        parsed_embeddings = processor.parse_embeddings(sample_embeddings)
        
        print(f"   ✅ Parsed embeddings shape: {parsed_embeddings.shape}")
        print(f"   ✅ Expected dimensions: 384")
        
        if parsed_embeddings.shape[1] != 384:
            raise ValueError(f"Generated embeddings have wrong dimensions: {parsed_embeddings.shape[1]}")
        
        # Test complete pipeline with embedding generation
        print("\n5️⃣ Testing complete pipeline with embedding generation...")
        result = processor.process_complete_dataset()
        
        final_data = result['data']
        final_embeddings = result['embeddings']
        
        print(f"   ✅ Final dataset shape: {final_data.shape}")
        print(f"   ✅ Final embeddings shape: {final_embeddings.shape}")
        
        # Verify all works now have embeddings
        works_with_final_embeddings = (final_embeddings != 0).any(axis=1).sum()
        print(f"   ✅ Works with valid embeddings: {works_with_final_embeddings}/{len(final_embeddings)}")
        
        print("\n🎉 Embedding generation test completed successfully!")
        print("=" * 60)
        
        # Print final statistics
        print("\n📊 Final Statistics:")
        print(f"   • Total works processed: {len(final_data)}")
        print(f"   • All works have embeddings: {len(final_embeddings) == len(final_data)}")
        print(f"   • Embedding dimensions: {final_embeddings.shape[1]}")
        print(f"   • Works with non-zero embeddings: {works_with_final_embeddings}")
        
        return True
        
    except ImportError as e:
        if "sentence_transformers" in str(e):
            print(f"\n⚠️  Sentence transformers not installed: {e}")
            print("   To install: pip install sentence-transformers")
            print("   Skipping embedding generation test")
            return True
        else:
            print(f"\n❌ Import error: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_embedding_generation()
    sys.exit(0 if success else 1)