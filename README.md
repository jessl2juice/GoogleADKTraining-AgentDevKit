# Jess's Google ADK Gym

A comprehensive environment for learning, testing, and deploying agents using the Google Agent Development Kit (ADK).

![Google ADK Training Environment](static/images/adk-logo.png)

## Overview

This application provides a user-friendly interface for working with Google's Agent Development Kit. It simplifies the process of exploring sample agents, understanding ADK features, and deploying agents to production environments with Google Cloud.

## Features

### Sample Management
- **Automatic Sample Discovery**: Automatically finds and categorizes all available ADK samples
- **Descriptive Naming**: Provides clear, descriptive names for each sample based on its functionality
- **Detailed Descriptions**: Includes information about what each sample does, expected outcomes, and required API credentials
- **Search Functionality**: Filter samples by name or description to find specific examples

### Execution Environment
- **One-Click Sample Runs**: Execute any sample with a single click
- **Detailed Output**: View complete execution results, including stdout, stderr, and exit codes
- **Import Testing**: Special handling for import-only modules and shared libraries
- **Path Management**: Automatically handles Python import paths for proper execution

### Google Cloud Integration
- **Credential Management**: Configure and store Google Cloud credentials for use with ADK samples
- **API Status Indicators**: Visual indicators for configured APIs and credentials status
- **Environment Variable Passing**: Automatically passes needed environment variables to sample executions

### Agent Deployment
- **Production Deployment**: Deploy tested agents to Google Cloud for production use
- **Agent Configuration**: Configure agent-specific settings like data sources, knowledge bases, and webhooks
- **Deployment Management**: View, monitor, and manage all deployed agents in one place
- **Type-Specific Options**: Specialized configuration options for different agent types (RAG, Data Science, etc.)

### Learning Resources
- **Documentation Links**: Quick access to official ADK documentation and resources
- **Getting Started Guide**: Step-by-step instructions for beginners
- **Usage Tips**: Helpful suggestions for effective use of the environment

## Getting Started

### Prerequisites
- Python 3.11+
- Flask and related dependencies
- Google Cloud account (for full functionality)
- Google API credentials (for deploying and testing agents)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/adk-training-environment.git
cd adk-training-environment
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables (optional):
```bash
export SESSION_SECRET="your_session_secret_here"
```

4. Run the application:
```bash
python main.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

### Initial Setup

1. **Download ADK Samples**: Click the "Set Up ADK Environment" button on the home page
2. **Configure Google Cloud Credentials**: Click "Configure Google Cloud Credentials" and enter your project details
3. **Explore Samples**: Browse the available samples in the table
4. **Run a Sample**: Click "Run" next to any sample to test it

## Agent Types and Capabilities

### RAG (Retrieval-Augmented Generation) Agents
- Answer questions using your data sources
- Connect to Cloud Storage, BigQuery, or Firestore
- Deploy with public or private access options

### Data Science Agents
- Perform data analysis using SQL and Python
- Connect to BigQuery datasets
- Generate insights and visualizations

### Customer Service Agents
- Handle customer inquiries and support requests
- Use knowledge bases for consistent responses
- Deploy with webhook integration options

### Brand Search Optimization Agents
- Optimize search results for brand content
- Analyze and enhance marketing content
- Connect to brand-specific data sources

## Deployment Options

### Configuration Settings
- **Conversation Logging**: Enable detailed conversation logs for monitoring
- **Webhook Integration**: Send agent events to external systems
- **Public Access**: Allow public access to deployed agents
- **Data Sources**: Connect agents to various data storages

### Deployment Process
1. Choose an agent type
2. Provide agent name and description
3. Configure general settings
4. Add type-specific configuration
5. Deploy to Google Cloud
6. Get integration code for your applications

## Project Structure

```
.
├── adk-samples/                # ADK samples (cloned from GitHub)
├── static/                     # Static assets
│   ├── css/                    # CSS styles
│   ├── js/                     # JavaScript files
│   └── images/                 # Images and icons
├── templates/                  # HTML templates
│   ├── deploy/                 # Deployment templates
│   └── ...                     # Other templates
├── app.py                      # Main application routes
├── adk_setup.py               # ADK setup utilities
├── deploy_agent.py            # Agent deployment functionality
├── sample_runner.py           # Sample execution logic
├── config.py                  # Configuration utilities
├── main.py                    # Application entry point
└── README.md                  # This documentation
```

## Google Cloud Setup

For full functionality, you need to enable the following Google Cloud APIs:

1. **Vertex AI API**: For agent intelligence and LLM access
2. **Generative Language API**: For language generation capabilities 
3. **Agent Builder API**: For creating and deploying agents
4. **IAM API**: For permission management
5. **BigQuery API**: For data science and analytics functionality (if using data science agents)

## Best Practices

1. **Start Simple**: Begin with basic samples before exploring complex ones
2. **Check Credentials**: Ensure your Google Cloud credentials are properly configured
3. **Read Descriptions**: Sample descriptions contain important information about requirements
4. **Test Locally**: Run and test agents in the local environment before deployment
5. **Monitor Deployments**: Use the deployment view to monitor agent performance

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Authentication Errors**: Check that your Google Cloud credentials are correctly configured
3. **Permission Denied**: Verify that required APIs are enabled in your Google Cloud project
4. **Timeout Errors**: Complex samples may require additional time to execute

### Solutions

1. **Restart the Server**: Sometimes a simple restart resolves environment issues
2. **Check Logs**: Review application logs for detailed error information
3. **Update Credentials**: Refresh your Google Cloud credentials if they've expired
4. **Reinstall Samples**: Use the setup button to refresh the ADK samples repository

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0.

```
Copyright 2025 Jess's Google ADK Gym

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

This Apache License 2.0 is chosen to align with Google's preferred licensing for open source projects related to their technologies.

## Acknowledgments

- Google ADK Team for developing the Agent Development Kit
- All contributors to the ADK samples repository
- The Flask team for the web framework

---

© 2025 Jess's Google ADK Gym