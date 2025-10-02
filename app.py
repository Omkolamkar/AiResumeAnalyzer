# app.py - Enhanced AI Resume Analyzer with Comprehensive Improvements
import os
import sys
import time
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

import streamlit as st
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber

# Import our enhanced modules
try:
    from config import api_config, app_config, ui_config, setup_logging, validate_api_keys
    from utils import (
        validate_file, sanitize_filename, generate_file_hash, temporary_file,
        safe_execute, display_error, display_success, create_progress_tracker,
        log_user_action, handle_streamlit_error, ValidationError, ProcessingError
    )
    from jobs_api_improved import search_all_apis, JobResult, get_job_search_stats
    from matching_improved import AdvancedJobMatcher, create_enhanced_profile_from_basic
    from utils_profile_improved import ProfileExtractor
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Please ensure all required files are present and dependencies are installed.")
    st.stop()

# Initialize logging
logger = setup_logging()

class ResumeAnalyzer:
    """Enhanced Resume Analyzer with better error handling and features"""
    
    def __init__(self):
        self.profile_extractor = ProfileExtractor()
        self.job_matcher = AdvancedJobMatcher()
        self._initialize_ai_model()
    
    def _initialize_ai_model(self):
        """Initialize AI model with error handling"""
        try:
            if not api_config.google_api_key:
                raise ValueError("Google API key not configured")
            genai.configure(api_key=api_config.google_api_key)
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            logger.info("AI model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            raise ProcessingError(f"AI model not available: {str(e)}")
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Enhanced PDF text extraction with better error handling"""
        if not pdf_file:
            raise ValidationError("No PDF file provided")
        
        progress = create_progress_tracker(3, "Extracting text from PDF")
        
        try:
            progress.update("Validating file")
            validate_file(pdf_file, app_config.max_file_size_mb, app_config.allowed_file_types)
            
            with temporary_file(suffix='.pdf') as temp_file:
                progress.update("Saving temporary file")
                temp_file.write(pdf_file.read())
                temp_file.flush()
                
                text = ""
                
                # Try direct text extraction first
                try:
                    progress.update("Extracting text directly")
                    with pdfplumber.open(temp_file.name) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    
                    if text.strip():
                        progress.complete("Text extraction successful")
                        logger.info(f"Successfully extracted {len(text)} characters from PDF")
                        return text.strip()
                
                except Exception as e:
                    logger.warning(f"Direct text extraction failed: {e}")
                
                # Fallback to OCR
                logger.info("Falling back to OCR extraction")
                try:
                    images = convert_from_path(temp_file.name)
                    for i, image in enumerate(images):
                        page_text = pytesseract.image_to_string(image)
                        text += f"Page {i+1}:\n{page_text}\n\n"
                    
                    progress.complete("OCR extraction successful")
                    logger.info(f"OCR extracted {len(text)} characters from PDF")
                    return text.strip()
                
                except Exception as ocr_error:
                    logger.error(f"OCR extraction failed: {ocr_error}")
                    raise ProcessingError(f"Failed to extract text from PDF: {ocr_error}")
        
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            raise ProcessingError(f"Error processing PDF file: {e}")
    
    def analyze_resume(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced resume analysis with comprehensive error handling"""
        if not resume_text or not resume_text.strip():
            raise ValidationError("Resume text is required for analysis")
        
        if not self.model:
            raise ProcessingError("AI model not available. Please check your API configuration.")
        
        progress = create_progress_tracker(3, "Analyzing resume")
        
        try:
            progress.update("Preparing analysis prompt")
            
            base_prompt = f"""
            You are an experienced HR professional with technical expertise across multiple domains including Data Science, Software Engineering, DevOPS, Machine Learning, AI, Full Stack Development, Marketing, and more.

            Please provide a comprehensive professional evaluation of this resume:

            **RESUME:**
            {resume_text}

            **ANALYSIS REQUIREMENTS:**
            1. **Professional Summary**: One-line summary of the candidate's profile
            2. **Experience Level**: Classify as Student/Intern/Junior/Mid-level/Senior/Executive
            3. **Existing Skills**: List all technical and relevant soft skills found
            4. **Skill Gaps**: Identify missing or weak skills for career growth
            5. **Course Recommendations**: Suggest 3-5 specific courses/certifications to improve the resume
            6. **Strengths**: Key positive aspects of the profile
            7. **Areas for Improvement**: Specific recommendations for enhancement
            8. **Industry Readiness**: Assessment of readiness for target roles
            """
            
            if job_description:
                base_prompt += f"""
                
                **JOB DESCRIPTION FOR COMPARISON:**
                {job_description}
                
                **ADDITIONAL ANALYSIS FOR JOB FIT:**
                9. **Job Compatibility Score**: Rate compatibility as a percentage (0-100%)
                10. **Job-Specific Strengths**: How the candidate aligns with this specific role
                11. **Job-Specific Gaps**: Missing requirements for this specific position
                12. **Recommendation**: Whether to proceed with application and next steps
                """
            
            progress.update("Generating AI analysis")
            response = self.model.generate_content(base_prompt)
            
            if not response or not response.text:
                raise ProcessingError("AI model returned empty response")
            
            progress.update("Processing results")
            analysis_result = {
                'analysis': response.text.strip(),
                'word_count': len(resume_text.split()),
                'character_count': len(resume_text),
                'timestamp': datetime.now().isoformat(),
                'job_specific': bool(job_description)
            }
            
            progress.complete("Analysis complete")
            logger.info("Resume analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            raise ProcessingError(f"Failed to analyze resume: {e}")

class EnhancedStreamlitApp:
    """Enhanced Streamlit application with better UI/UX and error handling"""
    
    def __init__(self):
        self.analyzer = ResumeAnalyzer()
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=app_config.app_title,
            layout="wide",
            # Removed page_icon="🤖"
        )
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if "session_id" not in st.session_state:
            st.session_state.session_id = generate_file_hash(str(time.time()).encode())
        
        st.session_state.theme = "light"
        
        if "resume_text" not in st.session_state:
            st.session_state.resume_text = ""
        
        if "candidate_profile" not in st.session_state:
            st.session_state.candidate_profile = None
        
        if "last_analysis" not in st.session_state:
            st.session_state.last_analysis = None
    
    def apply_custom_css(self):
        """Apply custom CSS for better UI and to remove anchor links"""
        theme = ui_config.theme_options["light"]
        
        css = f"""
        <style>
        .main-header {{
            background: linear-gradient(90deg, {theme['primary_color']}, {theme['accent_color']});
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }}
        
        .metric-card {{
            background-color: {theme['background_color']};
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            margin: 0.5rem 0;
        }}
        
        .job-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid {theme['accent_color']};
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .score-badge {{
            background: {theme['accent_color']};
            color: white;
            padding: 0.2rem 0.8rem;
            border-radius: 15px;
            font-weight: bold;
            display: inline-block;
        }}
        
        .sidebar-section {{
            background: {theme['background_color']};
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        
        /* General layout adjustments for removed sidebar */
        .st-emotion-cache-18ni7ap {{
            flex-direction: column;
        }}
        .st-emotion-cache-z5f0il {{
            padding-right: 1rem;
        }}

        /* The new, definitive fix for all Streamlit versions */
        [data-testid="stHeaderLink"] {{
            display: none !important;
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    @handle_streamlit_error
    def render_main_header(self):
        """Render main application header"""
        st.markdown(
            f'<div class="main-header">'
            '<h1>AI Resume Analyzer & Job Matcher</h1>'
            '<p>Powered by Advanced AI • Enhanced Job Matching • Professional Analysis</p>'
            '</div>',
            unsafe_allow_html=True
        )

    @handle_streamlit_error
    def render_resume_analysis_tab(self):
        """Render the resume analysis tab with enhanced features"""
        # Using markdown with an HTML 2 tag instead of st.header to avoid the anchor link
        st.markdown("<h2>Resume Analysis</h2>", unsafe_allow_html=True)
        
        # File upload section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload your resume (PDF only)",
                type=['pdf'],
                help=f"Maximum file size: {app_config.max_file_size_mb}MB"
            )
        
        with col2:
            if uploaded_file:
                file_details = f"""
                **File Details:**
                - Name: {uploaded_file.name}
                - Size: {uploaded_file.size / 1024:.1f} KB
                - Type: {uploaded_file.type}
                """
                st.info(file_details)
        
        # Job description input
        # Using markdown with an HTML 3 tag instead of st.subheader
        st.markdown("<h3>Job Description (Optional)</h3>", unsafe_allow_html=True)
        job_description = st.text_area(
            "Paste the job description for targeted analysis",
            height=150,
            placeholder="Paste the job description here for a more targeted analysis..."
        )
        
        # Analysis button and processing
        if st.button("Analyze Resume", type="primary", use_container_width=True):
            if not uploaded_file:
                display_error("Please upload a resume file first.")
                return
            
            try:
                log_user_action("resume_analysis_started", {"filename": uploaded_file.name})
                
                # Extract text from PDF
                with st.spinner("Extracting text from PDF..."):
                    resume_text = self.analyzer.extract_text_from_pdf(uploaded_file)
                    st.session_state.resume_text = resume_text
                
                # Show extracted text preview
                with st.expander("Extracted Text Preview", expanded=False):
                    st.text_area("Resume Text", resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text, height=200)
                
                # Analyze resume
                with st.spinner("Analyzing resume with AI..."):
                    analysis = self.analyzer.analyze_resume(resume_text, job_description)
                    st.session_state.last_analysis = analysis
                
                # Extract candidate profile for job matching
                with st.spinner("Extracting candidate profile..."):
                    profile = self.analyzer.profile_extractor.extract_candidate_profile(resume_text)
                    st.session_state.candidate_profile = profile
                
                display_success("Resume analysis completed successfully!")
                
                # Display results
                self._display_analysis_results(analysis, profile)
                
                log_user_action("resume_analysis_completed", {"success": True})
                
            except ValidationError as e:
                display_error(str(e), "warning")
            except ProcessingError as e:
                display_error(str(e))
            except Exception as e:
                logger.error(f"Unexpected error in resume analysis: {e}")
                display_error("An unexpected error occurred. Please try again.")
        
        # Display previous results if available
        elif st.session_state.last_analysis:
            st.success("Previous analysis available")
            if st.button("Show Last Analysis"):
                self._display_analysis_results(
                    st.session_state.last_analysis, 
                    st.session_state.candidate_profile
                )
    
    def _display_analysis_results(self, analysis: Dict[str, Any], profile: Dict[str, Any]):
        """Display comprehensive analysis results"""
        # Using markdown with an HTML 3 tag instead of st.subheader
        st.markdown("<h3>Analysis Results</h3>", unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Words", analysis.get('word_count', 0))
        
        with col2:
            st.metric("Characters", analysis.get('character_count', 0))
        
        with col3:
            skills_count = len(profile.get('skills', [])) if profile else 0
            st.metric("Skills Found", skills_count)
        
        with col4:
            exp_level = profile.get('experience_level', 'Unknown').title() if profile else 'Unknown'
            st.metric("Experience Level", exp_level)
        
        # Analysis text
        # Using markdown with an HTML 3 tag instead of st.subheader
        st.markdown("<h3>Detailed Analysis</h3>", unsafe_allow_html=True)
        st.markdown(analysis.get('analysis', 'No analysis available'))
        
        # Profile summary
        if profile and not profile.get('error'):
            # Using markdown with an HTML 3 tag instead of st.subheader
            st.markdown("<h3>Extracted Profile</h3>", unsafe_allow_html=True)
            profile_summary = self.analyzer.profile_extractor.get_profile_summary(profile)
            st.info(profile_summary)
            
            # Skills breakdown
            if profile.get('skills'):
                # Using markdown with an HTML 3 tag instead of st.subheader
                st.markdown("<h3>Skills Breakdown</h3>", unsafe_allow_html=True)
                skills_col1, skills_col2 = st.columns(2)
                
                skills = profile['skills']
                mid_point = len(skills) // 2
                
                with skills_col1:
                    st.write("**Technical Skills:**")
                    for skill in skills[:mid_point]:
                        st.write(f"• {skill}")
                
                with skills_col2:
                    st.write("**Additional Skills:**")
                    for skill in skills[mid_point:]:
                        st.write(f"• {skill}")
    
    @handle_streamlit_error 
    def render_job_matching_tab(self):
        """Render the job matching tab with enhanced features"""
        # Using markdown with an HTML 2 tag instead of st.header to avoid the anchor link
        st.markdown("<h2>Job Matching & Search</h2>", unsafe_allow_html=True)
        
        if not st.session_state.candidate_profile:
            st.warning("Please analyze a resume first to enable job matching.")
            return
        
        # Search controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Job Search Query",
                placeholder="e.g., Python Developer, Data Scientist, Software Engineer",
                help="Enter keywords related to your target job role"
            )
        
        with col2:
            location = st.text_input(
                "Location",
                placeholder="e.g., New York, Remote, India",
                help="Enter preferred location or 'Remote' for remote work"
            )
        
        # Advanced search options
        with st.expander("Advanced Search Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                max_results = st.slider("Maximum Results", 10, 100, 50)
                include_remote = st.checkbox("Include Remote Jobs", value=True)
            
            with col4:
                experience_filter = st.selectbox(
                    "Experience Level Filter",
                    ["All Levels", "Entry Level", "Mid Level", "Senior Level", "Executive"],
                    help="Filter jobs by experience level"
                )
        
        # Search button
        if st.button("Search & Match Jobs", type="primary", use_container_width=True):
            if not search_query:
                display_error("Please enter a search query.")
                return
            
            try:
                log_user_action("job_search_started", {"query": search_query, "location": location})
                
                with st.spinner("Searching job opportunities..."):
                    jobs = search_all_apis(search_query, location, max_results)
                
                if not jobs:
                    st.warning("No jobs found matching your criteria. Try different keywords or location.")
                    return
                
                display_success(f"Found {len(jobs)} job opportunities!")
                
                # Convert profile and rank jobs
                with st.spinner("Analyzing job compatibility..."):
                    enhanced_profile = create_enhanced_profile_from_basic(st.session_state.candidate_profile)
                    matcher = AdvancedJobMatcher()
                    ranked_jobs = matcher.rank_jobs([job.to_dict() for job in jobs], enhanced_profile, max_results)
                
                # Display results
                self._display_job_results(ranked_jobs)
                
                log_user_action("job_search_completed", {"jobs_found": len(jobs)})
                
            except Exception as e:
                logger.error(f"Job search failed: {e}")
                display_error(f"Job search failed: {str(e)}")
    
    def _display_job_results(self, ranked_jobs: List[tuple]):
        """Display ranked job results with enhanced UI"""
        # Using markdown with an HTML 3 tag instead of st.subheader
        st.markdown(f"<h3>Top Job Matches ({len(ranked_jobs)} found)</h3>", unsafe_allow_html=True)
        
        # Results summary
        if ranked_jobs:
            avg_score = sum(score for score, _, _ in ranked_jobs) / len(ranked_jobs)
            top_score = ranked_jobs[0][0] if ranked_jobs else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Top Match Score", f"{top_score:.1f}%")
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                st.metric("Total Matches", len(ranked_jobs))
        
        # Display individual job cards
        for i, (score, job, features) in enumerate(ranked_jobs):
            with st.container():
                # Job card header
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Using markdown with an HTML 3 tag here for job title
                    st.markdown(f"<h3>{job.get('title', 'Unknown Position')}</h3>", unsafe_allow_html=True)
                    st.markdown(f"**{job.get('company', 'Unknown Company')}** • {job.get('location', 'Location not specified')}")
                
                with col2:
                    score_color = "#4CAF50" if score >= 70 else "#FF9800" if score >= 50 else "#F44336"
                    st.markdown(
                        f'<div class="score-badge" style="background-color: {score_color}">'
                        f'{score:.1f}% Match</div>',
                        unsafe_allow_html=True
                    )
                
                # Job description
                description = job.get('description', '')
                if description:
                    if len(description) > 300:
                        with st.expander(f"Job Description"):
                            st.write(description)
                    else:
                        st.write(description)
                
                # Job details
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    if job.get('salary'):
                        salary_min, salary_max = job['salary']
                        if salary_min and salary_max:
                            st.write(f"**Salary:** ${salary_min:,} - ${salary_max:,}")
                        elif salary_min:
                            st.write(f"**Salary:** ${salary_min:,}+")
                
                with col4:
                    if job.get('job_type'):
                        st.write(f"**Type:** {job['job_type']}")
                
                with col5:
                    st.write(f"**Source:** {job.get('source', 'Unknown')}")
                
                # Apply button
                if job.get('apply_url'):
                    st.link_button(
                        "Apply Now",
                        job['apply_url'],
                        use_container_width=False
                    )
                
                # Matching details
                with st.expander("Why this job matches"):
                    if hasattr(features, 'skill_matches'):
                        st.write(f"**Skill Matches:** {features.skill_matches}")
                        st.write(f"**Keyword Matches:** {features.keyword_matches}")
                        st.write(f"**Title Relevance:** {features.title_relevance:.2f}")
                        st.write(f"**Experience Match:** {features.experience_match:.2f}")
                
                st.divider()
    
    def run(self):
        """Run the enhanced Streamlit application"""
        try:
            # Apply styling
            self.apply_custom_css()
            
            # Render main components
            self.render_main_header()
            
            # New description added here, outside the main header container
            st.markdown(
                """
                <p style='text-align: center; color: #555; margin-top: -1rem; margin-bottom: 2rem; font-size: 1.1rem;'>
                Our AI-powered tool simplifies your job search. Simply upload your resume and, optionally, a job description. The system will then perform a detailed professional analysis, identifying your key skills, strengths, and areas for improvement. Based on this, it will search for and rank top job opportunities, providing a compatibility score to help you find the perfect fit.
                </p>
                """,
                unsafe_allow_html=True
            )
            
            # Main tabs
            tab1, tab2 = st.tabs(["Resume Analysis", "Job Matching"])
            
            with tab1:
                self.render_resume_analysis_tab()
            
            with tab2:
                self.render_job_matching_tab()
            
            # Footer
            st.markdown("---")
            st.markdown(
                "<div style='text-align: center; color: #666; padding: 1rem;'>"
                "© 2025 Resume Analyzer. All rights reserved."
                "</div>",
                unsafe_allow_html=True
            )
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error("An unexpected error occurred. Please refresh the page.")

def main():
    """Main application entry point"""
    try:
        # Initialize and run the enhanced app
        app = EnhancedStreamlitApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        st.error("Failed to start the application. Please check your configuration.")
        st.info("Make sure all required environment variables are set and dependencies are installed.")

if __name__ == "__main__":
    main()
