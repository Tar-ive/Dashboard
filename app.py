"""
Main Streamlit application for AI-powered research team matching and assembly system.
Orchestrates the workflow from solicitation analysis to dream team report generation.
"""

import os
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Debug GROQ API key loading
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    print(f"✅ GROQ_API_KEY loaded successfully (length: {len(groq_api_key)})")
else:
    print("⚠️ GROQ_API_KEY not found in environment variables")

# Import our modular classes
from modules.data_loader import DataLoader
from modules.matcher import ResearcherMatcher
from modules.team_builder import TeamBuilder
from modules.report_generator import ReportGenerator
from modules.solicitation_parser import SolicitationParser
from modules.enhanced_skill_extractor import EnhancedSkillExtractor
from modules.data_models import Solicitation


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Research Team Matcher",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("🔬 AI-Powered Research Team Matching & Assembly System")
    st.markdown("""
    Upload a research solicitation and discover the optimal team of researchers 
    to maximize coverage of required skills and expertise.
    """)
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'matching_results' not in st.session_state:
        st.session_state.matching_results = None
    if 'team_results' not in st.session_state:
        st.session_state.team_results = None
    if 'final_report' not in st.session_state:
        st.session_state.final_report = None
    if 'parsed_solicitation' not in st.session_state:
        st.session_state.parsed_solicitation = None
    if 'parsing_result' not in st.session_state:
        st.session_state.parsing_result = None
    if 'enhanced_extraction_result' not in st.session_state:
        st.session_state.enhanced_extraction_result = None
    
    # Sidebar for configuration
    setup_sidebar()
    
    # Main workflow - system auto-initializes
    main_workflow()


def setup_sidebar():
    """Setup sidebar for system status and workflow."""
    
    st.sidebar.header("🔧 System Status")
    
    # Auto-initialize system if not loaded
    if not st.session_state.data_loaded:
        # Use persistent data directory and API key
        data_dir = "./data"  # Local data directory
        groq_api_key = os.getenv("GROQ_API_KEY", "")  # From Replit Secrets
        
        with st.spinner("🔄 Auto-initializing system..."):
            initialize_system(data_dir, groq_api_key)
    
    # Display system status
    if st.session_state.data_loaded:
        st.sidebar.success("✅ System ready!")
        
        # Display data summary
        if 'all_data' in st.session_state:
            data = st.session_state.all_data['data']
            st.sidebar.metric("Researchers", len(data['researcher_vectors']))
            st.sidebar.metric("Papers", len(data['conceptual_profiles']))
        
        # Show API key status
        if os.getenv("GROQ_API_KEY"):
            st.sidebar.success("🤖 AI Analysis Available")
        else:
            st.sidebar.info("💡 Add GROQ_API_KEY to Secrets for AI analysis")
    
    # Enhanced skill extraction status
    if 'enhanced_extraction_result' in st.session_state and st.session_state.enhanced_extraction_result:
        result = st.session_state.enhanced_extraction_result
        st.sidebar.markdown("### 🤖 **ENHANCED AI EXTRACTION**")
        st.sidebar.success("✅ **ACTIVE**")
        st.sidebar.metric("🎯 Skills Found", len(result.merged_skills))
        st.sidebar.metric("📊 Quality", f"{result.quality_score:.2f}")
        st.sidebar.metric("🔧 Method", result.source_method.title())
        
        # Performance stats if available
        if hasattr(st.session_state, 'skill_extractor_stats'):
            stats = st.session_state.skill_extractor_stats
            if stats.get('total_extractions', 0) > 0:
                st.sidebar.metric("Success Rate", f"{stats.get('success_rate', 0):.1%}")
    else:
        st.sidebar.markdown("### 🤖 Enhanced AI Extraction")
        st.sidebar.info("💡 Upload a document to see AI-powered skill extraction")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Workflow Steps")
    st.sidebar.markdown("""
    1. **Upload Solicitation** - PDF or JSON format
    2. **Enhanced Skill Extraction** - AI-powered skill analysis
    3. **Analyze & Match** - Find top researchers  
    4. **Build Dream Team** - Optimal team assembly
    5. **Generate Report** - AI-powered analysis
    """)


def initialize_system(data_dir: str, groq_api_key: str):
    """Initialize the system by loading all data and models."""
    
    try:
        # Check if data directory exists and has required files
        data_path = Path(data_dir)
        required_files = [
            'tfidf_model.pkl',
            'researcher_vectors.npz',
            'conceptual_profiles.npz', 
            'evidence_index.json',
            'researcher_metadata.parquet'
        ]
        
        missing_files = [f for f in required_files if not (data_path / f).exists()]
        
        if missing_files:
            st.session_state.data_loaded = False
            st.warning(f"⚠️ Missing data files: {', '.join(missing_files)}")
            st.info("📁 Please ensure all research data files are uploaded to the /data directory")
            return
        
        # Initialize data loader
        data_loader = DataLoader(data_dir)
        
        # Load all data
        all_data = data_loader.get_all_data()
        
        # Store in session state
        st.session_state.all_data = all_data
        st.session_state.groq_api_key = groq_api_key
        st.session_state.data_loaded = True
        
        # Run data quality diagnostics
        data_loader.diagnose_data_quality(all_data)
        
        st.success("✅ System initialized successfully!")
        
    except Exception as e:
        st.session_state.data_loaded = False
        st.error(f"❌ Failed to initialize system: {str(e)}")
        st.info("📁 Please ensure all research data files are properly uploaded to the /data directory")


def handle_document_upload(uploaded_file) -> Optional[Solicitation]:
    """Handle multi-format document upload and parsing with enhanced skill extraction."""
    
    # Save uploaded file temporarily
    temp_path = f"./data/temp_{uploaded_file.name}"
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Parse document with progress indicator
        with st.spinner("🔄 Parsing document..."):
            parser = SolicitationParser()
            parsing_result = parser.parse_document(temp_path)
        
        # Store parsing result in session state
        st.session_state.parsing_result = parsing_result
        
        # Show parsing results and quality indicators
        display_parsing_results(parsing_result)
        
        # Enhanced skill extraction
        st.info("🚀 **NEW FEATURE**: Enhanced AI-powered skill extraction is now running...")
        with st.spinner("🤖 Running enhanced skill extraction with GROQ AI..."):
            try:
                # Extract text for skill extraction
                text, _ = parser.extract_text_from_file(temp_path)
                
                # Initialize enhanced skill extractor
                groq_api_key = os.getenv("GROQ_API_KEY")
                if groq_api_key:
                    st.success(f"✅ GROQ API key loaded (length: {len(groq_api_key)})")
                else:
                    st.warning("⚠️ GROQ API key not found - using fallback extraction")
                
                skill_extractor = EnhancedSkillExtractor(groq_api_key=groq_api_key)
                
                # Run dual-model skill extraction
                enhanced_extraction_result = skill_extractor.extract_skills_dual_model(text)
                st.session_state.enhanced_extraction_result = enhanced_extraction_result
                
                st.success(f"🎉 Enhanced extraction completed! Found {len(enhanced_extraction_result.merged_skills)} skills with quality score {enhanced_extraction_result.quality_score:.2f}")
                
            except Exception as e:
                st.error(f"❌ Enhanced skill extraction failed: {str(e)}")
                # Create a fallback result
                enhanced_extraction_result = None
                st.session_state.enhanced_extraction_result = None
        
        # Show enhanced skill extraction results
        if enhanced_extraction_result:
            display_enhanced_skill_extraction(enhanced_extraction_result)
        else:
            st.warning("⚠️ Enhanced skill extraction was not available - using basic extraction")
        
        # Convert to solicitation if quality is acceptable
        if parsing_result.confidence_score > 0.3:  # Minimum threshold
            solicitation = parser.convert_to_solicitation(parsing_result)
            
            # Use enhanced skills if available and better quality
            if enhanced_extraction_result.merged_skills and enhanced_extraction_result.quality_score > 0.5:
                solicitation.required_skills_checklist = enhanced_extraction_result.merged_skills
                st.success("✅ Using enhanced skill extraction results!")
            
            st.session_state.parsed_solicitation = solicitation
            
            # Show extraction preview with edit capabilities
            solicitation = show_extraction_preview(solicitation, parsing_result)
            
            return solicitation
        else:
            st.warning("⚠️ Low extraction confidence. Please review and edit the extracted data.")
            # Still allow user to proceed with manual editing
            solicitation = parser.convert_to_solicitation(parsing_result)
            
            # Use enhanced skills if available
            if enhanced_extraction_result.merged_skills:
                solicitation.required_skills_checklist = enhanced_extraction_result.merged_skills
            
            st.session_state.parsed_solicitation = solicitation
            solicitation = show_extraction_preview(solicitation, parsing_result)
            return solicitation
            
    except Exception as e:
        st.error(f"❌ Error parsing document: {str(e)}")
        st.info("💡 Please try manual entry or check document format")
        return None
    finally:
        # Clean up temporary file
        if Path(temp_path).exists():
            Path(temp_path).unlink()


def handle_json_upload(uploaded_file) -> Optional[Solicitation]:
    """Handle JSON file upload (existing functionality)."""
    
    try:
        solicitation_data = json.load(uploaded_file)
        
        # Handle case where JSON contains a list of solicitations
        if isinstance(solicitation_data, list):
            if not solicitation_data:
                raise ValueError("Solicitation file is empty.")
            # Process the first solicitation in the list
            first_solicitation_dict = solicitation_data[0]
            solicitation = Solicitation.from_dict(first_solicitation_dict)
            
            # Show info about multiple solicitations if present
            if len(solicitation_data) > 1:
                st.info(f"📄 Found {len(solicitation_data)} solicitations. Processing the first one: '{first_solicitation_dict.get('title', 'Untitled')}'")
        else:
            # Handle single solicitation object
            solicitation = Solicitation.from_dict(solicitation_data)
        
        return solicitation
        
    except Exception as e:
        raise Exception(f"Error processing JSON file: {str(e)}")


def display_parsing_results(parsing_result):
    """Display PDF parsing results with quality indicators."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence_color = "green" if parsing_result.confidence_score > 0.7 else "orange" if parsing_result.confidence_score > 0.4 else "red"
        st.metric(
            "Extraction Confidence", 
            f"{parsing_result.confidence_score:.1%}",
            help="Quality score of the extracted data"
        )
        st.markdown(f"<div style='color: {confidence_color}'>{'High' if parsing_result.confidence_score > 0.7 else 'Medium' if parsing_result.confidence_score > 0.4 else 'Low'} Quality</div>", unsafe_allow_html=True)
    
    with col2:
        fields_extracted = len(parsing_result.extracted_data) - len(parsing_result.missing_fields)
        st.metric("Fields Extracted", f"{fields_extracted}/{len(parsing_result.extracted_data)}")
    
    with col3:
        st.metric("Processing Time", f"{parsing_result.processing_time:.1f}s")
    
    with col4:
        st.metric("Source File", Path(parsing_result.source_file).name)
    
    # Show missing fields if any
    if parsing_result.missing_fields:
        st.warning(f"⚠️ Missing fields: {', '.join(parsing_result.missing_fields)}")


def display_enhanced_skill_extraction(extraction_result):
    """Display enhanced skill extraction results with comparison interface."""
    
    # Make it very prominent with a colored header
    st.markdown("---")
    st.markdown("## 🤖 **ENHANCED AI SKILL EXTRACTION RESULTS**")
    st.markdown("*Powered by GROQ AI + OpenAlex Topic Classification*")
    
    # Show a success message
    if extraction_result.quality_score > 0.7:
        st.success("🎉 **HIGH QUALITY** extraction completed!")
    elif extraction_result.quality_score > 0.4:
        st.info("✅ **GOOD QUALITY** extraction completed!")
    else:
        st.warning("⚠️ **BASIC QUALITY** extraction - manual review recommended")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Skills Extracted", len(extraction_result.merged_skills))
    with col2:
        quality_color = "green" if extraction_result.quality_score > 0.7 else "orange" if extraction_result.quality_score > 0.4 else "red"
        st.metric("📊 Quality Score", f"{extraction_result.quality_score:.2f}")
        st.markdown(f"<div style='color: {quality_color}; font-weight: bold;'>{'🟢 High' if extraction_result.quality_score > 0.7 else '🟡 Medium' if extraction_result.quality_score > 0.4 else '🔴 Low'} Quality</div>", unsafe_allow_html=True)
    with col3:
        st.metric("⚡ Extraction Time", f"{extraction_result.extraction_time:.2f}s")
    with col4:
        st.metric("🔧 Source Method", extraction_result.source_method.title())
    
    # Show final merged skills prominently FIRST
    if extraction_result.merged_skills:
        st.markdown("### ✨ **FINAL EXTRACTED SKILLS**")
        st.markdown("*These skills will be used for researcher matching:*")
        
        # Display skills in a nice format
        skills_cols = st.columns(3)
        for i, skill in enumerate(extraction_result.merged_skills):
            col_idx = i % 3
            with skills_cols[col_idx]:
                st.markdown(f"**{i+1}.** {skill}")
        
        # Show skills as tags
        skills_text = " • ".join(extraction_result.merged_skills)
        st.info(f"**All Skills:** {skills_text}")
    else:
        st.error("❌ No skills were extracted. Manual entry required.")
    
    # Expandable detailed comparison
    with st.expander("🔍 **View Detailed AI vs Topic Classification Comparison**", expanded=False):
        try:
            # Create the comparison interface with proper API key
            groq_api_key = os.getenv("GROQ_API_KEY")
            skill_extractor = EnhancedSkillExtractor(groq_api_key=groq_api_key)
            skill_extractor.create_skill_comparison_interface(extraction_result)
        except Exception as e:
            st.error(f"Error displaying comparison: {str(e)}")
    
    st.markdown("---")


def show_extraction_preview(solicitation: Solicitation, parsing_result) -> Solicitation:
    """Show extraction preview with edit capabilities."""
    
    st.subheader("📝 Extraction Preview & Edit")
    st.info("Review and edit the extracted information before proceeding to matching.")
    
    with st.form("extraction_edit_form"):
        # Editable fields
        title = st.text_input("Title", value=solicitation.title or "")
        abstract = st.text_area("Abstract", value=solicitation.abstract or "", height=150)
        
        # Skills as text area for easier editing
        skills_text = '\n'.join(solicitation.required_skills_checklist) if solicitation.required_skills_checklist else ""
        skills_input = st.text_area(
            "Required Skills (one per line)", 
            value=skills_text, 
            height=100,
            help="Enter each skill on a separate line"
        )
        
        # Optional fields
        col1, col2 = st.columns(2)
        with col1:
            funding_amount = st.text_input("Funding Amount", value=solicitation.funding_amount or "")
            program = st.text_input("Program", value=solicitation.program or "")
        
        with col2:
            deadline = st.text_input("Deadline", value=solicitation.deadline or "")
            description = st.text_area("Description", value=solicitation.description or "", height=100)
        
        # Submit button
        submitted = st.form_submit_button("✅ Confirm & Proceed", type="primary")
        
        if submitted:
            # Process skills input
            skills_list = [skill.strip() for skill in skills_input.split('\n') if skill.strip()]
            
            # Create updated solicitation
            updated_solicitation = Solicitation(
                title=title,
                abstract=abstract,
                required_skills_checklist=skills_list,
                funding_amount=funding_amount if funding_amount else None,
                program=program if program else None,
                deadline=deadline if deadline else None,
                description=description if description else None,
                parsing_metadata=solicitation.parsing_metadata,
                extraction_confidence=parsing_result.confidence_score
            )
            
            st.success("✅ Solicitation data confirmed!")
            st.session_state.parsed_solicitation = updated_solicitation
            st.rerun()
    
    return solicitation


def display_solicitation_details(solicitation: Solicitation):
    """Display solicitation details in a consistent format."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Solicitation Details")
        st.write(f"**Title:** {solicitation.title}")
        if solicitation.abstract:
            abstract_preview = solicitation.abstract[:300] + "..." if len(solicitation.abstract) > 300 else solicitation.abstract
            st.write(f"**Abstract:** {abstract_preview}")
        
        # Show parsing metadata if available
        if solicitation.parsing_metadata:
            with st.expander("🔍 Parsing Details"):
                st.write(f"**Source:** {Path(solicitation.parsing_metadata.get('source_file', '')).name}")
                st.write(f"**Processing Time:** {solicitation.parsing_metadata.get('processing_time', 0):.1f}s")
                if solicitation.parsing_metadata.get('missing_fields'):
                    st.write(f"**Missing Fields:** {', '.join(solicitation.parsing_metadata['missing_fields'])}")
                if solicitation.extraction_confidence:
                    st.write(f"**Extraction Confidence:** {solicitation.extraction_confidence:.1%}")
    
    with col2:
        st.metric("Required Skills", len(solicitation.required_skills_checklist))
        if solicitation.funding_amount:
            st.write(f"**Funding:** {solicitation.funding_amount}")
        if solicitation.program:
            st.write(f"**Program:** {solicitation.program}")
        if solicitation.deadline:
            st.write(f"**Deadline:** {solicitation.deadline}")
    
    # Show required skills
    if solicitation.required_skills_checklist:
        with st.expander("🎯 View Required Skills"):
            for i, skill in enumerate(solicitation.required_skills_checklist, 1):
                st.write(f"{i}. {skill}")
    else:
        st.warning("⚠️ No required skills found. Consider adding them manually.")


def main_workflow():
    """Main application workflow after system initialization."""
    
    # Check if system is ready
    if not st.session_state.data_loaded:
        st.info("📁 System is loading... Please ensure data files are in the /data directory")
        st.markdown("**Required files:**")
        st.markdown("- tfidf_model.pkl")
        st.markdown("- researcher_vectors.npz") 
        st.markdown("- conceptual_profiles.npz")
        st.markdown("- evidence_index.json")
        st.markdown("- researcher_metadata.parquet")
        return
    
    # Step 1: Solicitation Upload
    st.header("📄 Step 1: Upload Research Solicitation")
    
    # Template management interface
    show_template_management()
    
    # File upload with multiple format support
    uploaded_file = st.file_uploader(
        "Choose a solicitation file",
        type=['pdf', 'docx', 'txt', 'json'],
        help="Upload a PDF, Word, text, or JSON file containing the research solicitation details"
    )
    
    solicitation = None
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        try:
            if file_type in ['pdf', 'docx', 'txt']:
                solicitation = handle_document_upload(uploaded_file)
            elif file_type == 'json':
                solicitation = handle_json_upload(uploaded_file)
            else:
                st.error("❌ Unsupported file format. Please upload a PDF, Word, text, or JSON file.")
                return
                
        except Exception as e:
            st.error(f"❌ Error processing solicitation file: {str(e)}")
            st.info("💡 Please try manual entry or check file format")
            return
    
    # Display solicitation details if available
    if solicitation is not None:
        display_solicitation_details(solicitation)
    
    # Step 2: Researcher Matching
    if solicitation is not None:
        st.header("🔍 Step 2: Researcher Analysis & Matching")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            top_k = st.number_input("Top researchers to analyze", min_value=10, max_value=500, value=100)
        
        with col2:
            if st.button("🔍 Analyze Solicitation", type="primary"):
                analyze_solicitation(solicitation, top_k)
        
        with col3:
            if st.session_state.matching_results:
                st.metric("Matches Found", len(st.session_state.matching_results.top_matches))
        
        # Display matching results
        if st.session_state.matching_results:
            display_matching_results()
    
    # Step 3: Dream Team Assembly
    if st.session_state.matching_results:
        st.header("🏗️ Step 3: Dream Team Assembly")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            team_size = st.number_input("Max team size", min_value=3, max_value=15, value=8)
        
        with col2:
            if st.button("🚀 Build Dream Team", type="primary"):
                build_dream_team(team_size)
        
        with col3:
            if st.session_state.team_results:
                st.metric("Team Coverage", f"{st.session_state.team_results.overall_coverage_score:.1%}")
        
        # Display team results
        if st.session_state.team_results:
            display_team_results()
    
    # Step 4: Final Report
    if st.session_state.team_results:
        st.header("📋 Step 4: Strategic Report Generation")
        
        if st.button("📊 Generate Full Report", type="primary") and solicitation is not None:
            generate_final_report(solicitation)
        
        # Display final report
        if st.session_state.final_report:
            display_final_report()


def analyze_solicitation(solicitation: Solicitation, top_k: int):
    """Analyze solicitation and find matching researchers."""
    
    try:
        with st.spinner("🔄 Analyzing solicitation and matching researchers..."):
            # Initialize matcher
            matcher = ResearcherMatcher()
            
            # Perform matching
            matching_results = matcher.search_researchers(
                solicitation,
                st.session_state.all_data['models'],
                st.session_state.all_data['data'],
                top_k=top_k
            )
            
            # Store results
            st.session_state.matching_results = matching_results
            st.session_state.solicitation = solicitation
        
        st.success(f"✅ Found {len(matching_results.top_matches)} matching researchers!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during matching: {str(e)}")


def display_matching_results():
    """Display the researcher matching results."""
    
    results = st.session_state.matching_results
    
    st.subheader("🎯 Top Matching Researchers")
    
    # Create DataFrame for display
    matches_data = []
    for match in results.top_matches:
        matches_data.append({
            "Researcher": match.researcher_name,
            "Final Score": f"{match.final_affinity_score:.3f}",
            "Academic Score": f"{match.academic_expertise_score:.3f}",
            "TF-IDF Score": f"{match.s_sparse:.3f}",
            "Semantic Score": f"{match.s_dense:.3f}",
            "Papers": match.total_papers,
            "Status": match.eligibility_status
        })
    
    matches_df = pd.DataFrame(matches_data)
    st.dataframe(matches_df, use_container_width=True, height=400)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Researchers", results.total_researchers)
    with col2:
        st.metric("Eligible", results.eligible_researchers)
    with col3:
        st.metric("Skills Analyzed", len(results.skills_analyzed))
    with col4:
        st.metric("Processing Time", f"{results.processing_time_seconds:.1f}s")


def build_dream_team(team_size: int):
    """Build the optimal dream team."""
    
    try:
        with st.spinner("🔄 Assembling optimal dream team..."):
            # Initialize team builder
            team_builder = TeamBuilder()
            
            # Assemble team
            team_results = team_builder.assemble_team(
                st.session_state.matching_results,
                st.session_state.all_data['models'],
                st.session_state.all_data['data'],
                max_team_size=team_size
            )
            
            # Store results
            st.session_state.team_results = team_results
        
        st.success(f"✅ Dream team assembled with {team_results.overall_coverage_score:.1%} coverage!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during team assembly: {str(e)}")


def display_team_results():
    """Display the assembled dream team."""
    
    team_results = st.session_state.team_results
    
    st.subheader("🏆 Dream Team Members")
    
    # Display team members
    for i, member in enumerate(team_results.team_members, 1):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{i}. {member['name']}**")
            with col2:
                st.metric("Affinity", f"{member['final_affinity_score']:.3f}")
            with col3:
                st.metric("Papers", member['total_papers'])
            with col4:
                st.write(f"*{member['team_role']}*")
    
    # Selection history
    with st.expander("📈 View Team Selection Process"):
        for step in team_results.selection_history:
            st.write(f"**Round {step['round']}:** {step['researcher']} "
                    f"(Gain: {step['marginal_gain']:.3f}, Coverage: {step['team_coverage']:.3f})")
    
    # Coverage visualization
    if hasattr(team_results, 'affinity_df'):
        with st.expander("🎯 View Skill Coverage Matrix"):
            # Show affinity matrix for team members
            team_affinity = team_results.affinity_df.iloc[team_results.team_indices]
            st.dataframe(team_affinity, use_container_width=True)


def generate_final_report(solicitation: Solicitation):
    """Generate the comprehensive final report."""
    
    try:
        with st.spinner("🔄 Generating comprehensive report with AI analysis..."):
            # Initialize report generator
            report_generator = ReportGenerator(st.session_state.groq_api_key)
            
            # Generate full report
            dream_team_report, team_evidence = report_generator.generate_full_report(
                st.session_state.matching_results,
                st.session_state.team_results,
                solicitation,
                st.session_state.all_data['data']
            )
            
            # Store results
            st.session_state.final_report = dream_team_report
            st.session_state.team_evidence = team_evidence
            st.session_state.markdown_report = report_generator.format_markdown_report(
                dream_team_report, team_evidence, solicitation
            )
        
        st.success("✅ Comprehensive report generated!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")


def show_template_management():
    """Display template management interface."""
    
    with st.expander("🔧 Template Management & Performance"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Extraction Templates")
            
            # Initialize parser to access templates
            parser = SolicitationParser()
            templates = parser.list_templates()
            
            if templates:
                st.write("**Available Templates:**")
                for template in templates:
                    st.write(f"• **{template['name']}** - {template['description']} ({template['field_count']} fields)")
            else:
                st.info("No custom templates saved yet.")
            
            # Template creation
            st.write("**Create New Template:**")
            template_name = st.text_input("Template Name", key="new_template_name")
            template_desc = st.text_input("Description", key="new_template_desc")
            
            if st.button("💾 Save Current Config as Template"):
                if template_name:
                    if parser.save_template(template_name, template_desc):
                        st.success(f"✅ Template '{template_name}' saved!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save template")
                else:
                    st.warning("Please enter a template name")
        
        with col2:
            st.subheader("📊 Performance Statistics")
            
            stats = parser.get_performance_stats()
            
            if stats['total_documents_processed'] > 0:
                col2a, col2b = st.columns(2)
                
                with col2a:
                    st.metric("Documents Processed", stats['total_documents_processed'])
                    st.metric("Success Rate", f"{stats['success_rate']:.1%}")
                
                with col2b:
                    if 'avg_processing_time' in stats:
                        st.metric("Avg Processing Time", f"{stats['avg_processing_time']:.2f}s")
                    if 'avg_memory_usage' in stats:
                        st.metric("Avg Memory Usage", f"{stats['avg_memory_usage']:.1f}MB")
                
                # Performance chart
                if len(stats['processing_times']) > 1:
                    st.line_chart(stats['processing_times'][-20:])  # Last 20 processing times
            else:
                st.info("No documents processed yet.")

def display_final_report():
    """Display the final comprehensive report."""
    
    report = st.session_state.final_report
    
    st.subheader("📊 Strategic Analysis Report")
    
    # Executive summary
    st.markdown("### 🎯 Strategic Analysis")
    st.markdown(report.strategic_analysis)
    
    # Team summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Overall Coverage Score", f"{report.overall_coverage_score:.1%}")
        st.metric("Team Members", len(report.team_members))
    
    with col2:
        avg_affinity = sum(m['final_affinity_score'] for m in report.team_members) / len(report.team_members)
        st.metric("Average Affinity", f"{avg_affinity:.3f}")
        st.metric("Total Papers", sum(m['total_papers'] for m in report.team_members))
    
    # Skill analysis
    if report.skill_analysis:
        st.markdown("### 📈 Skill Coverage Analysis")
        skill_data = []
        for skill in report.skill_analysis:
            skill_data.append({
                "Skill": skill['skill'],
                "Coverage": f"{skill['coverage']:.1%}"
            })
        
        skill_df = pd.DataFrame(skill_data)
        st.dataframe(skill_df, use_container_width=True)
    
    # Download report
    st.markdown("### 📥 Download Report")
    
    if 'markdown_report' in st.session_state:
        st.download_button(
            label="📄 Download Markdown Report",
            data=st.session_state.markdown_report,
            file_name=f"dream_team_report_{report.generated_at.replace(':', '-').replace(' ', '_')}.md",
            mime="text/markdown",
            type="primary"
        )


if __name__ == "__main__":
    main()
