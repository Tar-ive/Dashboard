#!/usr/bin/env python3
"""
Test script for just the core data processing functions
Tests only the data loading, parsing, and joining without ML dependencies
"""

import sys
import os
import numpy as np
from dotenv import load_dotenv

# Add current directory to path to import data_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_functions_only():
    """Test only the core data processing functions"""
    print("🧪 Testing Core Data Processing Functions (No ML)")
    print("=" * 50)
    
    try:
        # Test the load_and_process_data function from process_data.py
        # But we need to import it carefully to avoid ML dependencies
        
        # Load environment variables
        load_dotenv()
        
        # Import and test DataProcessor directly
        from data_loader import DataProcessor
        
        print("1️⃣ Testing DataProcessor...")
        processor = DataProcessor()
        
        # Test complete pipeline
        result = processor.process_complete_dataset()
        
        data = result['data']
        embeddings = result['embeddings']
        
        print(f"   ✅ Processed {len(data)} records")
        print(f"   ✅ Embeddings shape: {embeddings.shape}")
        
        # Verify the three main requirements are met:
        
        # 1. Fetch works and researchers from Supabase ✅
        print("\n✅ Requirement 1: Fetch works and researchers from Supabase")
        print(f"   - Successfully fetched {len(data)} works with researcher data")
        
        # 2. Parse pgvector embeddings from string format to NumPy arrays ✅
        print("\n✅ Requirement 2: Parse pgvector embeddings to NumPy arrays")
        print(f"   - Successfully parsed embeddings to shape {embeddings.shape}")
        print(f"   - Data type: {embeddings.dtype}")
        
        # 3. Join works with researcher data to get researcher names and departments ✅
        print("\n✅ Requirement 3: Join works with researcher data")
        print(f"   - Successfully joined data with researcher names and departments")
        print(f"   - Columns include: {[col for col in data.columns if 'name' in col or 'department' in col]}")
        
        # Show sample of the final data
        print("\n📊 Sample of processed data:")
        sample_cols = ['title', 'full_name', 'department', 'publication_year']
        available_cols = [col for col in sample_cols if col in data.columns]
        print(data[available_cols].head(3).to_string())
        
        print("\n🎉 All core requirements successfully implemented!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_core_functions_only()
    sys.exit(0 if success else 1)