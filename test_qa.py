"""
Test script to debug Q&A functionality.
Run this to test the Q&A agent independently.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_utils import LLMUtils
from utils.qa_agent import QAAgent

# Load environment variables
load_dotenv()

def test_qa_agent():
    """Test the Q&A agent with mock data."""
    print("🧪 Testing Q&A Agent")
    print("=" * 50)
    
    # Test 1: Initialize LLM utils
    print("1. Testing LLM initialization...")
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    llm = LLMUtils(api_key=api_key)
    print("✅ LLM initialized")
    
    # Test 2: Test API connection
    print("2. Testing API connection...")
    success, message = llm.test_api_connection()
    print(f"   {message}")
    if not success:
        print("❌ API connection failed")
        return
    
    # Test 3: Initialize Q&A agent
    print("3. Testing Q&A agent initialization...")
    qa_agent = QAAgent(llm)
    print("✅ Q&A agent initialized")
    
    # Test 4: Test with mock context
    print("4. Testing with mock repository context...")
    mock_analysis = {
        'total_files': 10,
        'analyzed_files': 8,
        'languages': {
            'python': {'files': 5, 'lines': 1000},
            'javascript': {'files': 3, 'lines': 500}
        },
        'summary': {
            'total_lines': 1500,
            'total_functions': 50,
            'total_classes': 15
        },
        'files': [
            {
                'path': 'app.py',
                'language': 'python',
                'lines': 200,
                'functions': [{'name': 'main', 'args': [], 'line': 10}],
                'classes': [{'name': 'App', 'methods': ['run'], 'line': 50}]
            },
            {
                'path': 'utils.js',
                'language': 'javascript',
                'lines': 100,
                'functions': [{'name': 'helper', 'args': ['data'], 'line': 5}],
                'classes': []
            }
        ]
    }
    
    mock_summary = {
        'overview': 'This is a web application built with Python and JavaScript.',
        'file_summaries': [
            {
                'file': 'app.py',
                'summary': 'Main application entry point with Flask server setup.',
                'language': 'python'
            }
        ],
        'key_components': [
            {
                'name': 'main',
                'files_count': 5,
                'total_lines': 800
            }
        ],
        'language_breakdown': {
            'python': {'files': 5, 'lines': 1000},
            'javascript': {'files': 3, 'lines': 500}
        }
    }
    
    qa_agent.load_repository_context(mock_analysis, mock_summary)
    print("✅ Mock context loaded")
    
    # Test 5: Test question suggestions
    print("5. Testing question suggestions...")
    try:
        suggestions = qa_agent.suggest_questions()
        print(f"   Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"   {i}. {suggestion}")
        print("✅ Question suggestions working")
    except Exception as e:
        print(f"❌ Question suggestions failed: {str(e)}")
        return
    
    # Test 6: Test Q&A functionality
    print("6. Testing Q&A functionality...")
    test_questions = [
        "What is the main purpose of this repository?",
        "What programming languages are used?",
        "What does the main function do?"
    ]
    
    for question in test_questions:
        print(f"\n   Q: {question}")
        try:
            answer, context = qa_agent.answer_question(question)
            print(f"   A: {answer[:100]}...")
            print("   ✅ Question answered successfully")
        except Exception as e:
            print(f"   ❌ Question failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Q&A Agent test completed!")

if __name__ == "__main__":
    test_qa_agent()
