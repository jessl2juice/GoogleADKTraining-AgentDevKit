import os
import logging
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import subprocess
import json
import sys
import adk_setup
from sample_runner import SampleRunner
from deploy_agent import DeploymentManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "adk_training_secret_key")

# Global variables
ADK_SAMPLES_PATH = os.path.join(os.getcwd(), "adk-samples")
sample_runner = None
deployment_manager = DeploymentManager()

@app.route('/')
def index():
    """Display the main page of the ADK Training environment."""
    # Check if ADK samples are already set up
    is_setup = os.path.exists(ADK_SAMPLES_PATH)
    
    # Check if Google Cloud credentials are set up
    has_credentials = False
    env_path = os.path.join(ADK_SAMPLES_PATH, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                if 'GOOGLE_CLOUD_PROJECT' in content:
                    has_credentials = True
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
    
    # List sample directories if already set up
    samples = []
    if is_setup:
        try:
            samples = sample_runner.get_available_samples()
        except Exception as e:
            logger.error(f"Error getting samples: {e}")
            flash(f"Error listing samples: {e}", "danger")
    
    return render_template('index.html', is_setup=is_setup, samples=samples, has_credentials=has_credentials)

@app.route('/setup', methods=['POST'])
def setup():
    """Set up the ADK environment by cloning the samples repository."""
    try:
        result = adk_setup.setup_adk_environment()
        if result['success']:
            flash("ADK environment set up successfully!", "success")
            global sample_runner
            sample_runner = SampleRunner(ADK_SAMPLES_PATH)
        else:
            flash(f"Error setting up ADK environment: {result['message']}", "danger")
    except Exception as e:
        logger.exception("Error during setup")
        flash(f"An unexpected error occurred: {str(e)}", "danger")
    
    return redirect(url_for('index'))

@app.route('/run_sample', methods=['POST'])
def run_sample():
    """Run a selected ADK sample."""
    sample_path = request.form.get('sample_path')
    
    if not sample_path:
        flash("No sample selected", "warning")
        return redirect(url_for('index'))
    
    # Check if the file is a non-runnable type
    non_runnable_files = ['__init__.py', 'prompts.py', 'config.py', 'tools.py']
    file_name = os.path.basename(sample_path)
    
    if file_name in non_runnable_files:
        flash(f"{file_name} is not meant to be run directly. Please choose another sample.", "warning")
        return redirect(url_for('index'))
    
    try:
        result = sample_runner.run_sample(sample_path)
        session['last_sample_result'] = result
        return redirect(url_for('sample_result'))
    except Exception as e:
        logger.exception("Error running sample")
        flash(f"Error running sample: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/sample_result')
def sample_result():
    """Show the result of the latest sample run."""
    result = session.get('last_sample_result', {})
    return render_template('sample_runner.html', result=result)

@app.route('/documentation')
def documentation():
    """Display ADK documentation and resources."""
    return render_template('documentation.html')

@app.route('/check_dependencies')
def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        result = adk_setup.check_dependencies()
        return jsonify(result)
    except Exception as e:
        logger.exception("Error checking dependencies")
        return jsonify({'success': False, 'message': str(e)})
        
@app.route('/cloud_credentials', methods=['GET', 'POST'])
def cloud_credentials():
    """Manage Google Cloud credentials for ADK samples."""
    if request.method == 'POST':
        try:
            # Get form data
            project_id = request.form.get('project_id')
            location = request.form.get('location', 'us-central1')
            api_key = request.form.get('api_key', '')
            
            # Validate inputs
            if not project_id:
                flash("Project ID is required", "danger")
                return redirect(url_for('cloud_credentials'))
            
            # Create .env file in the adk-samples directory
            env_path = os.path.join(ADK_SAMPLES_PATH, '.env')
            with open(env_path, 'w') as f:
                f.write(f"GOOGLE_CLOUD_PROJECT={project_id}\n")
                f.write(f"GOOGLE_CLOUD_LOCATION={location}\n")
                if api_key:
                    f.write(f"GOOGLE_API_KEY={api_key}\n")
                f.write("GOOGLE_GENAI_USE_VERTEXAI=1\n")
            
            # Set environment variables for the current process
            os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
            os.environ['GOOGLE_CLOUD_LOCATION'] = location
            if api_key:
                os.environ['GOOGLE_API_KEY'] = api_key
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '1'
            
            flash("Google Cloud credentials saved successfully!", "success")
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.exception("Error saving credentials")
            flash(f"Error saving credentials: {str(e)}", "danger")
            return redirect(url_for('cloud_credentials'))
    
    # GET request - show the form
    # Check if credentials already exist
    env_path = os.path.join(ADK_SAMPLES_PATH, '.env')
    credentials = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key] = value
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    
    return render_template('cloud_credentials.html', credentials=credentials)

@app.route('/deploy')
def deploy_agent_view():
    """Show the agent deployment page."""
    # Get all deployed agents
    deployed_agents = deployment_manager.get_all_agents()
    return render_template('deploy/index.html', deployed_agents=deployed_agents)

@app.route('/deploy/agent', methods=['POST'])
def deploy_agent():
    """Deploy an agent to production."""
    try:
        # Get form data
        agent_type = request.form.get('agent_type')
        agent_name = request.form.get('agent_name')
        agent_description = request.form.get('agent_description', '')
        
        # Validate basic inputs
        if not agent_type or not agent_name:
            flash("Agent type and name are required", "danger")
            return redirect(url_for('deploy_agent_view'))
        
        # Build agent configuration
        config = {
            'enable_logging': 'enable_logging' in request.form,
            'enable_webhooks': 'enable_webhooks' in request.form,
            'public_access': 'public_access' in request.form,
        }
        
        # Add webhook URL if enabled
        if config['enable_webhooks']:
            config['webhook_url'] = request.form.get('webhook_url', '')
        
        # Add type-specific configurations
        if agent_type == 'rag':
            config['data_source'] = request.form.get('data_source', '')
            config['data_location'] = request.form.get('data_location', '')
        elif agent_type == 'data_science':
            config['bigquery_dataset'] = request.form.get('bigquery_dataset', '')
        elif agent_type == 'customer_service':
            config['knowledge_base'] = request.form.get('knowledge_base', '')
        elif agent_type == 'brand_search':
            config['brand_data'] = request.form.get('brand_data', '')
        
        # Deploy the agent
        agent = deployment_manager.deploy_agent(
            name=agent_name,
            agent_type=agent_type,
            description=agent_description,
            config=config
        )
        
        # Show success page
        return render_template('deploy/success.html', agent=agent)
        
    except Exception as e:
        logger.exception("Error deploying agent")
        flash(f"Error deploying agent: {str(e)}", "danger")
        return redirect(url_for('deploy_agent_view'))

@app.route('/deploy/agent/<agent_id>')
def view_agent(agent_id):
    """View a deployed agent's details."""
    agent = deployment_manager.get_agent(agent_id)
    if not agent:
        flash("Agent not found", "danger")
        return redirect(url_for('deploy_agent_view'))
    
    return render_template('deploy/view.html', agent=agent)

@app.route('/deploy/agent/<agent_id>/delete')
def delete_agent(agent_id):
    """Delete a deployed agent."""
    try:
        success = deployment_manager.delete_agent(agent_id)
        if success:
            flash("Agent deleted successfully", "success")
        else:
            flash("Agent not found", "danger")
    except Exception as e:
        logger.exception("Error deleting agent")
        flash(f"Error deleting agent: {str(e)}", "danger")
    
    return redirect(url_for('deploy_agent_view'))

# Initialize sample runner if ADK samples are already available
if os.path.exists(ADK_SAMPLES_PATH):
    try:
        sample_runner = SampleRunner(ADK_SAMPLES_PATH)
    except Exception as e:
        logger.error(f"Error initializing sample runner: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
