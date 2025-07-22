"""
Code parsing utilities for analyzing repository structure and extracting code elements.
"""
import os
import ast
import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeParser:
    """Main class for parsing code repositories and extracting structure."""
    
    def __init__(self):
        """Initialize the code parser with language-specific handlers."""
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.md': 'markdown',
            '.txt': 'text',
            '.rst': 'restructuredtext'
        }
        
        self.ignore_dirs = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules', 
            'venv', 'env', '.env', 'build', 'dist', '.tox',
            'coverage', '.coverage', '.pytest_cache', '.mypy_cache',
            'target', 'bin', 'obj', '.gradle', '.idea', '.vscode',
            'vendor', 'deps', '_build', '.next', '.nuxt'
        }
        
        self.ignore_files = {
            '.gitignore', '.dockerignore', '.env', '.env.local',
            'package-lock.json', 'yarn.lock', 'poetry.lock',
            'Pipfile.lock', 'composer.lock'
        }
        
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.dat',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.zip', '.rar', '.tar', '.gz', '.7z',
            '.jar', '.war', '.ear', '.pyc', '.pyo', '.pyd'
        }
    
    def should_ignore_path(self, path: str) -> bool:
        """Check if a path should be ignored during analysis."""
        path_obj = Path(path)
        
        # Check if any parent directory should be ignored
        for part in path_obj.parts:
            if part in self.ignore_dirs:
                return True
        
        # Check file name
        if path_obj.name in self.ignore_files:
            return True
        
        # Check file extension
        if path_obj.suffix.lower() in self.binary_extensions:
            return True
        
        return False
    
    def get_file_language(self, file_path: str) -> Optional[str]:
        """Determine the programming language of a file based on its extension."""
        ext = Path(file_path).suffix.lower()
        return self.supported_extensions.get(ext)
    
    def analyze_repository(self, repo_path: str, progress_callback=None) -> Dict:
        """
        Analyze the entire repository structure and extract code information.
        
        Args:
            repo_path (str): Path to the repository
            progress_callback (callable): Optional progress callback
            
        Returns:
            dict: Repository analysis results
        """
        try:
            if progress_callback:
                progress_callback("Starting repository analysis...")
            
            analysis = {
                'repository_path': repo_path,
                'total_files': 0,
                'analyzed_files': 0,
                'languages': {},
                'files': [],
                'structure': {},
                'summary': {
                    'total_lines': 0,
                    'total_functions': 0,
                    'total_classes': 0,
                    'total_imports': 0
                }
            }
            
            # Walk through all files
            all_files = []
            for root, dirs, files in os.walk(repo_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore_path(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self.should_ignore_path(file_path):
                        all_files.append(file_path)
            
            analysis['total_files'] = len(all_files)
            
            # Analyze each file
            for i, file_path in enumerate(all_files):
                if progress_callback and i % 10 == 0:
                    progress_callback(f"Analyzing file {i+1}/{len(all_files)}")
                
                try:
                    file_analysis = self.analyze_file(file_path, repo_path)
                    if file_analysis:
                        analysis['files'].append(file_analysis)
                        analysis['analyzed_files'] += 1
                        
                        # Update language statistics
                        lang = file_analysis.get('language')
                        if lang:
                            if lang not in analysis['languages']:
                                analysis['languages'][lang] = {'files': 0, 'lines': 0}
                            analysis['languages'][lang]['files'] += 1
                            analysis['languages'][lang]['lines'] += file_analysis.get('lines', 0)
                        
                        # Update summary statistics
                        analysis['summary']['total_lines'] += file_analysis.get('lines', 0)
                        analysis['summary']['total_functions'] += len(file_analysis.get('functions', []))
                        analysis['summary']['total_classes'] += len(file_analysis.get('classes', []))
                        analysis['summary']['total_imports'] += len(file_analysis.get('imports', []))
                
                except Exception as e:
                    logger.warning(f"Error analyzing file {file_path}: {str(e)}")
                    continue
            
            # Generate directory structure
            analysis['structure'] = self.generate_directory_structure(repo_path)
            
            if progress_callback:
                progress_callback("Repository analysis completed!")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            return {}
    
    def analyze_file(self, file_path: str, repo_root: str) -> Optional[Dict]:
        """
        Analyze a single file and extract its structure.
        
        Args:
            file_path (str): Full path to the file
            repo_root (str): Root path of the repository
            
        Returns:
            dict: File analysis results or None if analysis failed
        """
        try:
            # Get relative path for better readability
            rel_path = os.path.relpath(file_path, repo_root)
            
            # Get file stats
            stat = os.stat(file_path)
            file_size = stat.st_size
            
            # Skip very large files (>1MB)
            if file_size > 1024 * 1024:
                return None
            
            # Determine language
            language = self.get_file_language(file_path)
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    return None
            
            lines = content.split('\n')
            
            file_info = {
                'path': rel_path,
                'full_path': file_path,
                'language': language,
                'size': file_size,
                'lines': len(lines),
                'content_preview': content[:500] + ('...' if len(content) > 500 else ''),
                'functions': [],
                'classes': [],
                'imports': [],
                'variables': [],
                'comments': []
            }
            
            # Store full content for important files (README, docs, small files)
            file_name_lower = Path(file_path).name.lower()
            if (
                'readme' in file_name_lower or 
                file_name_lower.startswith('license') or
                file_name_lower.startswith('changelog') or
                file_name_lower.startswith('contributing') or
                language in ['markdown', 'text', 'restructuredtext'] or
                len(content) < 5000  # Store full content for files smaller than 5KB
            ):
                file_info['content'] = content
            
            # Language-specific analysis
            if language == 'python':
                self.analyze_python_file(content, file_info)
            elif language in ['javascript', 'typescript']:
                self.analyze_js_file(content, file_info)
            elif language == 'java':
                self.analyze_java_file(content, file_info)
            elif language in ['markdown', 'text', 'restructuredtext']:
                self.analyze_text_file(content, file_info)
            else:
                # Generic analysis for other file types
                self.analyze_generic_file(content, file_info)
            
            return file_info
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {str(e)}")
            return None
    
    def analyze_python_file(self, content: str, file_info: Dict):
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node),
                        'decorators': [ast.unparse(dec) for dec in node.decorator_list] if hasattr(ast, 'unparse') else []
                    }
                    file_info['functions'].append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'bases': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                        'docstring': ast.get_docstring(node),
                        'methods': []
                    }
                    
                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info['methods'].append(item.name)
                    
                    file_info['classes'].append(class_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_info['imports'].append(alias.name)
                    else:
                        module = node.module or ''
                        for alias in node.names:
                            file_info['imports'].append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            file_info['variables'].append({
                                'name': target.id,
                                'line': node.lineno,
                                'type': 'assignment'
                            })
        
        except SyntaxError:
            # If file has syntax errors, do basic regex analysis
            self.analyze_generic_file(content, file_info)
        except Exception as e:
            logger.warning(f"Error in Python AST analysis: {str(e)}")
            self.analyze_generic_file(content, file_info)
    
    def analyze_js_file(self, content: str, file_info: Dict):
        """Analyze JavaScript/TypeScript file using regex patterns."""
        # Function patterns
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'(\w+)\s*:\s*function\s*\(',
            r'(\w+)\s*=>\s*{',
            r'(\w+)\s*=\s*function\s*\(',
            r'(\w+)\s*=\s*\([^)]*\)\s*=>'
        ]
        
        for pattern in func_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                file_info['functions'].append({
                    'name': match.group(1),
                    'line': line_num,
                    'type': 'function'
                })
        
        # Class patterns
        class_matches = re.finditer(r'class\s+(\w+)', content, re.MULTILINE)
        for match in class_matches:
            line_num = content[:match.start()].count('\n') + 1
            file_info['classes'].append({
                'name': match.group(1),
                'line': line_num
            })
        
        # Import patterns
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                file_info['imports'].append(match.group(1))
    
    def analyze_java_file(self, content: str, file_info: Dict):
        """Analyze Java file using regex patterns."""
        # Class pattern
        class_matches = re.finditer(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)', content)
        for match in class_matches:
            line_num = content[:match.start()].count('\n') + 1
            file_info['classes'].append({
                'name': match.group(1),
                'line': line_num
            })
        
        # Method pattern
        method_matches = re.finditer(r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*{', content)
        for match in method_matches:
            line_num = content[:match.start()].count('\n') + 1
            file_info['functions'].append({
                'name': match.group(1),
                'line': line_num,
                'type': 'method'
            })
        
        # Import pattern
        import_matches = re.finditer(r'import\s+([^;]+);', content)
        for match in import_matches:
            file_info['imports'].append(match.group(1).strip())
    
    def analyze_text_file(self, content: str, file_info: Dict):
        """Analyze text-based files (Markdown, README, etc.)."""
        lines = content.split('\n')
        
        # Extract headers for markdown
        if file_info['language'] == 'markdown':
            for i, line in enumerate(lines):
                if line.strip().startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    title = line.strip('#').strip()
                    file_info['functions'].append({
                        'name': title,
                        'line': i + 1,
                        'type': f'header_h{level}'
                    })
        
        # Extract any code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        file_info['code_blocks'] = len(code_blocks)
    
    def analyze_generic_file(self, content: str, file_info: Dict):
        """Generic analysis for unsupported file types."""
        # Look for common patterns
        lines = content.split('\n')
        
        # Count comments
        comment_patterns = [r'#.*', r'//.*', r'/\*.*?\*/', r'<!--.*?-->']
        for pattern in comment_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            file_info['comments'].extend(matches)
        
        # Look for function-like patterns
        func_pattern = r'(\w+)\s*\([^)]*\)\s*[{:]'
        matches = re.finditer(func_pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            file_info['functions'].append({
                'name': match.group(1),
                'line': line_num,
                'type': 'generic_function'
            })
    
    def generate_directory_structure(self, repo_path: str) -> Dict:
        """Generate a tree-like structure of the repository."""
        structure = {}
        
        for root, dirs, files in os.walk(repo_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore_path(os.path.join(root, d))]
            
            # Get relative path
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == '.':
                current_dict = structure
            else:
                path_parts = rel_root.split(os.sep)
                current_dict = structure
                for part in path_parts:
                    if part not in current_dict:
                        current_dict[part] = {}
                    current_dict = current_dict[part]
            
            # Add files
            filtered_files = [f for f in files if not self.should_ignore_path(os.path.join(root, f))]
            if filtered_files:
                if '_files' not in current_dict:
                    current_dict['_files'] = []
                current_dict['_files'].extend(filtered_files)
        
        return structure
