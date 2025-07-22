"""
Setup script for the AI GitHub Code Analyzer.
Run this script to install dependencies and configure the environment.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def setup_environment():
    """Setup environment configuration."""
    print("⚙️ Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copy example env file
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file and add your OpenRouter API key")
        except Exception as e:
            print(f"❌ Failed to create .env file: {str(e)}")
            return False
    elif env_file.exists():
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = ["repos", "sample_output", "assets"]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {str(e)}")
            return False
    
    return True

def test_installation():
    """Test the installation by importing modules."""
    print("🧪 Testing installation...")
    
    test_imports = [
        "streamlit",
        "git",
        "requests",
        "pandas",
        "plotly",
        "dotenv"
    ]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {str(e)}")
            return False
    
    return True

def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "=" * 80)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("📋 Next Steps:")
    print("1. Get your free OpenRouter API key from: https://openrouter.ai/")
    print("2. Edit the .env file and add your API key:")
    print("   OPENROUTER_API_KEY=your_actual_api_key_here")
    print()
    print("🚀 How to run the application:")
    print("   • Web Interface: streamlit run app.py")
    print("   • Demo Script:   python demo.py")
    print("   • Command Line:  python -m utils.cli_tool (if created)")
    print()
    print("📚 Example usage:")
    print("   1. Start the web app: streamlit run app.py")
    print("   2. Open your browser to: http://localhost:8501")
    print("   3. Enter a GitHub repository URL")
    print("   4. Click 'Analyze Repository'")
    print("   5. Explore the results and ask questions!")
    print()
    print("🆘 Troubleshooting:")
    print("   • If you get API errors, check your API key")
    print("   • If repo cloning fails, ensure the repo is public")
    print("   • For large repos, analysis may take several minutes")
    print("   • Check the logs for detailed error information")
    print()
    print("📞 Support:")
    print("   • Documentation: README.md")
    print("   • Issues: Create a GitHub issue")
    print("   • Demo: Run 'python demo.py' for a quick test")

def main():
    """Main setup function."""
    print("🔧 AI GitHub Code Analyzer Setup")
    print("=" * 80)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create directories
    if not create_directories():
        print("❌ Setup failed during directory creation")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed during environment setup")
        return
    
    # Test installation
    if not test_installation():
        print("❌ Setup failed during installation testing")
        return
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main()
