"""
Demo script for the AI GitHub Code Analyzer.
Run this script to see the analyzer in action with example repositories.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our utilities
from utils.github_utils import GitHubUtils
from utils.parser_utils import CodeParser
from utils.llm_utils import LLMUtils
from utils.summarizer import RepositorySummarizer
from utils.qa_agent import QAAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_analysis(repo_url: str, api_key: str = None):
    """
    Demonstrate the analysis capabilities on a sample repository.
    
    Args:
        repo_url (str): GitHub repository URL to analyze
        api_key (str): OpenRouter API key
    """
    print(f"🔍 Starting analysis of: {repo_url}")
    print("=" * 80)
    
    try:
        # Initialize utilities
        print("📦 Initializing analysis tools...")
        github_utils = GitHubUtils()
        code_parser = CodeParser()
        llm_utils = LLMUtils(api_key=api_key)
        summarizer = RepositorySummarizer(llm_utils)
        
        # Test API connection
        print("🔗 Testing LLM API connection...")
        api_success, api_message = llm_utils.test_api_connection()
        print(f"   {api_message}")
        
        if not api_success:
            print("❌ Cannot proceed without valid API connection")
            return
        
        # Clone repository
        print("📥 Cloning repository...")
        success, repo_path, error = github_utils.clone_repository(repo_url)
        
        if not success:
            print(f"❌ Failed to clone repository: {error}")
            return
        
        print(f"✅ Repository cloned to: {repo_path}")
        
        # Get repository info
        print("📊 Extracting repository information...")
        repo_info = github_utils.get_repo_info(repo_path)
        
        if repo_info:
            print(f"   Latest commit: {repo_info.get('latest_commit', {}).get('hash', 'Unknown')}")
            print(f"   Repository size: {repo_info.get('stats', {}).get('total_size_mb', 0):.2f} MB")
        
        # Parse repository
        print("🔍 Analyzing code structure...")
        analysis = code_parser.analyze_repository(repo_path)
        
        print(f"✅ Analysis complete!")
        print(f"   Total files: {analysis.get('total_files', 0)}")
        print(f"   Analyzed files: {analysis.get('analyzed_files', 0)}")
        print(f"   Languages found: {list(analysis.get('languages', {}).keys())}")
        print(f"   Lines of code: {analysis.get('summary', {}).get('total_lines', 0):,}")
        print(f"   Functions: {analysis.get('summary', {}).get('total_functions', 0)}")
        print(f"   Classes: {analysis.get('summary', {}).get('total_classes', 0)}")
        
        # Generate summaries
        print("🤖 Generating AI-powered summaries...")
        summary = summarizer.generate_comprehensive_summary(analysis, repo_info)
        
        print("✅ Summary generation complete!")
        
        # Display overview
        print("\n" + "=" * 80)
        print("📋 REPOSITORY OVERVIEW")
        print("=" * 80)
        overview = summary.get('overview', 'No overview available')
        print(overview)
        
        # Display structure analysis
        print("\n" + "=" * 80)
        print("🏗️ PROJECT STRUCTURE ANALYSIS")
        print("=" * 80)
        structure = summary.get('structure_analysis', 'No structure analysis available')
        print(structure)
        
        # Display key components
        print("\n" + "=" * 80)
        print("🔧 KEY COMPONENTS")
        print("=" * 80)
        components = summary.get('key_components', [])
        for i, component in enumerate(components[:3], 1):
            print(f"{i}. {component.get('name', 'Unknown')}")
            print(f"   Files: {component.get('files_count', 0)}")
            print(f"   Lines: {component.get('total_lines', 0):,}")
            print(f"   Functions: {component.get('functions_count', 0)}")
            print(f"   Classes: {component.get('classes_count', 0)}")
            print()
        
        # Display file summaries (top 3)
        print("📝 TOP FILE SUMMARIES")
        print("=" * 80)
        file_summaries = summary.get('file_summaries', [])
        for i, file_summary in enumerate(file_summaries[:3], 1):
            file_path = file_summary.get('file', 'Unknown')
            summary_text = file_summary.get('summary', 'No summary')
            
            print(f"{i}. {file_path}")
            print(f"   {summary_text[:200]}...")
            print()
        
        # Q&A demonstration
        print("💬 Q&A DEMONSTRATION")
        print("=" * 80)
        
        qa_agent = QAAgent(llm_utils)
        qa_agent.load_repository_context(analysis, summary)
        
        demo_questions = [
            "What is the main purpose of this repository?",
            "What programming languages are used?",
            "What are the key components of this project?"
        ]
        
        for question in demo_questions:
            print(f"Q: {question}")
            answer, _ = qa_agent.answer_question(question)
            print(f"A: {answer[:300]}...")
            print()
        
        # Export demonstration
        print("📄 EXPORT DEMONSTRATION")
        print("=" * 80)
        
        # Export to markdown
        markdown_filename = f"demo_analysis_{repo_url.split('/')[-1]}.md"
        markdown_content = summarizer.export_summary_to_markdown(summary, markdown_filename)
        print(f"✅ Markdown report exported to: {markdown_filename}")
        
        # Export to JSON
        json_filename = f"demo_analysis_{repo_url.split('/')[-1]}.json"
        json_content = summarizer.export_summary_to_json(summary, json_filename)
        print(f"✅ JSON report exported to: {json_filename}")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("💡 AI RECOMMENDATIONS")
        print("=" * 80)
        recommendations = summary.get('recommendations', 'No recommendations available')
        print(recommendations)
        
        # Clean up
        print("\n🧹 Cleaning up...")
        github_utils.cleanup_repo(repo_path)
        print("✅ Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")

def main():
    """Main demo function."""
    print("🚀 AI GitHub Code Analyzer Demo")
    print("=" * 80)
    
    # Check for API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("⚠️  No OpenRouter API key found!")
        print("   Please set your OPENROUTER_API_KEY environment variable")
        print("   or create a .env file with your API key")
        print("   Get your free API key from: https://openrouter.ai/")
        return
    
    # Demo repositories (small, well-structured repos)
    demo_repos = [
        "https://github.com/pallets/flask",
        "https://github.com/psf/requests",
        "https://github.com/kennethreitz/envoy",
        "https://github.com/getsentry/responses"
    ]
    
    print("📚 Available demo repositories:")
    for i, repo in enumerate(demo_repos, 1):
        print(f"   {i}. {repo}")
    
    print()
    
    try:
        # Let user choose or default to first repo
        choice = input("Enter repository number (1-4) or press Enter for default: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(demo_repos):
            selected_repo = demo_repos[int(choice) - 1]
        else:
            selected_repo = demo_repos[0]  # Default to first repo
        
        print(f"🎯 Selected repository: {selected_repo}")
        print()
        
        # Run the demo
        demo_analysis(selected_repo, api_key)
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {str(e)}")

if __name__ == "__main__":
    main()
