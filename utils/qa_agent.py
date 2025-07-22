"""
Q&A agent for answering natural language questions about repository contents.
"""
import logging
from typing import Dict, List, Optional, Tuple
import json
from utils.llm_utils import LLMUtils

logger = logging.getLogger(__name__)

class QAAgent:
    """Agent for answering questions about repository contents."""
    
    def __init__(self, llm_utils: Optional[LLMUtils] = None):
        """
        Initialize the Q&A agent.
        
        Args:
            llm_utils (LLMUtils): LLM utilities instance
        """
        self.llm = llm_utils or LLMUtils()
        self.context_cache = {}
        self.conversation_history = []
        self.search_index = {
            'files': {},
            'functions': {},
            'classes': {},
            'components': {}
        }
    
    def load_repository_context(self, analysis: Dict, summary: Dict):
        """
        Load repository context for answering questions.
        
        Args:
            analysis (dict): Repository analysis from parser
            summary (dict): Repository summary from summarizer
        """
        self.context_cache = {
            'analysis': analysis,
            'summary': summary,
            'repository_overview': summary.get('overview', ''),
            'file_summaries': summary.get('file_summaries', []),
            'structure_analysis': summary.get('structure_analysis', ''),
            'key_components': summary.get('key_components', []),
            'language_breakdown': summary.get('language_breakdown', {}),
            'metadata': summary.get('metadata', {})
        }
        
        # Create searchable index of files and functions
        self._build_search_index()
    
    def _build_search_index(self):
        """Build a searchable index of repository contents."""
        self.search_index = {
            'files': {},
            'functions': {},
            'classes': {},
            'components': {}
        }
        
        analysis = self.context_cache.get('analysis', {})
        files = analysis.get('files', [])
        
        # Index files
        for file_info in files:
            file_path = file_info.get('path', '')
            self.search_index['files'][file_path.lower()] = file_info
            
            # Index functions
            for func in file_info.get('functions', []):
                func_name = func.get('name', '').lower()
                if func_name:
                    if func_name not in self.search_index['functions']:
                        self.search_index['functions'][func_name] = []
                    self.search_index['functions'][func_name].append({
                        'file': file_path,
                        'function': func,
                        'file_info': file_info
                    })
            
            # Index classes
            for cls in file_info.get('classes', []):
                cls_name = cls.get('name', '').lower()
                if cls_name:
                    if cls_name not in self.search_index['classes']:
                        self.search_index['classes'][cls_name] = []
                    self.search_index['classes'][cls_name].append({
                        'file': file_path,
                        'class': cls,
                        'file_info': file_info
                    })
        
        # Index components
        components = self.context_cache.get('key_components', [])
        for component in components:
            comp_name = component.get('name', '').lower()
            self.search_index['components'][comp_name] = component
    
    def answer_question(self, question: str, include_context: bool = True) -> Tuple[str, Dict]:
        """
        Answer a question about the repository.
        
        Args:
            question (str): User's question
            include_context (bool): Whether to include context in response
            
        Returns:
            tuple: (answer, context_used)
        """
        try:
            # Analyze question to determine what context to include
            relevant_context = self._extract_relevant_context(question)
            
            # Prepare context for LLM
            context_text = self._prepare_context_for_llm(relevant_context, question)
            
            # Generate answer
            answer = self._generate_answer(question, context_text)
            
            # Add to conversation history
            self.conversation_history.append({
                'question': question,
                'answer': answer,
                'context_used': relevant_context
            })
            
            # Keep only last 10 conversations
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return answer, relevant_context
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your question: {str(e)}", {}
    
    def _extract_relevant_context(self, question: str) -> Dict:
        """
        Extract relevant context based on the question.
        
        Args:
            question (str): User's question
            
        Returns:
            dict: Relevant context information
        """
        question_lower = question.lower()
        context = {
            'type': 'general',
            'files': [],
            'functions': [],
            'classes': [],
            'components': [],
            'metadata': self.context_cache.get('metadata', {})
        }
        
        # Determine question type
        if any(keyword in question_lower for keyword in ['function', 'method', 'def ', 'function named']):
            context['type'] = 'function'
        elif any(keyword in question_lower for keyword in ['class', 'object', 'inheritance']):
            context['type'] = 'class'
        elif any(keyword in question_lower for keyword in ['file', 'module', 'script']):
            context['type'] = 'file'
        elif any(keyword in question_lower for keyword in ['structure', 'architecture', 'organization', 'folder', 'directory']):
            context['type'] = 'structure'
        elif any(keyword in question_lower for keyword in ['language', 'technology', 'framework']):
            context['type'] = 'technology'
        
        # Search for specific mentions
        # Look for file names
        for file_path, file_info in self.search_index['files'].items():
            if any(part in question_lower for part in file_path.split('/') if len(part) > 3):
                context['files'].append(file_info)
        
        # Special handling for README questions
        if 'readme' in question_lower:
            context['type'] = 'readme'
            for file_path, file_info in self.search_index['files'].items():
                if 'readme' in file_path.lower():
                    context['files'].append(file_info)
        
        # Special handling for documentation questions
        if any(keyword in question_lower for keyword in ['documentation', 'docs', 'doc']):
            context['type'] = 'documentation'
            for file_path, file_info in self.search_index['files'].items():
                if any(doc_indicator in file_path.lower() for doc_indicator in ['readme', 'doc', 'guide', 'manual']):
                    context['files'].append(file_info)
        
        # Look for function names
        for func_name, func_list in self.search_index['functions'].items():
            if func_name in question_lower and len(func_name) > 3:
                context['functions'].extend(func_list)
        
        # Look for class names
        for cls_name, cls_list in self.search_index['classes'].items():
            if cls_name in question_lower and len(cls_name) > 3:
                context['classes'].extend(cls_list)
        
        # Look for component names
        for comp_name, component in self.search_index['components'].items():
            if comp_name in question_lower and len(comp_name) > 3:
                context['components'].append(component)
        
        # If no specific context found, provide general context based on question type
        if not any([context['files'], context['functions'], context['classes'], context['components']]):
            if context['type'] == 'function':
                # Provide top functions
                all_functions = []
                for func_list in list(self.search_index['functions'].values())[:10]:
                    all_functions.extend(func_list)
                context['functions'] = all_functions[:20]
            
            elif context['type'] == 'file':
                # Provide important files
                context['files'] = list(self.search_index['files'].values())[:15]
            
            elif context['type'] == 'class':
                # Provide top classes
                all_classes = []
                for cls_list in list(self.search_index['classes'].values())[:10]:
                    all_classes.extend(cls_list)
                context['classes'] = all_classes[:15]
        
        return context
    
    def _prepare_context_for_llm(self, context: Dict, question: str) -> str:
        """
        Prepare context text for the LLM.
        
        Args:
            context (dict): Relevant context
            question (str): User's question
            
        Returns:
            str: Formatted context text
        """
        context_parts = []
        
        # Add repository overview
        overview = self.context_cache.get('repository_overview', '')
        if overview:
            context_parts.append(f"Repository Overview:\n{overview}\n")
        
        # Add file structure information for structure questions
        if context['type'] in ['structure', 'file']:
            analysis = self.context_cache.get('analysis', {})
            all_files = analysis.get('files', [])
            
            if all_files:
                context_parts.append("Complete File Structure:")
                for file_info in all_files:
                    file_path = file_info.get('path', 'unknown')
                    language = file_info.get('language', 'unknown')
                    size = file_info.get('size', 0)
                    lines = file_info.get('lines', 0)
                    context_parts.append(f"- {file_path} ({language}, {size} bytes, {lines} lines)")
                
                # Add summary statistics
                total_files = analysis.get('total_files', len(all_files))
                analyzed_files = analysis.get('analyzed_files', len(all_files))
                context_parts.append(f"\nTotal files: {total_files}, Analyzed files: {analyzed_files}")
                context_parts.append("")
        
        # Add structure analysis if relevant
        if context['type'] in ['structure', 'general']:
            structure = self.context_cache.get('structure_analysis', '')
            if structure:
                context_parts.append(f"Project Structure Analysis:\n{structure}\n")
        
        # Add language breakdown if relevant
        if context['type'] in ['technology', 'general']:
            languages = self.context_cache.get('language_breakdown', {})
            if languages:
                context_parts.append(f"Language Breakdown:\n{json.dumps(languages, indent=2)}\n")
        
        # Add file information
        if context['files']:
            context_parts.append("Relevant Files:")
            for file_info in context['files'][:10]:  # Limit to 10 files
                file_path = file_info.get('path', 'unknown')
                language = file_info.get('language', 'unknown')
                lines = file_info.get('lines', 0)
                functions = len(file_info.get('functions', []))
                classes = len(file_info.get('classes', []))
                
                context_parts.append(f"- {file_path} ({language}, {lines} lines, {functions} functions, {classes} classes)")
                
                # Include file content for important files like README, small files, or specifically mentioned files
                content = file_info.get('content', file_info.get('content_preview', ''))
                if content and (
                    'readme' in file_path.lower() or 
                    'license' in file_path.lower() or
                    'changelog' in file_path.lower() or
                    'contributing' in file_path.lower() or
                    language in ['markdown', 'text', 'restructuredtext'] or
                    lines < 100 or 
                    any(part.lower() in question.lower() for part in file_path.split('/'))
                ):
                    # Use full content if available, otherwise use preview
                    full_content = file_info.get('content', content)
                    if len(full_content) > 3000:
                        # For very long files, show first part + relevant sections
                        context_parts.append(f"  Content (first 3000 chars):\n```\n{full_content[:3000]}...\n```")
                    else:
                        context_parts.append(f"  Full Content:\n```\n{full_content}\n```")
            context_parts.append("")
        
        # Add function information
        if context['functions']:
            context_parts.append("Relevant Functions:")
            for func_info in context['functions'][:10]:  # Limit to 10 functions
                func = func_info.get('function', {})
                file_path = func_info.get('file', 'unknown')
                func_name = func.get('name', 'unknown')
                args = func.get('args', [])
                line = func.get('line', 0)
                docstring = func.get('docstring', '')
                
                context_parts.append(f"- {func_name}({', '.join(args)}) in {file_path}:{line}")
                if docstring:
                    context_parts.append(f"  Description: {docstring[:200]}...")
            context_parts.append("")
        
        # Add class information
        if context['classes']:
            context_parts.append("Relevant Classes:")
            for cls_info in context['classes'][:10]:  # Limit to 10 classes
                cls = cls_info.get('class', {})
                file_path = cls_info.get('file', 'unknown')
                cls_name = cls.get('name', 'unknown')
                methods = cls.get('methods', [])
                line = cls.get('line', 0)
                docstring = cls.get('docstring', '')
                
                context_parts.append(f"- {cls_name} in {file_path}:{line}")
                if methods:
                    context_parts.append(f"  Methods: {', '.join(methods[:5])}")
                if docstring:
                    context_parts.append(f"  Description: {docstring[:200]}...")
            context_parts.append("")
        
        # Add component information
        if context['components']:
            context_parts.append("Relevant Components:")
            for component in context['components'][:5]:  # Limit to 5 components
                name = component.get('name', 'unknown')
                files_count = component.get('files_count', 0)
                lines = component.get('total_lines', 0)
                functions = component.get('functions_count', 0)
                classes = component.get('classes_count', 0)
                
                context_parts.append(f"- {name}: {files_count} files, {lines} lines, {functions} functions, {classes} classes")
            context_parts.append("")
        
        # Add file summaries if relevant
        if context['type'] in ['general', 'file'] and not context['files']:
            file_summaries = self.context_cache.get('file_summaries', [])[:5]
            if file_summaries:
                context_parts.append("Key File Summaries:")
                for file_summary in file_summaries:
                    file_path = file_summary.get('file', 'unknown')
                    summary_text = file_summary.get('summary', 'No summary')[:300]
                    context_parts.append(f"- {file_path}: {summary_text}...")
                context_parts.append("")
        
        # Add conversation history for context
        if self.conversation_history:
            context_parts.append("Recent Conversation:")
            for conv in self.conversation_history[-3:]:  # Last 3 conversations
                context_parts.append(f"Q: {conv['question'][:100]}...")
                context_parts.append(f"A: {conv['answer'][:200]}...")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context_text: str) -> str:
        """
        Generate an answer using the LLM.
        
        Args:
            question (str): User's question
            context_text (str): Formatted context
            
        Returns:
            str: Generated answer
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert software engineer and code analyst. Your task is to answer questions about a repository based on the provided analysis and context.

Guidelines for answering:
1. ONLY answer based on the provided context - do not hallucinate or make assumptions
2. If file content is provided in the context, reference it directly and quote relevant sections
3. Be specific and accurate - reference exact file names, line numbers, and content when available
4. If you cannot answer based on the provided context, clearly state what information is missing
5. For README questions, quote the actual content from the README file if provided
6. For file structure questions, list ONLY the files shown in the "Complete File Structure" section
7. Use markdown formatting for clarity and code blocks for file content
8. When discussing code, provide relevant details like file locations, function signatures, etc.
9. If the question asks about file content that isn't provided, explain that the content analysis is limited
10. Never mention files that are not explicitly listed in the provided context

Remember: Your credibility depends on accuracy. Only state what you can verify from the provided repository analysis. Do not invent or assume the existence of files not shown in the context."""
            },
            {
                "role": "user",
                "content": f"Repository Context:\n{context_text}\n\nQuestion: {question}\n\nPlease provide an accurate answer based strictly on the repository analysis above. If file content is shown in the context, reference it directly. For file structure questions, only list the files explicitly shown in the 'Complete File Structure' section."
            }
        ]
        
        response = self.llm.call_llm(messages, max_tokens=1000, temperature=0.4)
        return response or "I'm unable to answer your question based on the available repository analysis. Could you please rephrase your question or be more specific?"
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
    
    def suggest_questions(self) -> List[str]:
        """
        Suggest relevant questions based on the repository context.
        
        Returns:
            list: List of suggested questions
        """
        if not self.context_cache:
            return [
                "What is the main purpose of this repository?",
                "What programming languages are used?",
                "How is the code organized?"
            ]
        
        try:
            suggestions = []
            
            # General questions
            suggestions.extend([
                "What is the main purpose of this repository?",
                "What programming languages are used in this project?",
                "How is the code organized and structured?"
            ])
            
            # Function-specific questions
            functions = self.search_index.get('functions', {})
            if functions:
                top_functions = list(functions.keys())[:3]
                for func_name in top_functions:
                    suggestions.append(f"What does the {func_name} function do?")
            
            # Class-specific questions
            classes = self.search_index.get('classes', {})
            if classes:
                top_classes = list(classes.keys())[:2]
                for cls_name in top_classes:
                    suggestions.append(f"What is the {cls_name} class used for?")
            
            # File-specific questions
            files = list(self.search_index.get('files', {}).keys())[:3]
            for file_path in files:
                if any(important in file_path.lower() for important in ['main', 'app', 'index', 'api']):
                    suggestions.append(f"What does the {file_path} file contain?")
            
            # Technology questions
            languages = self.context_cache.get('language_breakdown', {})
            if len(languages) > 1:
                suggestions.append("What frameworks and libraries are being used?")
                suggestions.append("How are different technologies integrated in this project?")
            
            # Architecture questions
            components = self.context_cache.get('key_components', [])
            if len(components) > 2:
                suggestions.extend([
                    "What are the main components of this application?",
                    "How do different modules interact with each other?"
                ])
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error generating question suggestions: {str(e)}")
            return [
                "What is the main purpose of this repository?",
                "What programming languages are used?",
                "How is the code organized?",
                "What are the main components?",
                "How does this project work?"
            ]
