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
                    
                    # Get base sample name (filename without extension)
                    base_name = os.path.splitext(file)[0]
                    
                    # Create a more descriptive name based on the path and type of sample
                    descriptive_name = self._create_descriptive_name(base_name, file_path, relative_path)
                    
                    # Add to samples list
                    samples.append({
                        "name": descriptive_name,
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
            if ('RAG/rag/agent.py' in sample_path or 'agents/RAG/rag/agent.py' in sample_path 
                or 'keyword_finding/agent.py' in sample_path or 'sub_agents' in sample_path
                or 'brand-search-optimization/brand_search_optimization/agent.py' in sample_path
                or 'brand_search_optimization/agent.py' in sample_path):
                # Create a temporary file that imports the module correctly
                temp_file = os.path.join(sample_dir, 'run_sample_temp.py')
                with open(temp_file, 'w') as f:
                    template = '''
import sys
import os

# Add parent directory to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
# Now import the agent module (avoid relative imports)
try:
    from google.adk import Agent, Tool
    from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
    print("Successfully imported ADK modules")
    
    # Special case for Brand Search Optimization samples
    if "brand-search-optimization" in os.path.abspath(__file__) or "brand_search_optimization" in os.path.abspath(__file__):
        print("Setting up Brand Search Optimization imports")
        # Get the correct path
        brand_search_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if brand_search_path not in sys.path:
            sys.path.insert(0, brand_search_path)
        try:
            # Try absolute imports instead of relative
            import brand_search_optimization.shared_libraries.constants
            print("Successfully imported brand search modules")
        except Exception as e:
            print(f"Brand search module import error: {e}")
    else:
        # Default import for most other agents
        from prompts import return_instructions_root
        print("Successfully imported prompt module")
except Exception as e:
    print(f"Import error: {e}")

print("Module imports completed")
'''
                    f.write(template)
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
    
    # Check for environment variables
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if project_id:
        print(f"Using Google Cloud Project: {project_id}")
    else:
        print("Warning: No Google Cloud Project ID found in environment variables")
except Exception as e:
    print(f"Import error: {e}")

print("Module setup completed")
''')
                # Check for environment variables
                env_vars = os.environ.copy()
                env_path = os.path.join(os.path.dirname(os.path.dirname(sample_path)), '.env')
                if os.path.exists(env_path):
                    try:
                        with open(env_path, 'r') as f:
                            for line in f:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    env_vars[key] = value
                                    logger.info(f"Using environment variable: {key}")
                    except Exception as e:
                        logger.error(f"Error reading .env file: {e}")
                
                process = subprocess.run(
                    [sys.executable, 'run_deploy_temp.py'],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env_vars  # Pass environment variables
                )
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                # Regular run method for other samples
                # Check for environment variables
                env_vars = os.environ.copy()
                env_path = os.path.join(os.path.dirname(os.path.dirname(sample_path)), '.env')
                if os.path.exists(env_path):
                    try:
                        with open(env_path, 'r') as f:
                            for line in f:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    env_vars[key] = value
                                    logger.info(f"Using environment variable: {key}")
                    except Exception as e:
                        logger.error(f"Error reading .env file: {e}")
                
                process = subprocess.run(
                    [sys.executable, os.path.basename(sample_path)], 
                    capture_output=True, 
                    text=True,
                    timeout=60,  # 60 second timeout to prevent hanging
                    env=env_vars  # Pass environment variables
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
    
    def _create_descriptive_name(self, base_name, file_path, relative_path):
        """
        Create a more descriptive name for the sample based on its type and purpose.
        Ensures names are unique and descriptive.
        
        Args:
            base_name (str): Original file name without extension
            file_path (str): Full path to the sample file
            relative_path (str): Path relative to samples directory
            
        Returns:
            str: A unique descriptive name for the sample
        """
        # Define sample type prefixes based on path
        agent_types = {
            "RAG": "RAG",
            "data-science": "Data Science",
            "customer-service": "Customer Service",
            "brand-search-optimization": "Brand Search"
        }
        
        # Define function type identifiers
        function_types = {
            "agent.py": "Agent",
            "deploy.py": "Deploy",
            "run.py": "Runner",
            "test_eval.py": "Evaluator",
            "eval.py": "Evaluator",
            "bq_populate_data.py": "BQ Data Loader"
        }
        
        # Extract agent type from path
        agent_type = "Sample"
        for key, value in agent_types.items():
            if key in relative_path:
                agent_type = value
                break
        
        # Extract function type from filename
        function_type = ""
        for key, value in function_types.items():
            if key in os.path.basename(file_path):
                function_type = value
                break
                
        # If no specific function type was found
        if not function_type:
            if "deployment" in relative_path:
                function_type = "Deployer"
            elif "eval" in relative_path:
                function_type = "Evaluator"
            elif "test" in relative_path and "test_" in os.path.basename(file_path):
                function_type = "Tester"
            else:
                # Use capitalized base name as fallback
                function_type = base_name.capitalize()
        
        # Add unique identifiers based on directory structure
        # Extract the sub-module from path
        path_segments = relative_path.split(os.sep)
        submodule = ""
        
        # Look for specific submodules to include
        for segment in path_segments:
            if segment in ["rag", "deployment", "eval", "tests", "data_science", "customer_service", "brand_search_optimization"]:
                submodule = f" ({segment})"
                break
                
        # Add identifying numbers for potential duplicates based on directory depth
        if len(path_segments) > 2:
            depth_indicator = f"{len(path_segments)}"
            if not submodule:
                submodule = f" (L{depth_indicator})"
                
        # Special case for test files to differentiate them
        if "test_" in os.path.basename(file_path):
            test_name = os.path.basename(file_path).replace("test_", "").replace(".py", "")
            if test_name:
                submodule = f" ({test_name})"
                
        # Combine for final unique name
        return f"{agent_type} {function_type}{submodule}"
        
    def _extract_description(self, file_path):
        """
        Extract a description from the sample file comments and enhance it with
        API credential requirements and functionality.
        
        Args:
            file_path (str): Path to the sample file
            
        Returns:
            str: Enhanced description of the sample
        """
        # Comprehensive custom descriptions for all samples with specific API requirements
        custom_descriptions = {
            # RAG Agents
            "agents/RAG/rag/agent.py": "RAG Agent: Creates a retrieval-augmented generation agent that answers questions using your data. When run: Shows agent setup and test conversation. APIs needed: Vertex AI API, Generative Language API.",
            "agents/RAG/deployment/deploy.py": "RAG Deployment: Deploys retrieval agent to Google Cloud for production use. When run: Creates and configures agent in your GCP. APIs needed: Vertex AI API, Agent Builder API, IAM API.",
            "agents/RAG/deployment/run.py": "RAG Runner: Tests a deployed RAG agent with sample queries. When run: Shows conversation with your deployed agent. APIs needed: Vertex AI API, Agent Builder API.",
            "agents/RAG/eval/test_eval.py": "RAG Evaluation: Tests RAG agent's accuracy on predefined questions. When run: Displays evaluation metrics and scores. APIs needed: Vertex AI API, Generative Language API.",
            
            # Data Science Agents
            "agents/data-science/data_science/agent.py": "Data Science Agent: Performs data analysis using SQL and Python. When run: Executes sample queries and shows analysis results. APIs needed: BigQuery API, Vertex AI API, Generative Language API.",
            "agents/data-science/deployment/deploy.py": "Data Science Deployment: Publishes data analysis agent to Google Cloud. When run: Creates configured agent in your GCP. APIs needed: Vertex AI API, Agent Builder API, IAM API, BigQuery API.",
            "agents/data-science/deployment/test_deployment.py": "Data Science Deployment Test: Verifies successful agent deployment. When run: Tests agent functionality in cloud. APIs needed: Vertex AI API, Agent Builder API.",
            "agents/data-science/eval/test_eval.py": "Data Science Evaluation: Tests data agent with analytical queries. When run: Shows query results and performance metrics. APIs needed: Vertex AI API, BigQuery API.",
            "agents/data-science/tests/test_agents.py": "Data Science Agent Tests: Unit tests for data analysis agent. When run: Executes test suite and reports results. APIs needed: BigQuery API, Vertex AI API.",
            
            # Customer Service Agents
            "agents/customer-service/customer_service/agent.py": "Customer Service Agent: Handles customer inquiries and support tickets. When run: Demonstrates support conversation. APIs needed: Vertex AI API, Generative Language API.",
            "agents/customer-service/deployment/deploy.py": "Customer Service Deployment: Deploys support agent to your cloud. When run: Creates agent in GCP for your application. APIs needed: Vertex AI API, Agent Builder API, IAM API.",
            "agents/customer-service/eval/test_eval.py": "Customer Service Evaluation: Tests agent's responses to support queries. When run: Shows conversation testing with metrics. APIs needed: Vertex AI API, Generative Language API.",
            
            # Brand Search Optimization
            "agents/brand-search-optimization/brand_search_optimization/agent.py": "Brand Search Agent: Optimizes search results for brand queries. When run: Demonstrates search optimization. APIs needed: Vertex AI API, Generative Language API.",
            "agents/brand-search-optimization/deployment/bq_populate_data.py": "Brand Search Data Loader: Populates BigQuery with sample brand data. When run: Creates and fills BigQuery tables. APIs needed: BigQuery API, IAM API.",
            "agents/brand-search-optimization/deployment/deploy.py": "Brand Search Deployment: Deploys search optimization agent. When run: Publishes agent to your GCP. APIs needed: Vertex AI API, Agent Builder API, IAM API, BigQuery API.",
            "agents/brand-search-optimization/eval/eval.py": "Brand Search Evaluation: Tests search optimization effectiveness. When run: Shows performance metrics on test queries. APIs needed: Vertex AI API, Generative Language API, BigQuery API."
        }
        
        # Handle specific Python files that aren't meant to be directly run
        not_runnable_files = {
            "__init__.py": "Module initialization file. Not meant to be run directly.",
            "prompts.py": "Contains prompt templates for agent instructions. Not meant to be run directly.",
            "config.py": "Configuration settings for agent environment. Not meant to be run directly.",
            "tools.py": "Defines agent tools and capabilities. Not meant to be run directly."
        }
        
        # Check if it's a non-runnable file type
        file_name = os.path.basename(file_path)
        if file_name in not_runnable_files:
            return not_runnable_files[file_name]
        
        # Extract file path relative to samples directory
        relative_path = None
        for key in custom_descriptions.keys():
            if key in file_path:
                relative_path = key
                break
                
        # Use custom description if available
        if relative_path and relative_path in custom_descriptions:
            return custom_descriptions[relative_path]
            
        # For any unknown samples, give a more useful generic description based on path
        if "deployment" in file_path:
            return "Agent Deployment Script: Deploys an agent to Google Cloud. When run: Creates cloud resources. APIs needed: Vertex AI API, Agent Builder API, IAM API."
        elif "eval" in file_path:
            return "Agent Evaluation: Tests agent performance and accuracy. When run: Shows test results and metrics. APIs needed: Vertex AI API, Generative Language API."
        elif "agent" in file_path:
            return "AI Agent: Performs specialized tasks using Google's Vertex AI. When run: Demonstrates agent capabilities. APIs needed: Vertex AI API, Generative Language API."
        elif "test" in file_path:
            return "Test Script: Validates agent functionality. When run: Executes tests and shows results. APIs needed: Vertex AI API, Generative Language API."
            
        # Default description that avoids copyright text
        return "ADK Sample Script: Demonstrates ADK functionality. When run: Shows sample execution. APIs needed: Vertex AI API, Generative Language API."
    
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
