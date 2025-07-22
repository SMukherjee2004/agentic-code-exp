"""
Test file structure extraction for Q&A agent.
"""
import json

# Mock repository analysis data based on the context you provided
mock_analysis = {
    'total_files': 7,
    'analyzed_files': 2,
    'files': [
        {
            'path': 'README.md',
            'full_path': 'repos/SMukherjee2004_eclipsed/README.md',
            'language': 'markdown',
            'size': 1452,
            'lines': 45,
            'content': '# 🌘 Eclipse Prediction Data Preprocessing and EDA\n\nThis repository contains a Jupyter notebook focused on preprocessing and exploratory data analysis (EDA) of a solar eclipse dataset...'
        },
        {
            'path': 'requirements.txt',
            'full_path': 'repos/SMukherjee2004_eclipsed/requirements.txt',
            'language': 'text',
            'size': 50,
            'lines': 6,
            'content': 'matplotlib\nnumpy\npandas\nseaborn\nfolium\nplotly'
        },
        {
            'path': 'Research_01.ipynb',
            'full_path': 'repos/SMukherjee2004_eclipsed/Research_01.ipynb',
            'language': 'jupyter',
            'size': 35000000,  # ~35MB as indicated in context
            'lines': 1000
        },
        {
            'path': 'LICENSE.txt',
            'full_path': 'repos/SMukherjee2004_eclipsed/LICENSE.txt',
            'language': 'text',
            'size': 1000,
            'lines': 20
        },
        {
            'path': 'icon.ico',
            'full_path': 'repos/SMukherjee2004_eclipsed/icon.ico',
            'language': 'binary',
            'size': 5000,
            'lines': 0
        }
    ]
}

mock_summary = {
    'overview': 'Eclipse Prediction Data Preprocessing and EDA repository',
    'structure_analysis': 'The repository contains a Jupyter notebook for eclipse data analysis, documentation files, and dependencies.',
    'language_breakdown': {
        'jupyter': {'files': 1, 'lines': 1000},
        'markdown': {'files': 1, 'lines': 45},
        'text': {'files': 2, 'lines': 26}
    }
}

print("🧪 Testing File Structure Extraction")
print("=" * 50)

try:
    from utils.qa_agent import QAAgent
    from utils.llm_utils import LLMUtils
    
    # Create Q&A agent (will use mock LLM for testing)
    qa_agent = QAAgent()
    
    # Load the mock context
    qa_agent.load_repository_context(mock_analysis, mock_summary)
    
    # Test structure question
    test_question = "What is the file structure of this folder?"
    
    print(f"Question: {test_question}")
    print("\nExtracting context...")
    
    # Extract context to see what the agent sees
    context = qa_agent._extract_relevant_context(test_question)
    print(f"Context type detected: {context['type']}")
    print(f"Files found: {len(context.get('files', []))}")
    
    # Get the formatted context
    context_text = qa_agent._prepare_context_for_llm(context, test_question)
    
    print("\n" + "="*30)
    print("FORMATTED CONTEXT:")
    print("="*30)
    print(context_text)
    print("="*30)
    
    print("\n✅ File structure extraction test completed!")
    print("\n📝 Expected behavior:")
    print("- Should show all 5 files: README.md, requirements.txt, Research_01.ipynb, LICENSE.txt, icon.ico")
    print("- Should not hallucinate any files like shopping_list.py")
    print("- Should include file sizes and languages")
    
except Exception as e:
    print(f"❌ Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
