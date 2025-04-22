import os
import subprocess
import logging
import sys
import platform
import shutil
import time

logger = logging.getLogger(__name__)

# Define constants
ADK_SAMPLES_REPO = "https://github.com/google/adk-samples.git"
ADK_SAMPLES_PATH = os.path.join(os.getcwd(), "adk-samples")

def setup_adk_environment():
    """
    Set up the ADK environment by cloning the samples repository
    and installing required dependencies.
    
    Returns:
        dict: A dictionary with 'success' and 'message' keys indicating the result
    """
    result = {
        'success': False,
        'message': ''
    }
    
    try:
        # Check if Python version is compatible (3.9+)
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
            result['message'] = f"Python 3.9+ is required. You have Python {python_version.major}.{python_version.minor}.{python_version.micro}"
            return result
        
        # Check if git is installed
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            result['message'] = "Git is not installed or not in the PATH. Please install Git."
            return result
        
        # Check if ADK samples directory already exists
        if os.path.exists(ADK_SAMPLES_PATH):
            logger.info(f"ADK samples directory already exists at {ADK_SAMPLES_PATH}")
            # Pull latest changes instead of cloning
            try:
                subprocess.run(["git", "-C", ADK_SAMPLES_PATH, "pull"], check=True, capture_output=True)
                logger.info("Successfully pulled latest changes from ADK samples repository")
            except subprocess.SubprocessError as e:
                logger.error(f"Error pulling latest changes: {e}")
                result['message'] = f"Error updating ADK samples: {e}"
                return result
        else:
            # Clone the ADK samples repository
            logger.info(f"Cloning ADK samples repository to {ADK_SAMPLES_PATH}")
            try:
                subprocess.run(["git", "clone", ADK_SAMPLES_REPO, ADK_SAMPLES_PATH], check=True, capture_output=True)
                logger.info("Successfully cloned ADK samples repository")
            except subprocess.SubprocessError as e:
                logger.error(f"Error cloning repository: {e}")
                result['message'] = f"Error cloning ADK samples repository: {e}"
                return result
                
        # Install ADK and other dependencies
        try:
            logger.info("Installing ADK and dependencies")
            subprocess.run([sys.executable, "-m", "pip", "install", "google-adk"], check=True, capture_output=True)
            
            # Install additional dependencies for samples
            subprocess.run([sys.executable, "-m", "pip", "install", "requests", "matplotlib", "pandas", "numpy", "llama-index"], 
                         check=True, capture_output=True)
            
            logger.info("Successfully installed ADK and dependencies")
        except subprocess.SubprocessError as e:
            logger.error(f"Error installing dependencies: {e}")
            result['message'] = f"Error installing dependencies: {e}"
            return result
        
        result['success'] = True
        result['message'] = "ADK environment set up successfully"
        return result
        
    except Exception as e:
        logger.exception("Unexpected error during ADK setup")
        result['message'] = f"Unexpected error: {str(e)}"
        return result

def check_dependencies():
    """
    Check if all required dependencies for the ADK are installed.
    
    Returns:
        dict: A dictionary with information about installed dependencies
    """
    required_dependencies = [
        {"name": "Python 3.9+", "package": None},
        {"name": "google-adk", "package": "google-adk"},
        {"name": "Git", "package": None},
        {"name": "requests", "package": "requests"},
        {"name": "matplotlib", "package": "matplotlib"},
        {"name": "pandas", "package": "pandas"},
        {"name": "numpy", "package": "numpy"},
        {"name": "llama-index", "package": "llama_index"}
    ]
    
    result = {
        "success": True,
        "dependencies": [],
        "message": ""
    }
    
    for dep in required_dependencies:
        installed = False
        version = "Unknown"
        
        if dep["name"] == "Python 3.9+":
            python_version = sys.version_info
            installed = python_version.major >= 3 and python_version.minor >= 9
            version = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        
        elif dep["name"] == "Git":
            try:
                git_process = subprocess.run(["git", "--version"], capture_output=True, text=True, check=False)
                installed = git_process.returncode == 0
                if installed:
                    version = git_process.stdout.strip()
            except FileNotFoundError:
                installed = False
        
        elif dep["package"]:
            try:
                import importlib
                module = importlib.import_module(dep["package"].replace("-", "_"))
                installed = True
                if hasattr(module, "__version__"):
                    version = module.__version__
                elif hasattr(module, "version"):
                    version = module.version
            except ImportError:
                installed = False
        
        result["dependencies"].append({
            "name": dep["name"],
            "installed": installed,
            "version": version if installed else "Not installed"
        })
        
        if not installed:
            result["success"] = False
    
    if not result["success"]:
        result["message"] = "Some required dependencies are missing. Please install them to use ADK fully."
    else:
        result["message"] = "All required dependencies are installed."
    
    return result
