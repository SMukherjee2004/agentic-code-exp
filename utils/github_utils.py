"""
GitHub utilities for cloning and managing repositories.
"""
import os
import shutil
import re
import stat
import time
import subprocess
from git import Repo, GitCommandError, Git
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class GitHubUtils:
    """Utility class for GitHub repository operations."""
    
    def __init__(self, base_dir="repos"):
        """Initialize with base directory for cloned repos."""
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _on_rm_error(self, func, path, exc_info):
        """Error handler for Windows readonly files during removal."""
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
            func(path)
    
    def _force_remove_directory(self, path):
        """Force remove directory with robust error handling."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if os.path.exists(path):
                    # First attempt: standard removal
                    shutil.rmtree(path, onerror=self._on_rm_error)
                    return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} to remove {path} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    logger.error(f"Failed to remove directory after {max_retries} attempts: {e}")
                    return False
        return True
    
    def validate_github_url(self, url):
        """
        Validate if the provided URL is a valid GitHub repository URL.
        
        Args:
            url (str): GitHub repository URL
            
        Returns:
            tuple: (is_valid, repo_name, error_message)
        """
        try:
            # Clean up the URL
            url = url.strip()
            if not url:
                return False, None, "URL cannot be empty"
            
            # Add https if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Parse URL
            parsed = urlparse(url)
            
            # Check if it's GitHub
            if parsed.netloc.lower() not in ['github.com', 'www.github.com']:
                return False, None, "URL must be from github.com"
            
            # Extract path parts
            path_parts = [part for part in parsed.path.split('/') if part]
            
            if len(path_parts) < 2:
                return False, None, "Invalid GitHub URL format. Expected: github.com/owner/repo"
            
            owner, repo = path_parts[0], path_parts[1]
            
            # Remove .git suffix if present
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Validate owner and repo names
            if not re.match(r'^[a-zA-Z0-9._-]+$', owner):
                return False, None, "Invalid owner name"
            
            if not re.match(r'^[a-zA-Z0-9._-]+$', repo):
                return False, None, "Invalid repository name"
            
            repo_name = f"{owner}/{repo}"
            return True, repo_name, None
            
        except Exception as e:
            return False, None, f"URL validation error: {str(e)}"
    
    def clone_repository(self, url, progress_callback=None):
        """
        Clone a GitHub repository to local directory.
        
        Args:
            url (str): GitHub repository URL
            progress_callback (callable): Optional callback for progress updates
            
        Returns:
            tuple: (success, local_path, error_message)
        """
        try:
            # Validate URL first
            is_valid, repo_name, error = self.validate_github_url(url)
            if not is_valid:
                return False, None, error
            
            # Prepare local directory
            safe_name = repo_name.replace('/', '_')
            local_path = os.path.join(self.base_dir, safe_name)
            
            # Remove existing directory if it exists using improved cleanup
            if os.path.exists(local_path):
                if progress_callback:
                    progress_callback("Cleaning up existing directory...")
                self._force_remove_directory(local_path)
            
            if progress_callback:
                progress_callback("Starting clone operation...")
            
            # Ensure URL is properly formatted
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if not url.endswith('.git'):
                url += '.git'
            
            # Clone the repository
            if progress_callback:
                progress_callback("Cloning repository...")
            
            repo = Repo.clone_from(url, local_path, depth=1)  # Shallow clone for speed
            
            if progress_callback:
                progress_callback("Clone completed successfully!")
            
            logger.info(f"Successfully cloned {repo_name} to {local_path}")
            return True, local_path, None
            
        except GitCommandError as e:
            # Clean up any partial clone on error
            if os.path.exists(local_path):
                self._force_remove_directory(local_path)
            
            error_msg = f"Git error: {str(e)}"
            if "Repository not found" in str(e):
                error_msg = "Repository not found. Please check if the repository exists and is public."
            elif "Authentication" in str(e):
                error_msg = "Authentication failed. Please check if the repository is private."
            elif "Access is denied" in str(e) or "WinError 5" in str(e):
                error_msg = "Access denied error. Try running as administrator or close any programs that might be accessing the repository files."
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            # Clean up any partial clone on error
            if os.path.exists(local_path):
                self._force_remove_directory(local_path)
            
            error_msg = f"Unexpected error during cloning: {str(e)}"
            if "Access is denied" in str(e) or "WinError 5" in str(e):
                error_msg = "File access error. Please close any programs that might be using the repository files and try again."
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_repo_info(self, local_path):
        """
        Extract basic information about the cloned repository.
        
        Args:
            local_path (str): Path to the cloned repository
            
        Returns:
            dict: Repository information
        """
        try:
            repo = Repo(local_path)
            
            # Get remote URL
            remote_url = None
            if repo.remotes:
                remote_url = repo.remotes.origin.url
            
            # Get latest commit info
            latest_commit = repo.head.commit
            
            # Count files and get basic stats
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(local_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                    
                total_files += len(files)
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        continue
            
            return {
                'remote_url': remote_url,
                'latest_commit': {
                    'hash': latest_commit.hexsha[:8],
                    'message': latest_commit.message.strip(),
                    'author': str(latest_commit.author),
                    'date': latest_commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
                },
                'stats': {
                    'total_files': total_files,
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting repo info: {str(e)}")
            return {}
    
    def _force_remove_directory(self, directory_path):
        """
        Force remove a directory with Windows-specific error handling.
        
        Args:
            directory_path (str): Path to directory to remove
        """
        def handle_remove_readonly(func, path, exc):
            """Error handler for removing read-only files on Windows."""
            try:
                # Make the file writable and try again
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception as e:
                logger.warning(f"Could not remove {path}: {str(e)}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not os.path.exists(directory_path):
                    return  # Already removed
                
                # Method 1: Try standard removal first
                if attempt == 0:
                    shutil.rmtree(directory_path, onerror=handle_remove_readonly)
                
                # Method 2: Make all files writable first
                elif attempt == 1:
                    logger.info(f"Attempt {attempt + 1}: Making files writable before removal...")
                    for root, dirs, files in os.walk(directory_path):
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            try:
                                os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                            except:
                                pass
                        for file_name in files:
                            file_path = os.path.join(root, file_name)
                            try:
                                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                            except:
                                pass
                    shutil.rmtree(directory_path, onerror=handle_remove_readonly)
                
                # Method 3: Use system command as last resort
                else:
                    logger.info(f"Attempt {attempt + 1}: Using system command for removal...")
                    if os.name == 'nt':  # Windows
                        # Use rmdir /s /q for Windows
                        subprocess.run(['rmdir', '/s', '/q', directory_path], 
                                     shell=True, capture_output=True)
                    else:
                        # Use rm -rf for Unix-like systems
                        subprocess.run(['rm', '-rf', directory_path], 
                                     capture_output=True)
                
                # Verify removal
                if not os.path.exists(directory_path):
                    logger.info(f"Successfully removed directory: {directory_path}")
                    return
                else:
                    raise Exception("Directory still exists after removal attempt")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} to remove directory failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info("Waiting before retry...")
                    time.sleep(2)  # Wait before retry
                else:
                    logger.error(f"Failed to remove directory after {max_retries} attempts: {directory_path}")
                    # Don't raise exception - just log the error and continue
                    logger.warning("Continuing with analysis despite cleanup failure...")
    
    def cleanup_repo(self, local_path):
        """
        Clean up a cloned repository with improved error handling.
        
        Args:
            local_path (str): Path to the repository to clean up
        """
        try:
            if os.path.exists(local_path):
                logger.info(f"Cleaning up repository at {local_path}")
                self._force_remove_directory(local_path)
        except Exception as e:
            logger.error(f"Error cleaning up repository: {str(e)}")
            # Don't fail the entire operation due to cleanup issues
            logger.warning("Cleanup failed but continuing...")
    
    def cleanup_all_repos(self):
        """Clean up all cloned repositories with improved error handling."""
        try:
            if os.path.exists(self.base_dir):
                logger.info(f"Cleaning up all repositories in {self.base_dir}")
                self._force_remove_directory(self.base_dir)
                os.makedirs(self.base_dir, exist_ok=True)
                logger.info("Cleaned up all repositories")
        except Exception as e:
            logger.error(f"Error cleaning up all repositories: {str(e)}")
            # Ensure base directory exists even if cleanup failed
            try:
                os.makedirs(self.base_dir, exist_ok=True)
            except:
                pass
