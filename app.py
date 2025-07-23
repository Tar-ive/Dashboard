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

# Import our modular classes
from modules.data_loader import DataLoader
from modules.matcher import ResearcherMatcher
from modules.team_builder import TeamBuilder
from modules.report_generator import ReportGenerator
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
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Workflow Steps")
    st.sidebar.markdown("""
    1. **Upload Solicitation** - JSON format
    2. **Analyze & Match** - Find top researchers  
    3. **Build Dream Team** - Optimal team assembly
    4. **Generate Report** - AI-powered analysis
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
    
    uploaded_file = st.file_uploader(
        "Choose a JSON solicitation file",
        type=['json'],
        help="Upload a JSON file containing the research solicitation details"
    )
    
    solicitation = None
    
    if uploaded_file is not None:
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
            
            # Display solicitation details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📋 Solicitation Details")
                st.write(f"**Title:** {solicitation.title}")
                st.write(f"**Abstract:** {solicitation.abstract[:300]}...")
                
            with col2:
                st.metric("Required Skills", len(solicitation.required_skills_checklist))
                if solicitation.funding_amount:
                    st.write(f"**Funding:** {solicitation.funding_amount}")
            
            # Show required skills
            with st.expander("🎯 View Required Skills"):
                for i, skill in enumerate(solicitation.required_skills_checklist, 1):
                    st.write(f"{i}. {skill}")
                    
        except Exception as e:
            st.error(f"❌ Error processing solicitation file: {str(e)}")
            return
    
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
