"""
LLM utilities for interacting with language models via OpenRouter API.
"""
import os
import requests
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMUtils:
    """Utility class for LLM API interactions."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistralai/mixtral-8x7b-instruct"):
        """
        Initialize LLM utilities.
        
        Args:
            api_key (str): OpenRouter API key
            model (str): Model to use for completions
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("No OpenRouter API key found. Please set OPENROUTER_API_KEY environment variable.")
    
    def call_llm(self, messages: List[Dict[str, str]], max_tokens: int = 2000, temperature: float = 0.3) -> Optional[str]:
        """
        Make a call to the LLM API.
        
        Args:
            messages (list): List of message dictionaries with 'role' and 'content'
            max_tokens (int): Maximum tokens to generate
            temperature (float): Temperature for generation
            
        Returns:
            str: Generated response or None if failed
        """
        if not self.api_key:
            return "Error: No API key configured. Please set your OpenRouter API key."
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ai-code-analyzer",
                "X-Title": "AI Code Analyzer"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Unexpected API response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return f"Error: API request failed - {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            return "Error: Invalid API response format"
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {str(e)}")
            return f"Error: {str(e)}"
    
    def summarize_file(self, file_info: Dict) -> str:
        """
        Generate a summary for a single file.
        
        Args:
            file_info (dict): File information from parser
            
        Returns:
            str: File summary
        """
        file_path = file_info.get('path', 'Unknown')
        language = file_info.get('language', 'unknown')
        lines = file_info.get('lines', 0)
        functions = file_info.get('functions', [])
        classes = file_info.get('classes', [])
        content_preview = file_info.get('content_preview', '')
        
        # Prepare context for the LLM
        context = f"""
File: {file_path}
Language: {language}
Lines of code: {lines}
Functions: {len(functions)}
Classes: {len(classes)}

Content preview:
```{language}
{content_preview}
```

Functions found:
{json.dumps([f.get('name', 'unnamed') for f in functions], indent=2)}

Classes found:
{json.dumps([c.get('name', 'unnamed') for c in classes], indent=2)}
"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert code analyst. Your task is to analyze source code files and provide clear, concise summaries. 

For each file, provide:
1. **Purpose**: What this file does in 1-2 sentences
2. **Key Components**: Main functions, classes, or important elements
3. **Dependencies**: Important imports or dependencies
4. **Notable Features**: Any interesting patterns, design choices, or important details

Keep your response well-structured and under 300 words. Use markdown formatting for clarity."""
            },
            {
                "role": "user",
                "content": f"Please analyze this code file and provide a comprehensive summary:\n\n{context}"
            }
        ]
        
        response = self.call_llm(messages, max_tokens=500, temperature=0.2)
        return response or "Failed to generate summary for this file."
    
    def summarize_repository(self, analysis: Dict) -> str:
        """
        Generate an overall summary of the repository.
        
        Args:
            analysis (dict): Repository analysis from parser
            
        Returns:
            str: Repository summary
        """
        total_files = analysis.get('total_files', 0)
        analyzed_files = analysis.get('analyzed_files', 0)
        languages = analysis.get('languages', {})
        summary_stats = analysis.get('summary', {})
        
        # Prepare repository overview
        overview = f"""
Repository Analysis Summary:
- Total files: {total_files}
- Analyzed files: {analyzed_files}
- Programming languages: {list(languages.keys())}
- Total lines of code: {summary_stats.get('total_lines', 0)}
- Total functions: {summary_stats.get('total_functions', 0)}
- Total classes: {summary_stats.get('total_classes', 0)}

Language breakdown:
{json.dumps(languages, indent=2)}

Key files analyzed:
"""
        
        # Add key files info
        files = analysis.get('files', [])
        important_files = sorted(files, key=lambda x: x.get('lines', 0), reverse=True)[:10]
        
        for file_info in important_files:
            overview += f"- {file_info.get('path', 'unknown')} ({file_info.get('language', 'unknown')}, {file_info.get('lines', 0)} lines)\n"
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert software architect and code analyst. Your task is to analyze repository structure and provide comprehensive project summaries.

For each repository, provide:
1. **Project Overview**: What this project appears to be (web app, library, tool, etc.)
2. **Architecture**: How the code is organized and structured
3. **Key Technologies**: Main languages, frameworks, and tools used
4. **Main Components**: Important modules, directories, or subsystems
5. **Purpose and Functionality**: What the project does and its main features
6. **Development Patterns**: Any notable coding patterns, architectural decisions

Keep your response well-structured, informative, and under 500 words. Use markdown formatting."""
            },
            {
                "role": "user",
                "content": f"Please analyze this repository and provide a comprehensive project summary:\n\n{overview}"
            }
        ]
        
        response = self.call_llm(messages, max_tokens=800, temperature=0.3)
        return response or "Failed to generate repository summary."
    
    def explain_function(self, function_info: Dict, file_context: str = "") -> str:
        """
        Explain what a specific function does.
        
        Args:
            function_info (dict): Function information
            file_context (str): Additional file context
            
        Returns:
            str: Function explanation
        """
        func_name = function_info.get('name', 'unknown')
        func_args = function_info.get('args', [])
        func_line = function_info.get('line', 0)
        docstring = function_info.get('docstring', '')
        
        context = f"""
Function: {func_name}
Arguments: {func_args}
Line number: {func_line}
Docstring: {docstring or 'None'}

File context:
{file_context[:1000]}...
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a code documentation expert. Explain what functions do in clear, concise language. Focus on the function's purpose, parameters, return value, and any side effects."
            },
            {
                "role": "user",
                "content": f"Please explain what this function does:\n\n{context}"
            }
        ]
        
        response = self.call_llm(messages, max_tokens=300, temperature=0.2)
        return response or f"Unable to explain function {func_name}."
    
    def answer_question(self, question: str, repository_context: str, file_summaries: List[str]) -> str:
        """
        Answer a natural language question about the repository.
        
        Args:
            question (str): User's question
            repository_context (str): Repository summary and context
            file_summaries (list): List of file summaries
            
        Returns:
            str: Answer to the question
        """
        # Prepare comprehensive context
        context = f"""
Repository Context:
{repository_context}

File Summaries:
{chr(10).join(file_summaries[:20])}  # Limit to first 20 files to avoid token limits
"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert software engineer with deep knowledge of codebases. Your task is to answer questions about repository contents based on the provided analysis.

Guidelines:
1. Provide accurate, specific answers based on the available information
2. If you're unsure about something, say so rather than guessing
3. Reference specific files, functions, or components when relevant
4. Keep answers concise but comprehensive
5. Use markdown formatting for clarity
6. If the question cannot be answered with the available information, explain what additional context would be needed

Answer the user's question using the repository analysis provided."""
            },
            {
                "role": "user",
                "content": f"Repository analysis:\n{context}\n\nQuestion: {question}"
            }
        ]
        
        response = self.call_llm(messages, max_tokens=1000, temperature=0.4)
        return response or "I'm unable to answer your question based on the available repository analysis."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            models = response.json()
            
            return [model['id'] for model in models.get('data', [])]
            
        except Exception as e:
            logger.error(f"Error fetching available models: {str(e)}")
            return [
                "mistralai/mixtral-8x7b-instruct",
                "anthropic/claude-3-haiku",
                "meta-llama/llama-3-8b-instruct",
                "microsoft/wizardlm-2-8x22b"
            ]
    
    def test_api_connection(self) -> Tuple[bool, str]:
        """
        Test the API connection and return status.
        
        Returns:
            tuple: (success, message)
        """
        if not self.api_key:
            return False, "No API key configured"
        
        test_messages = [
            {"role": "user", "content": "Hello! Please respond with 'API connection successful'"}
        ]
        
        response = self.call_llm(test_messages, max_tokens=50, temperature=0.1)
        
        if response and "API connection successful" in response:
            return True, "API connection successful"
        elif response:
            return True, f"API connected but unexpected response: {response}"
        else:
            return False, "API connection failed"
