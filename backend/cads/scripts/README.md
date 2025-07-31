# CADS Scripts Directory

This directory contains all scripts related to CADS (Computer Science Department) data processing and migration.

## 📁 Script Categories

### 🚀 Migration Scripts (Primary)

#### Main Migration Script
- **`execute_cads_migration_ipv4_pooler.py`** - ✅ **WORKING VERSION**
  - Uses IPv4 pooler connection (recommended)
  - Creates CADS tables and migrates data
  - Handles SQL syntax issues properly

#### Alternative Migration Approaches
- `execute_cads_migration_direct.py` - Direct DATABASE_URL connection (has IPv6 issues)
- `execute_cads_migration_alternative.py` - Multiple connection methods
- `execute_cads_migration_fixed.py` - DNS resolution fix attempt
- `execute_cads_migration_ipv6.py` - IPv6 specific approach
- `execute_cads_migration_port_6543.py` - Port 6543 testing
- `execute_cads_migration_retry.py` - Retry logic implementation
- `execute_cads_migration.py` - Original migration script

### 📊 Data Processing Scripts

#### OpenAlex Integration
- **`process_cads_with_openalex_ids.py`** - ✅ **RECOMMENDED**
  - Processes all 42 CADS professors using known OpenAlex IDs
  - Most reliable approach for data collection
  - Handles all professors with confirmed OpenAlex profiles

- `process_all_cads_professors.py` - Alternative processing approach
  - Searches for professors by name matching
  - Less reliable due to name variations

#### Data Migration and Organization
- **`migrate_cads_data_to_cads_tables.py`** - ✅ **ESSENTIAL**
  - Migrates data from main tables to CADS-specific tables
  - Fixes data location issues
  - Required after running main processing scripts

### 🔍 Analysis and Verification Scripts

#### Data Location and Verification
- `check_cads_data_location.py` - Verify where CADS data is stored
- `check_existing_cads_data.py` - Analyze existing CADS data
- `test_cads_parsing.py` - Test CADS data parsing functionality

#### Legacy Creation Scripts
- `create_cads_subset.py` - Original CADS subset creation
- `create_cads_subset_supabase.py` - Supabase-specific subset creation

## 🎯 Recommended Workflow

### For Fresh CADS Database Setup:
```bash
# Step 1: Create CADS tables and basic structure
python cads/scripts/execute_cads_migration_ipv4_pooler.py

# Step 2: Process all CADS professors with OpenAlex IDs
python cads/scripts/process_cads_with_openalex_ids.py

# Step 3: Migrate data to CADS-specific tables
python cads/scripts/migrate_cads_data_to_cads_tables.py

# Step 4: Verify data location and completeness
python cads/scripts/check_cads_data_location.py
```

### For Data Verification:
```bash
# Check where data is located
python cads/scripts/check_cads_data_location.py

# Analyze existing data
python cads/scripts/check_existing_cads_data.py
```

## ⚠️ Important Notes

### Connection Requirements
- All scripts require IPv4 pooler connection configuration
- DNS resolution issues prevent direct hostname connections
- Use environment variables from `.env` file

### Data Location
- Initial processing stores data in main tables (`researchers`, `works`, `topics`)
- Migration script moves data to CADS tables (`cads_researchers`, `cads_works`, `cads_topics`)
- Always verify final data location after processing

### Script Dependencies
- All scripts require database connection via IPv4 pooler
- OpenAlex API access for data retrieval
- Proper environment configuration in `.env` file

## 🔧 Environment Setup

### Required Environment Variables
```bash
# IPv4 Pooler Connection
user=postgres.zsezliiffdcgqekwggjq
password=cadstxst2025
host=aws-0-us-east-2.pooler.supabase.com
port=5432
dbname=postgres

# OpenAlex API
OPENALEX_EMAIL=test@texasstate.edu
```

## 📈 Success Metrics

### Expected Results After Full Workflow:
- **32 CADS researchers** in `cads_researchers` table
- **2,454+ research works** in `cads_works` table
- **6,834+ research topics** in `cads_topics` table
- **Complete semantic embeddings** for all works
- **Citation data** and publication metadata

## 🐛 Troubleshooting

### Common Issues:
1. **IPv6 Connection Errors**: Use IPv4 pooler scripts only
2. **Data in Wrong Tables**: Run migration script to move to CADS tables
3. **Missing OpenAlex Data**: Check API rate limits and network connectivity
4. **SQL Syntax Errors**: Use the IPv4 pooler version which handles syntax properly

### Debug Scripts:
- `check_cads_data_location.py` - Verify data location
- Connection diagnostic tools in main scripts directory

## 📝 Logging

All scripts generate detailed logs:
- Execution logs saved to `cads/logs/` directory
- Error tracking and progress monitoring
- Performance metrics and success rates

## 🎯 Script Status

| Script | Status | Purpose | Recommended |
|--------|--------|---------|-------------|
| `execute_cads_migration_ipv4_pooler.py` | ✅ Working | Main migration | Yes |
| `process_cads_with_openalex_ids.py` | ✅ Working | Data processing | Yes |
| `migrate_cads_data_to_cads_tables.py` | ✅ Working | Data organization | Yes |
| `check_cads_data_location.py` | ✅ Working | Verification | Yes |
| Other migration scripts | ⚠️ Issues | Alternative approaches | No |

Use the recommended scripts for reliable CADS database setup and maintenance.