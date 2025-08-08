"""
AI GitHub Code Analyzer - Main Streamlit Application

A comprehensive tool for analyzing GitHub repositories using AI-powered insights.
"""
import streamlit as st
import os
import json
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Import our utilities
from utils.github_utils import GitHubUtils
from utils.parser_utils import CodeParser
from utils.llm_utils import LLMUtils
from utils.summarizer import RepositorySummarizer
from utils.qa_agent import QAAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI GitHub Code Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .file-summary {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .question-suggestion {
        background: #e3f2fd;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.2rem 0;
        cursor: pointer;
        border: 1px solid #bbdefb;
    }
    .question-suggestion:hover {
        background: #bbdefb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'summary_data' not in st.session_state:
        st.session_state.summary_data = None
    if 'repo_info' not in st.session_state:
        st.session_state.repo_info = None
    if 'repo_path' not in st.session_state:
        st.session_state.repo_path = None
    if 'qa_agent' not in st.session_state:
        st.session_state.qa_agent = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

def main():
    """Main application function."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🔍 AI GitHub Code Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            help="Get your free API key from https://openrouter.ai/"
        )
        
        if api_key:
            os.environ['OPENROUTER_API_KEY'] = api_key
        
        # Model selection
        available_models = [
            "mistralai/mixtral-8x7b-instruct",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3-8b-instruct",
            "microsoft/wizardlm-2-8x22b"
        ]
        
        selected_model = st.selectbox(
            "Select LLM Model",
            available_models,
            help="Choose the language model for analysis"
        )
        
        # Analysis options
        st.subheader("📊 Analysis Options")
        max_files = st.slider("Max files to analyze", 10, 500, 100)
        include_docs = st.checkbox("Include documentation files", True)
        include_config = st.checkbox("Include configuration files", True)
        
        # Actions
        st.subheader("🔧 Actions")
        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.session_state.clear()
            st.success("Cache cleared!")
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Repository Input",
        "📊 Analysis Results", 
        "📝 File Summaries",
        "💬 Q&A Assistant",
        "📄 Export & Reports"
    ])
    
    with tab1:
        repository_input_tab(api_key, selected_model, max_files)
    
    with tab2:
        analysis_results_tab()
    
    with tab3:
        file_summaries_tab()
    
    with tab4:
        qa_assistant_tab()
    
    with tab5:
        export_reports_tab()

# def repository_input_tab(api_key, selected_model, max_files):
#     """Repository input and analysis tab."""
#     st.header("📥 Repository Analysis")
    
#     # URL input
#     col1, col2 = st.columns([3, 1])

#     # if "repo_url" not in st.session_state:
#     #     st.session_state.repo_url = ""
    
#     # with col1:
#     #     # repo_url = st.text_input(
#     #     #     "GitHub Repository URL",
#     #     #     placeholder="https://github.com/owner/repository",
#     #     #     help="Enter a public GitHub repository URL"
#     #     # )
#     #     repo_url = st.text_input(
#     #     "GitHub Repository URL",
#     #     value=st.session_state.repo_url,
#     #     placeholder="https://github.com/owner/repository",
#     #     help="Enter a public GitHub repository URL",
#     #     key="repo_url"
#     # )
#     # with col2:
#     #     st.markdown("<br>", unsafe_allow_html=True)
#     #     analyze_button = st.button("🔍 Analyze Repository", type="primary")

#     # Bind the text input to session state
#     if "repo_url" not in st.session_state:
#         st.session_state.repo_url = ""

#     # Example repositories
#     st.subheader("📚 Example Repositories")
#     example_repos = [
#         "https://github.com/microsoft/vscode",
#         "https://github.com/facebook/react",
#         "https://github.com/tensorflow/tensorflow",
#         "https://github.com/django/django",
#         "https://github.com/fastapi/fastapi"
#     ]
    
#     example_cols = st.columns(len(example_repos))
#     for i, repo in enumerate(example_repos):
#         with example_cols[i]:
#             repo_name = repo.split('/')[-1]
#             if st.button(f"📦 {repo_name}", key=f"example_{i}"):
#                 st.session_state.example_url = repo
#                 st.rerun()
    
#     # # Use example URL if selected
#     # if hasattr(st.session_state, 'example_url'):
#     #     repo_url = st.session_state.example_url
#     #     delattr(st.session_state, 'example_url')
    
#     with col1:
#         # repo_url = st.text_input(
#         #     "GitHub Repository URL",
#         #     placeholder="https://github.com/owner/repository",
#         #     help="Enter a public GitHub repository URL"
#         # )
#         repo_url = st.text_input(
#         "GitHub Repository URL",
#         value=st.session_state.repo_url,
#         placeholder="https://github.com/owner/repository",
#         help="Enter a public GitHub repository URL",
#         key="repo_url"
#     )
#     with col2:
#         st.markdown("<br>", unsafe_allow_html=True)
#         analyze_button = st.button("🔍 Analyze Repository", type="primary")


#     # Analysis process
#     if analyze_button and repo_url:
#         if not api_key:
#             st.error("⚠️ Please enter your OpenRouter API key in the sidebar.")
#             return
        
#         perform_analysis(repo_url, api_key, selected_model, max_files)


def repository_input_tab(api_key, selected_model, max_files):
    """Repository input and analysis tab."""
    st.header("📥 Repository Analysis")

    # Ensure session state key exists
    if "repo_url" not in st.session_state:
        st.session_state.repo_url = ""

    # Example repositories
    example_repos = [
        "https://github.com/microsoft/vscode",
        "https://github.com/facebook/react",
        "https://github.com/tensorflow/tensorflow",
        "https://github.com/django/django",
        "https://github.com/fastapi/fastapi"
    ]

    # Place example repo buttons
    st.subheader("📚 You may try with... ")
    example_cols = st.columns(len(example_repos))
    for i, repo in enumerate(example_repos):
        with example_cols[i]:
            repo_name = repo.split('/')[-1]
            if st.button(f"📦 {repo_name}", key=f"example_{i}"):
                # Set repo_url BEFORE text_input is rendered
                st.session_state.repo_url = repo
                st.rerun()

    # Now render text input AFTER possible updates from above
    col1, col2 = st.columns([3, 1])
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL",
            value=st.session_state.repo_url,
            placeholder="https://github.com/owner/repository",
            help="Enter a public GitHub repository URL",
            key="repo_url"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Repository", type="primary")

    # Analysis
    if analyze_button and repo_url:
        if not api_key:
            st.error("⚠️ Please enter your OpenRouter API key in the sidebar.")
            return
        perform_analysis(repo_url, api_key, selected_model, max_files)

def perform_analysis(repo_url, api_key, selected_model, max_files):
    """Perform repository analysis."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize utilities
        status_text.text("Initializing analysis tools...")
        github_utils = GitHubUtils()
        code_parser = CodeParser()
        llm_utils = LLMUtils(api_key=api_key, model=selected_model)
        summarizer = RepositorySummarizer(llm_utils)
        
        progress_bar.progress(10)
        
        # Test API connection
        status_text.text("Testing API connection...")
        api_success, api_message = llm_utils.test_api_connection()
        if not api_success:
            st.error(f"API connection failed: {api_message}")
            return
        
        progress_bar.progress(20)
        
        # Clone repository
        status_text.text("Cloning repository...")
        success, repo_path, error = github_utils.clone_repository(repo_url)
        
        if not success:
            st.error(f"Failed to clone repository: {error}")
            return
        
        progress_bar.progress(40)
        
        # Get repository info
        status_text.text("Extracting repository information...")
        repo_info = github_utils.get_repo_info(repo_path)
        st.session_state.repo_info = repo_info
        st.session_state.repo_path = repo_path
        
        progress_bar.progress(50)
        
        # Parse repository
        status_text.text("Analyzing code structure...")
        
        def update_progress(message):
            status_text.text(message)
        
        analysis = code_parser.analyze_repository(repo_path, progress_callback=update_progress)
        st.session_state.analysis_data = analysis
        
        progress_bar.progress(70)
        
        # Generate summaries
        status_text.text("Generating AI-powered summaries...")
        summary = summarizer.generate_comprehensive_summary(
            analysis, 
            repo_info, 
            progress_callback=update_progress
        )
        st.session_state.summary_data = summary
        
        progress_bar.progress(90)
        
        # Initialize Q&A agent
        status_text.text("Setting up Q&A assistant...")
        qa_agent = QAAgent(llm_utils)
        qa_agent.load_repository_context(analysis, summary)
        st.session_state.qa_agent = qa_agent
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        st.session_state.analysis_complete = True
        st.success("🎉 Repository analysis completed successfully!")
        
        # Clean up repository
        github_utils.cleanup_repo(repo_path)
        
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        logger.error(f"Analysis error: {str(e)}")

def analysis_results_tab():
    """Analysis results and overview tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Please analyze a repository first using the Repository Input tab.")
        return
    
    analysis = st.session_state.analysis_data
    summary = st.session_state.summary_data
    repo_info = st.session_state.repo_info
    
    # Repository overview
    st.header("📊 Repository Overview")
    
    # Basic stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Files",
            analysis.get('total_files', 0),
            help="Total number of files in the repository"
        )
    
    with col2:
        st.metric(
            "Analyzed Files",
            analysis.get('analyzed_files', 0),
            help="Number of files successfully analyzed"
        )
    
    with col3:
        st.metric(
            "Lines of Code",
            f"{analysis.get('summary', {}).get('total_lines', 0):,}",
            help="Total lines of code across all files"
        )
    
    with col4:
        st.metric(
            "Languages",
            len(analysis.get('languages', {})),
            help="Number of programming languages detected"
        )
    
    # Repository info
    if repo_info:
        st.subheader("📋 Repository Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Remote URL:**", repo_info.get('remote_url', 'Unknown'))
            if 'latest_commit' in repo_info:
                commit = repo_info['latest_commit']
                st.write("**Latest Commit:**", commit.get('hash', 'Unknown'))
                st.write("**Author:**", commit.get('author', 'Unknown'))
                st.write("**Date:**", commit.get('date', 'Unknown'))
        
        with col2:
            if 'stats' in repo_info:
                stats = repo_info['stats']
                st.write("**Repository Size:**", f"{stats.get('total_size_mb', 0):.2f} MB")
    
    # AI-generated overview
    st.subheader("🤖 AI-Generated Overview")
    overview = summary.get('overview', 'No overview available')
    st.markdown(overview)
    
    # Language breakdown
    st.subheader("📈 Language Breakdown")
    
    languages = analysis.get('languages', {})
    if languages:
        # Create language charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Files by language
            lang_files = {lang: stats['files'] for lang, stats in languages.items()}
            fig_files = px.pie(
                values=list(lang_files.values()),
                names=list(lang_files.keys()),
                title="Files by Language"
            )
            st.plotly_chart(fig_files, use_container_width=True)
        
        with col2:
            # Lines by language
            lang_lines = {lang: stats['lines'] for lang, stats in languages.items()}
            fig_lines = px.pie(
                values=list(lang_lines.values()),
                names=list(lang_lines.keys()),
                title="Lines of Code by Language"
            )
            st.plotly_chart(fig_lines, use_container_width=True)
        
        # Language details table
        lang_df = pd.DataFrame([
            {
                'Language': lang,
                'Files': stats['files'],
                'Lines': stats['lines'],
                'Avg Lines/File': round(stats['lines'] / stats['files'], 1) if stats['files'] > 0 else 0
            }
            for lang, stats in languages.items()
        ])
        lang_df = lang_df.sort_values('Lines', ascending=False)
        st.dataframe(lang_df, use_container_width=True)
    
    # Project structure
    st.subheader("🏗️ Project Structure Analysis")
    structure_analysis = summary.get('structure_analysis', 'No structure analysis available')
    st.markdown(structure_analysis)
    
    # Key components
    st.subheader("🔧 Key Components")
    components = summary.get('key_components', [])
    
    if components:
        for component in components[:5]:  # Show top 5 components
            with st.expander(f"📁 {component.get('name', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Files", component.get('files_count', 0))
                
                with col2:
                    st.metric("Lines", f"{component.get('total_lines', 0):,}")
                
                with col3:
                    st.metric("Functions", component.get('functions_count', 0))
                
                st.write("**Languages:**", ", ".join(component.get('languages', [])))
                st.write("**Key Files:**", ", ".join(component.get('key_files', [])[:3]))

def file_summaries_tab():
    """File summaries and detailed analysis tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Please analyze a repository first using the Repository Input tab.")
        return
    
    summary = st.session_state.summary_data
    file_summaries = summary.get('file_summaries', [])
    
    st.header("📝 File Summaries")
    
    if not file_summaries:
        st.warning("No file summaries available.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        languages = list(set(fs.get('language', 'unknown') for fs in file_summaries))
        selected_language = st.selectbox("Filter by Language", ["All"] + languages)
    
    with col2:
        min_lines = st.slider("Minimum Lines", 0, 1000, 0)
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Lines", "Functions", "Classes", "File Name"])
    
    # Filter and sort files
    filtered_summaries = file_summaries
    
    if selected_language != "All":
        filtered_summaries = [fs for fs in filtered_summaries if fs.get('language') == selected_language]
    
    if min_lines > 0:
        filtered_summaries = [fs for fs in filtered_summaries if fs.get('lines', 0) >= min_lines]
    
    # Sort files
    if sort_by == "Lines":
        filtered_summaries.sort(key=lambda x: x.get('lines', 0), reverse=True)
    elif sort_by == "Functions":
        filtered_summaries.sort(key=lambda x: x.get('functions_count', 0), reverse=True)
    elif sort_by == "Classes":
        filtered_summaries.sort(key=lambda x: x.get('classes_count', 0), reverse=True)
    else:  # File Name
        filtered_summaries.sort(key=lambda x: x.get('file', ''))
    
    # Display summaries
    st.write(f"Showing {len(filtered_summaries)} files")
    
    for file_summary in filtered_summaries:
        file_path = file_summary.get('file', 'Unknown')
        language = file_summary.get('language', 'unknown')
        lines = file_summary.get('lines', 0)
        functions_count = file_summary.get('functions_count', 0)
        classes_count = file_summary.get('classes_count', 0)
        summary_text = file_summary.get('summary', 'No summary available')
        
        with st.expander(f"📄 {file_path} ({language}, {lines} lines)"):
            # File stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Lines", lines)
            
            with col2:
                st.metric("Functions", functions_count)
            
            with col3:
                st.metric("Classes", classes_count)
            
            # AI summary
            st.markdown("**AI Summary:**")
            st.markdown(summary_text)

def qa_assistant_tab():
    """Q&A assistant tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Please analyze a repository first using the Repository Input tab.")
        return
    
    if not st.session_state.qa_agent:
        st.error("Q&A agent not initialized. Please re-analyze the repository.")
        return
    
    st.header("💬 Q&A Assistant")
    st.markdown("Ask questions about the repository in natural language!")
    
    qa_agent = st.session_state.qa_agent
    
    # Debug information
    if hasattr(qa_agent, 'context_cache') and qa_agent.context_cache:
        st.success(f"✅ Q&A Agent loaded with context for {len(qa_agent.context_cache.get('file_summaries', []))} files")
    else:
        st.warning("⚠️ Q&A Agent may not have proper context. Try re-analyzing the repository.")
    
    # Question suggestions
    st.subheader("💡 Suggested Questions")
    try:
        suggestions = qa_agent.suggest_questions()
    except Exception as e:
        st.error(f"Error generating suggestions: {str(e)}")
        suggestions = [
            "What is the main purpose of this repository?",
            "What programming languages are used?",
            "How is the code organized?"
        ]
    
    suggestion_cols = st.columns(2)
    for i, suggestion in enumerate(suggestions[:6]):  # Show 6 suggestions
        with suggestion_cols[i % 2]:
            if st.button(suggestion, key=f"suggestion_{i}"):
                st.session_state.selected_question = suggestion
                st.rerun()
    
    # Question input
    selected_question = st.session_state.get('selected_question', '')
    question_input = st.text_input(
        "Ask a question about the repository:",
        value=selected_question,
        placeholder="e.g., What is the main purpose of this repository?",
        key="question_input"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ask_button = st.button("🤔 Ask Question", type="primary", key="ask_question_btn")
    
    with col2:
        clear_button = st.button("🗑️ Clear History", key="clear_history_btn")
    
    # Clear the selected question after displaying it in the input
    if 'selected_question' in st.session_state and question_input:
        del st.session_state.selected_question
    
    if clear_button:
        qa_agent.clear_conversation_history()
        if 'conversation_history' in st.session_state:
            st.session_state.conversation_history = []
        st.success("Conversation history cleared!")
        st.rerun()
    
    # Process question
    if ask_button and question_input.strip():
        try:
            with st.spinner("Analyzing your question..."):
                answer, context_used = qa_agent.answer_question(question_input)
            
            # Display answer
            st.subheader("🤖 Answer")
            st.markdown(answer)
            
            # Show context used (optional)
            with st.expander("🔍 Context Used"):
                st.json(context_used)
            
            # Initialize conversation history if not exists
            if 'conversation_history' not in st.session_state:
                st.session_state.conversation_history = []
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                'question': question_input,
                'answer': answer,
                'timestamp': datetime.now().isoformat()
            })
            
            # Clear the selected question to reset for next question
            if 'selected_question' in st.session_state:
                del st.session_state.selected_question
            
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")
            logger.error(f"Q&A error: {str(e)}")
    
    # Show conversation history
    if st.session_state.conversation_history:
        st.subheader("📚 Conversation History")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(f"Q{len(st.session_state.conversation_history) - i}: {conv['question'][:50]}..."):
                st.markdown(f"**Question:** {conv['question']}")
                st.markdown(f"**Answer:** {conv['answer']}")
                st.caption(f"Asked at: {conv['timestamp']}")

def export_reports_tab():
    """Export and reports tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Please analyze a repository first using the Repository Input tab.")
        return
    
    summary = st.session_state.summary_data
    analysis = st.session_state.analysis_data
    
    st.header("📄 Export & Reports")
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.json({
            "Total Files": analysis.get('total_files', 0),
            "Analyzed Files": analysis.get('analyzed_files', 0),
            "Total Lines": analysis.get('summary', {}).get('total_lines', 0),
            "Total Functions": analysis.get('summary', {}).get('total_functions', 0),
            "Total Classes": analysis.get('summary', {}).get('total_classes', 0),
            "Languages": len(analysis.get('languages', {}))
        })
    
    with col2:
        if summary.get('language_breakdown'):
            st.json(summary['language_breakdown'])
    
    # Export options
    st.subheader("💾 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export as Markdown", type="primary"):
            summarizer = RepositorySummarizer()
            markdown_content = summarizer.export_summary_to_markdown(summary)
            
            st.download_button(
                label="⬇️ Download Markdown Report",
                data=markdown_content,
                file_name=f"repository_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    
    with col2:
        if st.button("📊 Export as JSON", type="primary"):
            summarizer = RepositorySummarizer()
            json_content = summarizer.export_summary_to_json(summary)
            
            st.download_button(
                label="⬇️ Download JSON Report",
                data=json_content,
                file_name=f"repository_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Recommendations
    if summary.get('recommendations'):
        st.subheader("💡 AI Recommendations")
        st.markdown(summary['recommendations'])
    
    # Raw data
    with st.expander("🔍 View Raw Analysis Data"):
        st.json(analysis)

if __name__ == "__main__":
    main()
