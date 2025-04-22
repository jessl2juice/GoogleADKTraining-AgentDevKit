import os
import uuid
import json
import logging
import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for deployed agents."""
    enable_logging: bool = True
    enable_webhooks: bool = False
    webhook_url: Optional[str] = None
    public_access: bool = False
    # RAG-specific configs
    data_source: Optional[str] = None
    data_location: Optional[str] = None
    # Data science configs
    bigquery_dataset: Optional[str] = None
    # Customer service configs
    knowledge_base: Optional[str] = None
    # Brand search configs
    brand_data: Optional[str] = None

@dataclass
class AgentMetrics:
    """Metrics for deployed agents."""
    requests: int = 0
    avg_response_time: int = 0
    errors: int = 0

@dataclass
class DeployedAgent:
    """Represents a deployed agent."""
    id: str
    name: str
    type: str
    description: Optional[str]
    status: str  # 'active', 'deploying', 'failed'
    project_id: str
    location: str
    deployed_at: str
    config: AgentConfig = field(default_factory=AgentConfig)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    access_url: Optional[str] = None

class DeploymentManager:
    """Manages agent deployments."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the deployment manager.
        
        Args:
            storage_path: Path to store deployment data. Defaults to .adk-deployments.json in ADK samples directory.
        """
        self.storage_path = storage_path
        if not self.storage_path:
            adk_samples_path = os.path.join(os.getcwd(), "adk-samples")
            self.storage_path = os.path.join(adk_samples_path, ".adk-deployments.json")
        self.deployed_agents = []
        self._load_deployments()
    
    def _load_deployments(self):
        """Load deployments from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.deployed_agents = []
                    for agent_data in data:
                        # Convert dict to AgentConfig
                        config_data = agent_data.pop('config', {})
                        config = AgentConfig(**config_data)
                        
                        # Convert dict to AgentMetrics
                        metrics_data = agent_data.pop('metrics', {})
                        metrics = AgentMetrics(**metrics_data)
                        
                        # Create DeployedAgent
                        agent = DeployedAgent(**agent_data, config=config, metrics=metrics)
                        self.deployed_agents.append(agent)
            except Exception as e:
                logger.error(f"Error loading deployments: {e}")
                self.deployed_agents = []
    
    def _save_deployments(self):
        """Save deployments to storage."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Convert deployed_agents to dicts
            agent_dicts = []
            for agent in self.deployed_agents:
                agent_dict = asdict(agent)
                agent_dicts.append(agent_dict)
            
            # Save to file
            with open(self.storage_path, 'w') as f:
                json.dump(agent_dicts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving deployments: {e}")
    
    def get_all_agents(self) -> List[DeployedAgent]:
        """Get all deployed agents.
        
        Returns:
            List of deployed agents.
        """
        return self.deployed_agents
    
    def get_agent(self, agent_id: str) -> Optional[DeployedAgent]:
        """Get a deployed agent by ID.
        
        Args:
            agent_id: The ID of the agent to retrieve.
            
        Returns:
            The deployed agent, or None if not found.
        """
        for agent in self.deployed_agents:
            if agent.id == agent_id:
                return agent
        return None
    
    def deploy_agent(self, 
                    name: str, 
                    agent_type: str, 
                    description: Optional[str] = None,
                    config: dict = None) -> DeployedAgent:
        """Deploy a new agent.
        
        Args:
            name: Name of the agent.
            agent_type: Type of the agent (rag, data_science, customer_service, brand_search).
            description: Optional description of the agent.
            config: Configuration for the agent.
            
        Returns:
            The deployed agent.
        """
        # Get project ID and location from environment variables
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'example-project-id')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # Create agent configuration
        agent_config = AgentConfig()
        if config:
            # Update configuration with provided values
            for key, value in config.items():
                if hasattr(agent_config, key) and value is not None:
                    setattr(agent_config, key, value)
        
        # Generate unique ID for the agent
        agent_id = str(uuid.uuid4())
        
        # Create access URL if public access is enabled
        access_url = None
        if agent_config.public_access:
            access_url = f"https://console.cloud.google.com/vertex-ai/generative/agents/agent/{agent_id}?project={project_id}"
        
        # Create agent
        deployed_agent = DeployedAgent(
            id=agent_id,
            name=name,
            type=agent_type,
            description=description,
            status="active",  # In a real implementation, this would be 'deploying' initially
            project_id=project_id,
            location=location,
            deployed_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            config=agent_config,
            access_url=access_url
        )
        
        # Add to deployed agents
        self.deployed_agents.append(deployed_agent)
        self._save_deployments()
        
        return deployed_agent
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete a deployed agent.
        
        Args:
            agent_id: The ID of the agent to delete.
            
        Returns:
            True if the agent was deleted, False otherwise.
        """
        for i, agent in enumerate(self.deployed_agents):
            if agent.id == agent_id:
                self.deployed_agents.pop(i)
                self._save_deployments()
                return True
        return False
    
    def deploy_from_sample(self, sample_path: str, name: str, description: Optional[str] = None, config: dict = None) -> DeployedAgent:
        """Deploy an agent from a sample.
        
        Args:
            sample_path: Path to the sample file.
            name: Name for the deployed agent.
            description: Optional description of the agent.
            config: Configuration for the agent.
            
        Returns:
            The deployed agent.
        """
        # Determine agent type from sample path
        agent_type = "sample"  # Default
        if "rag" in sample_path.lower():
            agent_type = "rag"
        elif "data-science" in sample_path.lower() or "data_science" in sample_path.lower():
            agent_type = "data_science"
        elif "customer-service" in sample_path.lower() or "customer_service" in sample_path.lower():
            agent_type = "customer_service"
        elif "brand-search" in sample_path.lower() or "brand_search" in sample_path.lower():
            agent_type = "brand_search"
        
        # Deploy the agent
        return self.deploy_agent(name, agent_type, description, config)