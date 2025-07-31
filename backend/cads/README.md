# CADS (Computer Science Department) Research Database

This folder contains all code, data, and documentation related to the Computer Science Department (CADS) research database subset at Texas State University.

## 📁 Folder Structure

```
cads/
├── README.md                 # This file
├── data/                     # CADS data files
│   ├── cads.txt             # List of 55 CADS professors
│   └── cads_search_patterns.json  # Name matching patterns
├── scripts/                  # CADS-specific scripts
│   ├── Migration Scripts/
│   ├── Data Processing/
│   └── Analysis Tools/
├── sql/                      # SQL files for CADS tables
│   ├── create_cads_tables.sql
│   └── create_cads_tables_simple.sql
├── logs/                     # Execution logs
└── docs/                     # Documentation
    ├── cads_migration_report.md
    └── supabase_connection_issue_analysis.md
```

## 🎯 Purpose

The CADS database contains a specialized subset of research data focused on the Computer Science Department faculty at Texas State University. This includes:

- **32 CADS professors** with complete research profiles
- **2,454 research publications** with full metadata
- **6,834 research topics** for semantic analysis
- **81,939+ total citations** captured
- **Vector embeddings** for semantic search capabilities

## 📊 Database Schema

### CADS Tables
- `cads_researchers` - Computer Science faculty profiles
- `cads_works` - Research publications by CADS faculty
- `cads_topics` - Research topics extracted from publications
- `cads_researcher_summary` - Aggregated statistics view

## 🚀 Key Scripts

### Migration Scripts
- `execute_cads_migration_ipv4_pooler.py` - **Main migration script** (working version)
- `migrate_cads_data_to_cads_tables.py` - Migrate data from main tables to CADS tables
- `create_cads_subset.py` - Original CADS subset creation
- `create_cads_subset_supabase.py` - Supabase-specific migration

### Data Processing
- `process_cads_with_openalex_ids.py` - Process all CADS professors using OpenAlex IDs
- `process_all_cads_professors.py` - Alternative processing approach
- `check_cads_data_location.py` - Verify where CADS data is stored

### Analysis Tools
- `check_existing_cads_data.py` - Analyze existing CADS data
- `test_cads_parsing.py` - Test CADS data parsing

## 📈 Data Statistics

### Current CADS Database Content
- **Researchers**: 32 CADS professors
- **Publications**: 2,454 research works
- **Topics**: 6,834 research topics
- **Citations**: 81,939+ total citations
- **Time Range**: 1999-2025
- **Research Areas**: Computer Science, AI/ML, Data Science, Engineering

### Top Productive Researchers
- **Chul-Ho Lee**: 422 works
- **Togay Ozbakkaloglu**: 354 works  
- **Subasish Das**: 345 works
- **Mylene Farias**: 206 works
- **Tongdan Jin**: 188 works

## 🔧 Usage

### Running the Migration
```bash
# Main migration script (recommended)
python cads/scripts/execute_cads_migration_ipv4_pooler.py

# Process all CADS professors with known OpenAlex IDs
python cads/scripts/process_cads_with_openalex_ids.py

# Migrate data from main tables to CADS tables
python cads/scripts/migrate_cads_data_to_cads_tables.py
```

### Database Connection
All scripts use the IPv4 pooler connection configuration:
- Host: `aws-0-us-east-2.pooler.supabase.com`
- Port: `5432`
- Database: `postgres`
- User: `postgres.zsezliiffdcgqekwggjq`

## 🔍 Key Features

### Semantic Search
- 384-dimensional vector embeddings for all publications
- Cosine similarity search for finding related research
- Topic-based expertise discovery

### Full-Text Search
- GIN indexes on titles and abstracts
- Keyword-based publication discovery
- Multi-field search capabilities

### Citation Analysis
- Real-time citation tracking from OpenAlex
- Impact assessment and trend analysis
- Collaboration network discovery

## 📝 Documentation

### Migration Reports
- `docs/cads_migration_report.md` - Comprehensive migration documentation
- `docs/supabase_connection_issue_analysis.md` - Connection troubleshooting guide

### Database Schema
- Complete schema documentation in main `database_schema_documentation.md`
- Relationship diagrams and data flow documentation

## 🐛 Troubleshooting

### Common Issues
1. **IPv6 Connection Issues**: Use IPv4 pooler connection
2. **DNS Resolution**: Check network configuration
3. **Data Location**: Verify data is in CADS tables, not main tables

### Connection Testing
```bash
python cads/scripts/check_cads_data_location.py
```

## 🎯 Future Enhancements

### Planned Features
- Real-time collaboration recommendation engine
- Advanced research trend analysis
- Grant opportunity matching
- Cross-departmental collaboration discovery

### Data Expansion
- Additional faculty metadata
- Grant and funding information
- Conference and journal impact metrics
- Student collaboration tracking

## 📞 Support

For issues with CADS database:
1. Check connection using IPv4 pooler
2. Verify data location in CADS tables
3. Review migration logs in `logs/` directory
4. Consult troubleshooting documentation

## 🏆 Success Metrics

The CADS database migration achieved:
- ✅ 100% success rate for professors with OpenAlex profiles
- ✅ Complete research portfolio capture
- ✅ Semantic search capabilities enabled
- ✅ Real-time citation tracking implemented
- ✅ Topic extraction and analysis ready

This CADS research database serves as a comprehensive foundation for academic collaboration discovery and research analytics at Texas State University's Computer Science Department.