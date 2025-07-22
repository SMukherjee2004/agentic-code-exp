"""
Summarizer utilities for generating comprehensive repository summaries.
"""
import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import markdown
from utils.llm_utils import LLMUtils

logger = logging.getLogger(__name__)

class RepositorySummarizer:
    """Class for generating comprehensive repository summaries."""
    
    def __init__(self, llm_utils: Optional[LLMUtils] = None):
        """
        Initialize the summarizer.
        
        Args:
            llm_utils (LLMUtils): LLM utilities instance
        """
        self.llm = llm_utils or LLMUtils()
    
    def generate_comprehensive_summary(self, analysis: Dict, repo_info: Dict = None, progress_callback=None) -> Dict:
        """
        Generate a comprehensive summary of the repository.
        
        Args:
            analysis (dict): Repository analysis from parser
            repo_info (dict): Additional repository information
            progress_callback (callable): Progress callback function
            
        Returns:
            dict: Comprehensive summary with multiple sections
        """
        if progress_callback:
            progress_callback("Generating repository overview...")
        
        summary = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_files': analysis.get('total_files', 0),
                'analyzed_files': analysis.get('analyzed_files', 0),
                'repository_path': analysis.get('repository_path', ''),
                'repo_info': repo_info or {}
            },
            'overview': '',
            'file_summaries': [],
            'language_breakdown': analysis.get('languages', {}),
            'structure_analysis': '',
            'key_components': [],
            'recommendations': ''
        }
        
        # Generate overall repository summary
        if progress_callback:
            progress_callback("Analyzing repository structure...")
        
        summary['overview'] = self.llm.summarize_repository(analysis)
        
        # Generate file summaries
        files = analysis.get('files', [])
        if progress_callback:
            progress_callback("Generating file summaries...")
        
        # Prioritize important files
        important_files = self.get_important_files(files)
        
        for i, file_info in enumerate(important_files[:50]):  # Limit to 50 most important files
            if progress_callback and i % 5 == 0:
                progress_callback(f"Summarizing file {i+1}/{min(50, len(important_files))}")
            
            try:
                file_summary = self.llm.summarize_file(file_info)
                summary['file_summaries'].append({
                    'file': file_info.get('path', 'unknown'),
                    'language': file_info.get('language', 'unknown'),
                    'lines': file_info.get('lines', 0),
                    'summary': file_summary,
                    'functions_count': len(file_info.get('functions', [])),
                    'classes_count': len(file_info.get('classes', []))
                })
            except Exception as e:
                logger.warning(f"Error summarizing file {file_info.get('path', 'unknown')}: {str(e)}")
                continue
        
        # Analyze structure
        if progress_callback:
            progress_callback("Analyzing project structure...")
        
        summary['structure_analysis'] = self.analyze_project_structure(analysis)
        
        # Identify key components
        summary['key_components'] = self.identify_key_components(analysis)
        
        # Generate recommendations
        if progress_callback:
            progress_callback("Generating recommendations...")
        
        summary['recommendations'] = self.generate_recommendations(analysis)
        
        if progress_callback:
            progress_callback("Summary generation completed!")
        
        return summary
    
    def get_important_files(self, files: List[Dict]) -> List[Dict]:
        """
        Identify and prioritize important files for summarization.
        
        Args:
            files (list): List of file information dictionaries
            
        Returns:
            list: Prioritized list of important files
        """
        # Define importance scores based on various factors
        def calculate_importance_score(file_info):
            score = 0
            path = file_info.get('path', '').lower()
            language = file_info.get('language', '')
            lines = file_info.get('lines', 0)
            functions_count = len(file_info.get('functions', []))
            classes_count = len(file_info.get('classes', []))
            
            # High priority files
            if any(keyword in path for keyword in ['main', 'index', 'app', 'server', 'api', '__init__']):
                score += 50
            
            if any(keyword in path for keyword in ['readme', 'documentation', 'doc']):
                score += 40
            
            if any(keyword in path for keyword in ['config', 'settings', 'setup']):
                score += 30
            
            if path.endswith(('requirements.txt', 'package.json', 'pom.xml', 'cargo.toml')):
                score += 35
            
            # Language priorities
            if language in ['python', 'javascript', 'typescript', 'java', 'cpp']:
                score += 20
            elif language in ['markdown', 'yaml', 'json']:
                score += 10
            
            # Size and complexity factors
            if lines > 100:
                score += min(lines // 50, 20)  # Cap at 20 points
            
            if functions_count > 0:
                score += min(functions_count * 3, 30)
            
            if classes_count > 0:
                score += min(classes_count * 5, 25)
            
            # Penalize very large files
            if lines > 2000:
                score -= 20
            
            # Boost files in root or src directories
            if path.count('/') <= 1 or '/src/' in path:
                score += 15
            
            return score
        
        # Sort files by importance score
        scored_files = [(file_info, calculate_importance_score(file_info)) for file_info in files]
        scored_files.sort(key=lambda x: x[1], reverse=True)
        
        return [file_info for file_info, score in scored_files]
    
    def analyze_project_structure(self, analysis: Dict) -> str:
        """
        Analyze and describe the project structure.
        
        Args:
            analysis (dict): Repository analysis
            
        Returns:
            str: Structure analysis description
        """
        structure = analysis.get('structure', {})
        languages = analysis.get('languages', {})
        files = analysis.get('files', [])
        
        # Prepare structure context
        structure_info = f"""
Directory Structure:
{json.dumps(structure, indent=2)[:2000]}...

Languages Used:
{json.dumps(languages, indent=2)}

File Distribution:
- Total files: {len(files)}
- Configuration files: {len([f for f in files if any(cfg in f.get('path', '').lower() for cfg in ['config', 'settings', '.env', 'package.json', 'requirements.txt'])])}
- Documentation files: {len([f for f in files if f.get('language') in ['markdown', 'text', 'restructuredtext']])}
- Source code files: {len([f for f in files if f.get('language') in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust']])}
"""
        
        messages = [
            {
                "role": "system",
                "content": """You are a software architecture expert. Analyze the project structure and provide insights about:

1. **Project Organization**: How directories and files are organized
2. **Architecture Pattern**: What architectural pattern is being used (MVC, microservices, monolith, etc.)
3. **Technology Stack**: What technologies and frameworks are evident
4. **Code Organization**: How the codebase is structured and modularized
5. **Build and Configuration**: What build tools and configuration files are present

Provide a clear, structured analysis in markdown format, under 400 words."""
            },
            {
                "role": "user",
                "content": f"Analyze this project structure:\n\n{structure_info}"
            }
        ]
        
        response = self.llm.call_llm(messages, max_tokens=600, temperature=0.3)
        return response or "Unable to analyze project structure."
    
    def identify_key_components(self, analysis: Dict) -> List[Dict]:
        """
        Identify key components and modules in the repository.
        
        Args:
            analysis (dict): Repository analysis
            
        Returns:
            list: List of key components with descriptions
        """
        components = []
        files = analysis.get('files', [])
        
        # Group files by directory
        directories = {}
        for file_info in files:
            path = file_info.get('path', '')
            dir_path = os.path.dirname(path) if '/' in path else 'root'
            
            if dir_path not in directories:
                directories[dir_path] = []
            directories[dir_path].append(file_info)
        
        # Analyze each directory
        for dir_path, dir_files in directories.items():
            if len(dir_files) < 2:  # Skip single-file directories
                continue
            
            total_lines = sum(f.get('lines', 0) for f in dir_files)
            total_functions = sum(len(f.get('functions', [])) for f in dir_files)
            total_classes = sum(len(f.get('classes', [])) for f in dir_files)
            languages = set(f.get('language') for f in dir_files if f.get('language'))
            
            component = {
                'name': dir_path,
                'files_count': len(dir_files),
                'total_lines': total_lines,
                'functions_count': total_functions,
                'classes_count': total_classes,
                'languages': list(languages),
                'key_files': [f.get('path') for f in sorted(dir_files, key=lambda x: x.get('lines', 0), reverse=True)[:3]]
            }
            
            components.append(component)
        
        # Sort by importance (lines of code + complexity)
        components.sort(key=lambda x: x['total_lines'] + x['functions_count'] * 10 + x['classes_count'] * 20, reverse=True)
        
        return components[:10]  # Return top 10 components
    
    def generate_recommendations(self, analysis: Dict) -> str:
        """
        Generate recommendations for the codebase.
        
        Args:
            analysis (dict): Repository analysis
            
        Returns:
            str: Recommendations text
        """
        files = analysis.get('files', [])
        languages = analysis.get('languages', {})
        summary_stats = analysis.get('summary', {})
        
        # Prepare analysis context
        context = f"""
Repository Statistics:
- Total files analyzed: {len(files)}
- Total lines of code: {summary_stats.get('total_lines', 0)}
- Programming languages: {list(languages.keys())}
- Functions: {summary_stats.get('total_functions', 0)}
- Classes: {summary_stats.get('total_classes', 0)}

Large files (>500 lines): {len([f for f in files if f.get('lines', 0) > 500])}
Files without documentation: {len([f for f in files if not f.get('functions', []) or not any(func.get('docstring') for func in f.get('functions', []))])}
Configuration files present: {len([f for f in files if any(cfg in f.get('path', '').lower() for cfg in ['config', 'setup', 'package.json', 'requirements'])])}
"""
        
        messages = [
            {
                "role": "system",
                "content": """You are a senior software architect and code quality expert. Based on the repository analysis, provide actionable recommendations for:

1. **Code Organization**: Suggestions for better structure and modularity
2. **Documentation**: Areas that need better documentation
3. **Testing**: Testing strategy recommendations
4. **Performance**: Potential performance improvements
5. **Maintainability**: Ways to improve code maintainability
6. **Best Practices**: Language-specific best practices

Provide 5-7 specific, actionable recommendations in markdown format, under 400 words."""
            },
            {
                "role": "user",
                "content": f"Analyze this repository and provide recommendations:\n\n{context}"
            }
        ]
        
        response = self.llm.call_llm(messages, max_tokens=600, temperature=0.4)
        return response or "Unable to generate recommendations."
    
    def export_summary_to_markdown(self, summary: Dict, output_path: str = None) -> str:
        """
        Export the summary to a markdown file.
        
        Args:
            summary (dict): Comprehensive summary
            output_path (str): Output file path
            
        Returns:
            str: Markdown content
        """
        metadata = summary.get('metadata', {})
        
        markdown_content = f"""# Repository Analysis Report

**Generated:** {metadata.get('generated_at', 'Unknown')}  
**Total Files:** {metadata.get('total_files', 0)}  
**Analyzed Files:** {metadata.get('analyzed_files', 0)}  

## Overview

{summary.get('overview', 'No overview available')}

## Project Structure Analysis

{summary.get('structure_analysis', 'No structure analysis available')}

## Language Breakdown

"""
        
        # Add language statistics
        languages = summary.get('language_breakdown', {})
        for lang, stats in languages.items():
            markdown_content += f"- **{lang.capitalize()}**: {stats.get('files', 0)} files, {stats.get('lines', 0)} lines\n"
        
        markdown_content += "\n## Key Components\n\n"
        
        # Add key components
        components = summary.get('key_components', [])
        for component in components[:5]:  # Top 5 components
            markdown_content += f"### {component.get('name', 'Unknown')}\n"
            markdown_content += f"- Files: {component.get('files_count', 0)}\n"
            markdown_content += f"- Lines of code: {component.get('total_lines', 0)}\n"
            markdown_content += f"- Functions: {component.get('functions_count', 0)}\n"
            markdown_content += f"- Classes: {component.get('classes_count', 0)}\n"
            markdown_content += f"- Languages: {', '.join(component.get('languages', []))}\n\n"
        
        markdown_content += "## File Summaries\n\n"
        
        # Add file summaries
        file_summaries = summary.get('file_summaries', [])
        for file_summary in file_summaries[:20]:  # Top 20 files
            file_path = file_summary.get('file', 'Unknown')
            file_lang = file_summary.get('language', 'unknown')
            file_lines = file_summary.get('lines', 0)
            file_desc = file_summary.get('summary', 'No summary available')
            
            markdown_content += f"### `{file_path}`\n"
            markdown_content += f"**Language:** {file_lang} | **Lines:** {file_lines}\n\n"
            markdown_content += f"{file_desc}\n\n"
        
        markdown_content += f"## Recommendations\n\n{summary.get('recommendations', 'No recommendations available')}\n"
        
        # Save to file if path provided
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Summary exported to {output_path}")
            except Exception as e:
                logger.error(f"Error exporting summary: {str(e)}")
        
        return markdown_content
    
    def export_summary_to_json(self, summary: Dict, output_path: str = None) -> str:
        """
        Export the summary to a JSON file.
        
        Args:
            summary (dict): Comprehensive summary
            output_path (str): Output file path
            
        Returns:
            str: JSON content
        """
        json_content = json.dumps(summary, indent=2, default=str)
        
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                logger.info(f"Summary exported to {output_path}")
            except Exception as e:
                logger.error(f"Error exporting summary: {str(e)}")
        
        return json_content
