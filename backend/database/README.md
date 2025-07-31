# Database Project

This folder contains the implementation for populating a Supabase database with Texas State University researcher data from the OpenAlex API.

## Project Structure

- `requirements.md` - Feature requirements document
- `design.md` - Technical design document  
- `tasks.md` - Implementation task list
- `schema.sql` - Database schema definition with all tables, indexes, and constraints
- `create_tables.py` - Script to create database tables and test relationships
- `verify_schema.py` - Script to verify database schema is correctly configured
- `main.py` - Main database population script (to be implemented)
- `test_*.py` - Test files

## Database Schema

The database consists of five main tables:

### Tables Created
- **institutions** - University/institution information (6 columns)
- **researchers** - Faculty/researcher profiles (8 columns)  
- **works** - Publications with vector embeddings (12 columns)
- **topics** - Research topics extracted from publications (6 columns)
- **researcher_grants** - Grant/funding information (8 columns)

### Key Features
- **Vector Support**: Enabled `pg_vector` extension for 384-dimensional embeddings
- **Full-text Search**: GIN indexes on title and abstract fields
- **Foreign Key Relationships**: Proper referential integrity between all tables
- **Performance Indexes**: Optimized indexes for common query patterns
- **Data Validation**: Check constraints for data quality (positive values, valid years, etc.)
- **Automatic Timestamps**: Created/updated timestamp tracking with triggers

## Usage

### Create Database Tables
```bash
python database/create_tables.py
```

This script will:
1. Enable required PostgreSQL extensions (vector, uuid-ossp)
2. Create all five tables with proper relationships
3. Add performance indexes and constraints
4. Test table relationships with sample data
5. Verify vector similarity functionality

### Verify Schema
```bash
python database/verify_schema.py
```

This script provides a detailed report of:
- All tables and column counts
- Database indexes
- Foreign key relationships  
- Enabled extensions
- Data validation constraints

## Requirements

- Python 3.7+
- psycopg2-binary
- python-dotenv
- Supabase database with `DATABASE_URL` configured in `.env`