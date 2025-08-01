#!/usr/bin/env python3
"""
Test script for core data processing pipeline
Tests the three main requirements:
1. Fetch works and researchers from Supabase
2. Parse pgvector embeddings from string format to NumPy arrays
3. Join works with researcher data to get researcher names and departments
"""

import sys
import os
import numpy as np
from dotenv import load_dotenv

# Add current directory to path to import data_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataProcessor

def test_core_data_processing():
    """Test the core data processing pipeline"""
    print("🧪 Testing Core Data Processing Pipeline")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize data processor
        print("1️⃣ Initializing DataProcessor...")
        processor = DataProcessor()
        print("   ✅ DataProcessor initialized successfully")
        
        # Test 1: Fetch works and researchers from Supabase
        print("\n2️⃣ Testing data fetching from Supabase...")
        raw_data = processor.fetch_research_data()
        
        works_df = raw_data['works']
        researchers_df = raw_data['researchers']
        
        print(f"   ✅ Fetched {len(works_df)} works")
        print(f"   ✅ Fetched {len(researchers_df)} researchers")
        
        # Verify required columns exist
        required_work_cols = ['id', 'researcher_id', 'title', 'embedding']
        required_researcher_cols = ['id', 'full_name', 'department']
        
        for col in required_work_cols:
            if col not in works_df.columns:
                raise ValueError(f"Missing required column in works: {col}")
        
        for col in required_researcher_cols:
            if col not in researchers_df.columns:
                raise ValueError(f"Missing required column in researchers: {col}")
        
        print("   ✅ All required columns present")
        
        # Test 2: Parse pgvector embeddings
        print("\n3️⃣ Testing embedding parsing...")
        
        # Get a sample of embeddings to test
        sample_embeddings = works_df['embedding'].head(10)
        parsed_embeddings = processor.parse_embeddings(sample_embeddings)
        
        print(f"   ✅ Parsed embeddings shape: {parsed_embeddings.shape}")
        print(f"   ✅ Expected shape: ({len(sample_embeddings)}, 384)")
        
        # Verify shape is correct
        if parsed_embeddings.shape != (len(sample_embeddings), 384):
            raise ValueError(f"Unexpected embedding shape: {parsed_embeddings.shape}")
        
        # Verify data type
        if parsed_embeddings.dtype != np.float32:
            print(f"   ⚠️  Warning: Expected float32, got {parsed_embeddings.dtype}")
        
        # Test 3: Join works with researcher data
        print("\n4️⃣ Testing data joining...")
        merged_data = processor.join_works_researchers(raw_data)
        
        print(f"   ✅ Joined data shape: {merged_data.shape}")
        
        # Verify join worked correctly
        if len(merged_data) != len(works_df):
            print(f"   ⚠️  Warning: Joined data length ({len(merged_data)}) != works length ({len(works_df)})")
        
        # Check that researcher names and departments are present
        if 'full_name' not in merged_data.columns:
            raise ValueError("Missing 'full_name' column after join")
        if 'department' not in merged_data.columns:
            raise ValueError("Missing 'department' column after join")
        
        # Count how many works have researcher info
        works_with_researchers = merged_data['full_name'].notna().sum()
        print(f"   ✅ {works_with_researchers}/{len(merged_data)} works have researcher information")
        
        # Test 4: Complete pipeline
        print("\n5️⃣ Testing complete processing pipeline...")
        result = processor.process_complete_dataset()
        
        final_data = result['data']
        final_embeddings = result['embeddings']
        validation_passed = result['validation_passed']
        
        print(f"   ✅ Final dataset shape: {final_data.shape}")
        print(f"   ✅ Final embeddings shape: {final_embeddings.shape}")
        print(f"   ✅ Validation passed: {validation_passed}")
        
        # Verify embeddings are in the final data
        if 'parsed_embeddings' not in final_data.columns:
            raise ValueError("Missing 'parsed_embeddings' column in final data")
        
        print("\n🎉 All tests passed successfully!")
        print("=" * 50)
        
        # Print summary statistics
        print("\n📊 Summary Statistics:")
        print(f"   • Total works: {len(final_data)}")
        print(f"   • Total researchers: {len(researchers_df)}")
        print(f"   • Works with embeddings: {(final_embeddings != 0).any(axis=1).sum()}")
        print(f"   • Works with researcher info: {final_data['full_name'].notna().sum()}")
        print(f"   • Unique departments: {final_data['department'].nunique()}")
        print(f"   • Year range: {final_data['publication_year'].min()}-{final_data['publication_year'].max()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_core_data_processing()
    sys.exit(0 if success else 1)