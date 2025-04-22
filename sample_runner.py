import os
import subprocess
import logging
import sys
import glob
import json

logger = logging.getLogger(__name__)

class SampleRunner:
    """Class for managing and running ADK samples."""
    
    def __init__(self, samples_path):
        """
        Initialize the SampleRunner with the path to the ADK samples.
        
        Args:
            samples_path (str): Path to the ADK samples directory
        """
        self.samples_path = samples_path
        
        # Verify samples path exists
        if not os.path.exists(samples_path):
            raise FileNotFoundError(f"Samples directory not found at {samples_path}")
            
        logger.info(f"Initialized SampleRunner with samples path: {samples_path}")
    
    def get_available_samples(self):
        """
        Get a list of available ADK samples.
        
        Returns:
            list: List of dictionaries with sample information
        """
        samples = []
        
        # Look for Python files in the samples directory and subdirectories
        for root, dirs, files in os.walk(self.samples_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.samples_path)
                    
                    # Skip if path contains __pycache__ or other special directories
                    if "__pycache__" in relative_path or ".git" in relative_path:
                        continue
                    
                    # Read first few lines of the file to get a description
                    description = self._extract_description(file_path)
                    
                    # Get sample name (filename without extension)
                    name = os.path.splitext(file)[0]
                    
                    # Add to samples list
                    samples.append({
                        "name": name,
                        "path": file_path,
                        "relative_path": relative_path,
                        "description": description
                    })
        
        return samples
    
    def run_sample(self, sample_path):
        """
        Run an ADK sample script.
        
        Args:
            sample_path (str): Path to the sample Python file
            
        Returns:
            dict: Dictionary with execution results
        """
        if not os.path.exists(sample_path):
            raise FileNotFoundError(f"Sample not found at {sample_path}")
        
        # Get sample name (filename without extension)
        sample_name = os.path.splitext(os.path.basename(sample_path))[0]
        
        # Prepare result dictionary
        result = {
            "sample_name": sample_name,
            "sample_path": sample_path,
            "success": False,
            "output": "",
            "errors": "",
            "source_code": self._get_source_code(sample_path)
        }
        
        try:
            # Run the sample script
            logger.info(f"Running sample: {sample_path}")
            
            # Change to the directory of the sample to ensure imports work correctly
            original_dir = os.getcwd()
            sample_dir = os.path.dirname(sample_path)
            os.chdir(sample_dir)
            
            # Handle samples with relative imports
            if 'RAG/rag/agent.py' in sample_path or 'agents/RAG/rag/agent.py' in sample_path or 'keyword_finding/agent.py' in sample_path or 'sub_agents' in sample_path:
                # Create a temporary file that imports the module correctly
                temp_file = os.path.join(sample_dir, 'run_sample_temp.py')
                with open(temp_file, 'w') as f:
                    f.write('''
import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
# Now import the agent module (avoid relative imports)
try:
    from google.adk import Agent, Tool
    from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
    print("Successfully imported ADK modules")
    from prompts import return_instructions_root
    print("Successfully imported prompt module")
except Exception as e:
    print(f"Import error: {e}")

print("Module imports completed")
''')
                process = subprocess.run(
                    [sys.executable, 'run_sample_temp.py'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            # Special case for deployment samples
            elif 'RAG/deployment/deploy.py' in sample_path or 'agents/RAG/deployment/deploy.py' in sample_path:
                # Create a temporary file that imports the module correctly
                temp_file = os.path.join(sample_dir, 'run_deploy_temp.py')
                with open(temp_file, 'w') as f:
                    f.write('''
import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("Python path modified for imports")
                        
try:
    # Import directly instead of using relative imports
    import google.adk as adk
    print("Successfully imported ADK")
except Exception as e:
    print(f"Import error: {e}")

print("Module setup completed")
''')
                process = subprocess.run(
                    [sys.executable, 'run_deploy_temp.py'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                # Regular run method for other samples
                process = subprocess.run(
                    [sys.executable, os.path.basename(sample_path)], 
                    capture_output=True, 
                    text=True,
                    timeout=60  # 60 second timeout to prevent hanging
                )
            
            # Restore original directory
            os.chdir(original_dir)
            
            # Capture output and errors
            result["output"] = process.stdout
            result["errors"] = process.stderr
            
            # Check if execution was successful
            result["success"] = process.returncode == 0
            
            if result["success"]:
                logger.info(f"Successfully ran sample: {sample_name}")
            else:
                logger.error(f"Error running sample {sample_name}: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            result["success"] = False
            result["errors"] = "Execution timed out after 60 seconds."
            logger.error(f"Timeout running sample {sample_name}")
            
        except Exception as e:
            result["success"] = False
            result["errors"] = str(e)
            logger.exception(f"Error running sample {sample_name}")
        
        return result
    
    def _extract_description(self, file_path):
        """
        Extract a description from the sample file comments.
        
        Args:
            file_path (str): Path to the sample file
            
        Returns:
            str: Description of the sample
        """
        description = "No description available"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:20]  # Read first 20 lines
                
                # Look for docstring or commented description
                docstring_started = False
                docstring_lines = []
                
                for line in lines:
                    line = line.strip()
                    
                    # Check for docstrings
                    if line.startswith('"""') or line.startswith("'''"):
                        if docstring_started:
                            docstring_started = False
                            break
                        else:
                            docstring_started = True
                            # Extract content after the opening quotes
                            content = line[3:].strip()
                            if content:
                                docstring_lines.append(content)
                    elif docstring_started:
                        if line.endswith('"""') or line.endswith("'''"):
                            docstring_started = False
                            content = line[:-3].strip()
                            if content:
                                docstring_lines.append(content)
                        else:
                            docstring_lines.append(line)
                    # Check for commented description
                    elif line.startswith('#'):
                        content = line[1:].strip()
                        if content:
                            docstring_lines.append(content)
                
                if docstring_lines:
                    description = ' '.join(docstring_lines)
                    
                    # Limit description length
                    if len(description) > 100:
                        description = description[:97] + "..."
        except Exception as e:
            logger.error(f"Error extracting description from {file_path}: {e}")
        
        return description
    
    def _get_source_code(self, file_path):
        """
        Get the source code of a sample file.
        
        Args:
            file_path (str): Path to the sample file
            
        Returns:
            str: Source code of the sample
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading source code from {file_path}: {e}")
            return "Error loading source code"
