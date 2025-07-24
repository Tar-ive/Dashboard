# Product Overview

## AI-Powered Research Team Matching & Assembly System

This is a Streamlit-based AI application that analyzes research solicitations and assembles optimal research teams by matching researchers to project requirements.

### Core Functionality
- **Solicitation Analysis**: Processes research funding opportunities and extracts skill requirements
- **Researcher Matching**: Scores individual researchers using hybrid TF-IDF and semantic similarity algorithms
- **Team Assembly**: Uses optimization algorithms to build dream teams that maximize coverage of required skills
- **Strategic Reporting**: Generates AI-powered analysis and recommendations using Groq API integration

### Key Features
- Handles large datasets of researcher profiles and publications
- Supports both sparse (TF-IDF) and dense (sentence embeddings) text matching
- Provides interactive web interface with step-by-step workflow
- Generates comprehensive reports with evidence and strategic analysis
- Graceful fallback when optional AI services are unavailable

### Target Users
Research administrators, funding agencies, and project managers who need to identify and assemble optimal research teams for specific solicitations and funding opportunities.