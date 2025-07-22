# AI GitHub Code Analyzer

An intelligent AI-powered tool that analyzes GitHub repositories, generates comprehensive summaries, and answers questions about codebases using advanced LLM technology.

## Features

🔹 **Repository Analysis**: Clone and analyze any public GitHub repository  
🔹 **Code Structure Parsing**: Extract files, folders, classes, functions, and variables  
🔹 **AI-Powered Summaries**: Generate detailed summaries using Mixtral LLM  
🔹 **Interactive Q&A**: Ask natural language questions about the codebase  
🔹 **Smart Filtering**: Automatically skip binary files and irrelevant directories  
🔹 **Visual Reports**: Beautiful Streamlit interface with structured outputs  

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **LLM**: OpenRouter API (Mixtral-8x7B-Instruct)
- **Git Operations**: GitPython
- **Code Parsing**: AST + Regex patterns

## Setup

1. **Clone this repository**
```bash
git clone <your-repo-url>
cd ai-github-code-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Get your free API key from [OpenRouter](https://openrouter.ai/)

4. **Run the application**
```bash
streamlit run app.py
```

## Usage

1. **Enter GitHub Repository URL**: Paste any public GitHub repository URL
2. **Click Analyze**: The tool will clone and analyze the repository
3. **View Summaries**: Get comprehensive file and function summaries
4. **Ask Questions**: Use the Q&A section to query the codebase

## Example

Input: `https://github.com/microsoft/vscode`

Output:
- Repository structure analysis
- File-by-file summaries
- Function and class explanations
- Overall project summary
- Interactive Q&A capabilities

## Project Structure

```
ai-github-code-analyzer/
├── app.py                  # Streamlit main application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore patterns
├── repos/                 # Temporary cloned repositories
├── utils/                 # Core utilities
│   ├── github_utils.py    # GitHub operations
│   ├── parser_utils.py    # Code parsing logic
│   ├── llm_utils.py       # LLM API integration
│   ├── summarizer.py      # Summary generation
│   └── qa_agent.py        # Q&A functionality
├── assets/                # Static assets
└── sample_output/         # Example outputs
```

## Configuration

The tool supports various configuration options:
- **Max files**: Limit number of files to analyze
- **File size limits**: Skip large files
- **Language filters**: Focus on specific programming languages
- **Directory exclusions**: Skip node_modules, .git, etc.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions, please open a GitHub issue or contact the maintainers.
