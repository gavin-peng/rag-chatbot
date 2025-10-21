from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from rag_chatbot.config import settings

class AgentType(Enum):
    QA_AGENT = "qa_agent"
    CODE_ASSISTANT = "code_assistant"
    WORKFLOW_AGENT = "workflow_agent"

@dataclass
class AgentConfig:
    """Configuration for different agent types"""
    agent_type: AgentType
    name: str
    description: str
    model_name: str
    temperature: float
    max_search_results: int
    search_strategy: str
    prompt_template: str
    file_category_weights: Dict[str, float]
    language_priorities: List[str]
    enable_code_execution: bool = False
    enable_state_management: bool = False
    
class AgentConfigManager:
    """Manages configurations for different agent types"""
    
    def __init__(self):
        self.configs = self._load_default_configs()
        
    def _load_default_configs(self) -> Dict[AgentType, AgentConfig]:
        """Load default configurations for each agent type"""
        return {
            AgentType.QA_AGENT: AgentConfig(
                agent_type=AgentType.QA_AGENT,
                name="Documentation Q&A Agent",
                description="Answers questions about documentation and general topics",
                model_name=getattr(settings, 'qa_agent_model', "gemini-2.5-flash"),
                temperature=getattr(settings, 'qa_agent_temperature', 0.7),
                max_search_results=getattr(settings, 'max_search_results', 5),
                search_strategy="balanced",
                prompt_template="qa_prompt",
                file_category_weights={"documentation": 0.7, "code": 0.3},
                language_priorities=["markdown", "text"],
                enable_code_execution=False,
                enable_state_management=False
            ),
            
            AgentType.CODE_ASSISTANT: AgentConfig(
                agent_type=AgentType.CODE_ASSISTANT,
                name="Code Assistant Agent",
                description="Helps with code analysis, debugging, and development tasks",
                model_name=getattr(settings, 'code_assistant_model', "gemini-2.5-flash"),
                temperature=getattr(settings, 'code_assistant_temperature', 0.2),
                max_search_results=getattr(settings, 'max_search_results', 10),
                search_strategy="code_focused",
                prompt_template="code_assistant_prompt",
                file_category_weights={"code": 0.8, "documentation": 0.2},
                language_priorities=["python", "java", "wdl", "bash", "yaml"],
                enable_code_execution=getattr(settings, 'enable_code_execution', False),
                enable_state_management=getattr(settings, 'enable_state_management', True)
            ),
            
            AgentType.WORKFLOW_AGENT: AgentConfig(
                agent_type=AgentType.WORKFLOW_AGENT,
                name="Workflow Agent",
                description="Specializes in bioinformatics workflows and pipeline management",
                model_name=getattr(settings, 'workflow_agent_model', "gemini-2.5-flash"), 
                temperature=getattr(settings, 'workflow_agent_temperature', 0.3),
                max_search_results=getattr(settings, 'max_search_results', 8),
                search_strategy="workflow_focused",
                prompt_template="workflow_prompt",
                file_category_weights={"code": 0.6, "documentation": 0.4},
                language_priorities=["wdl", "yaml", "bash", "python"],
                enable_code_execution=False,
                enable_state_management=getattr(settings, 'enable_state_management', True)
            )
        }
    
    def get_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for specific agent type"""
        return self.configs.get(agent_type)
    
    def get_default_agent(self) -> AgentType:
        """Get default agent type from settings or return QA_AGENT"""
        default = getattr(settings, 'default_agent', 'qa_agent')
        try:
            return AgentType(default)
        except ValueError:
            return AgentType.QA_AGENT
    
    def list_available_agents(self) -> List[Dict[str, str]]:
        """List all available agents with their descriptions"""
        return [
            {
                "type": config.agent_type.value,
                "name": config.name,
                "description": config.description
            }
            for config in self.configs.values()
        ]