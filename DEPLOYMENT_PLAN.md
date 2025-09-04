# 🚀 Sentry + Vercel Deployment Plan for Streamlit Dashboard

## Phase 1: Sentry Integration Setup

### 1.1 Core Sentry Initialization
- **Modify `app.py:15`**: Add Sentry SDK import and initialization after `load_dotenv()`
- **Enhance `app.py:18-23`**: Extend environment variable loading to include `SENTRY_DSN`
- **Update `requirements.txt`**: Add `sentry-sdk[streamlit]==1.38.0`

### 1.2 Strategic Error Monitoring Points
- **Data Loading Module** (`modules/data_loader.py:34-98`): Enhance ML model loading errors
- **Document Parser** (`modules/solicitation_parser.py:146-198`): Monitor file processing failures  
- **API Integration** (`modules/enhanced_skill_extractor.py:270-305`): Track GROQ API failures
- **Report Generation** (`modules/report_generator.py:89-95`): Monitor report generation errors

### 1.3 Logging Infrastructure Enhancement
- **Integrate with existing loggers** in `enhanced_skill_extractor.py:94-113` and `solicitation_parser.py:65-93`
- **Add performance monitoring** for ML model inference and API response times
- **Implement user action tracking** for research team assembly workflow

## Phase 2: Vercel Deployment Configuration

### 2.1 Core Vercel Setup
- **Create `vercel.json`**: Python runtime configuration with custom build settings
- **Create `api/streamlit.py`**: Serverless wrapper function for Streamlit app
- **Create `requirements-vercel.txt`**: Optimized dependencies list excluding heavy ML libraries

### 2.2 Critical Challenge: ML Model File Storage 
**Problem**: Data files (`*.npz`, `*.pkl`, `*.parquet`) exceed Vercel's 50MB limit

**Solution Strategy**:
- **Move to external storage** (Vercel Blob or AWS S3)
- **Modify `modules/data_loader.py:82-98`**: Add cloud storage download functionality
- **Implement caching mechanism** for model files
- **Add fallback to bundled lightweight models**

### 2.3 Environment & Configuration
- **Update `.env.example`**: Add required Vercel environment variables
- **Configure Vercel environment variables**: `GROQ_API_KEY`, `SENTRY_DSN`, `MODEL_STORAGE_URL`
- **Modify `app.py:84`**: Handle both local and cloud environment configurations

## Phase 3: Deployment Optimization

### 3.1 Streamlit-to-Vercel Adapter
- **Create custom ASGI wrapper**: Convert Streamlit to ASGI-compatible app
- **Handle session state persistence**: Implement Redis/external session storage
- **File upload handling**: Temporary file management in serverless environment

### 3.2 Performance Optimizations
- **Lazy loading**: Load ML models only when needed
- **Response compression**: Optimize API response sizes
- **Caching strategy**: Implement intelligent caching for repeated operations

### 3.3 Fallback Mechanisms
- **Graceful degradation**: App works without cloud models (existing pattern at `app.py:212`)
- **Sentry failure handling**: Continue operation if Sentry initialization fails
- **Multi-deployment support**: Maintain compatibility with Streamlit Cloud/Heroku

## Phase 4: Testing & Validation

### 4.1 Local Testing
- **Test Sentry integration**: Verify error capturing and performance monitoring
- **Test cloud model loading**: Ensure data files download and cache correctly
- **Validate environment handling**: Test both local `.env` and Vercel environment variables

### 4.2 Deployment Validation  
- **Vercel preview deployment**: Test serverless function execution
- **Performance benchmarking**: Compare response times vs current deployment
- **Error monitoring**: Verify Sentry captures deployment-specific issues

## Key Files to Create/Modify:

**New Files:**
- `vercel.json` - Deployment configuration
- `api/streamlit.py` - Serverless wrapper
- `requirements-vercel.txt` - Optimized dependencies
- `utils/cloud_storage.py` - External storage handling

**Modified Files:**
- `app.py` (lines 15, 18-23, 84) - Sentry init & environment handling
- `modules/data_loader.py` (lines 82-98) - Cloud storage integration
- `requirements.txt` - Add Sentry SDK
- `.env.example` - Document new environment variables

## Risk Mitigation:
- **Preserve existing functionality** - all changes are additive
- **Maintain deployment flexibility** - works with current targets
- **Progressive rollout** - can deploy incrementally
- **Comprehensive fallbacks** - graceful degradation at every level

This plan addresses the file size limitations, Streamlit serverless challenges, and maintains the robust error handling already in place.

---

## 📊 Investigation Findings (2025-09-04)

### **Git History Analysis**
- **Previous Vercel commits found**: `92149844` and `fd23fac7` 
- **Config was for static hosting** (`backend/visuals/vercel.json`), not Python/Streamlit
- **Configuration removed** from current codebase (likely due to deployment issues)
- **No Sentry commits found** - clean slate for implementation

### **Previous Vercel Config** (Retrieved from git)
```json
{
  "headers": [...caching for .gz, .js, .css],
  "rewrites": [{"source": "/(.*)", "destination": "/public/$1"}]
}
```
**Issue**: Wrong approach - static file serving instead of serverless Python

### **Test Suite Analysis**
- **10 test files** across `unit/`, `integration/`, `feature/` directories
- **Comprehensive coverage**: PDF parsing, skill extraction, full workflow
- **Dependencies**: Requires ML model files in `/data/`, GROQ_API_KEY
- **No CI/CD**: Missing `.github/workflows/` explains pipeline failures

### **Current Test Structure**
- `test/feature/test_enhanced_skill_extractor.py` - Dual-model validation
- `test/integration/test_complete_workflow.py` - End-to-end pipeline
- **Potential failures**: Missing data files, API keys, import path issues

### **Dependencies Analysis**
- **Heavy ML dependencies**: torch, sentence-transformers, scikit-learn
- **API dependencies**: GROQ for enhanced extraction
- **File processing**: PyPDF2, python-docx
- **Current total**: ~15 packages, likely exceeding Vercel limits

### **Vercel CLI Investigation**
- **Authenticated as**: adhsaksham26
- **Found dashboard projects**:
  - `dashboard` (prj_TUcKkpli0uaVM4M69B3CDm1b5cs4) - https://dashboard-bay-rho.vercel.app
  - `dashboard-a4dy` (prj_bJTRYeSKe1D2UrVSpcuszXtEGCZG) - https://dashboard-a4dy-sakshams-projects-1f763efb.vercel.app
- **Project ID prj_URZwqwFdPh5pwQ3NwEj7npRswMFn**: Not found in current account
- **Current directory**: Not linked to any Vercel project
- **All projects using Node.js 22.x** - confirms mismatch with Python/Streamlit app

### **Sentry Integration Status**
- **User mentioned**: Project already has Sentry configured
- **Need to verify**: Sentry DSN and project configuration
- **Current codebase**: No Sentry integration found

### **Key Issues Identified**
1. **Wrong deployment approach**: Previous attempts used Node.js static hosting
2. **Missing project link**: Current directory not connected to Vercel project  
3. **Python vs Node.js mismatch**: All projects configured for Node.js, not Python
4. **Test failures**: Missing CI/CD infrastructure and data dependencies
5. **Project ID mismatch**: Specified ID not found in current account

### **Correct Project Found & Linked**
- **✅ Successfully linked** to `cads-research` (prj_URZwqwFdPh5pwQ3NwEj7npRswMFn)
- **URL**: https://cads-research.vercel.app (currently 404 - needs deployment)
- **Team**: sakshams-projects-1f763efb
- **Last deployed**: 12 days ago
- **Current status**: Node.js 22.x project, needs reconfiguration for Python

### **Environment Configuration**
- **Current env vars**: None configured (fresh start needed)
- **Required variables**:
  - `GROQ_API_KEY` (already available locally)
  - `SENTRY_DSN` (to be configured)
  - `PYTHON_PATH` (for serverless functions)

### **Sentry Integration Evidence**
- **Security scanning configured**: Found Sentry access token detection in `.config/.semgrep/semgrep_rules.json`
- **No active integration**: No Sentry SDK found in current codebase
- **Prepared infrastructure**: Security rules suggest Sentry was planned/used previously

### **Current Deployment Status**
- **Site returns 404**: No active deployment or needs rebuild
- **Missing configuration**: No `vercel.json` for Python/Streamlit deployment
- **Clean slate opportunity**: Can deploy fresh configuration without conflicting with other projects

---
*Generated: 2025-09-04*
*Branch: streamlit*  
*Status: Ready for Implementation - Correct Project Linked*