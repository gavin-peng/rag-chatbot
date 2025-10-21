"""
Multi-agent system for RAG chatbot.

This package contains the agent system components:
- AgentConfig: Configuration management for different agent types
- BaseAgent: Abstract base class for all agents
- QAAgent: General Q&A and documentation agent
- CodeAssistantAgent: Code analysis and development agent
- WorkflowAgent: Bioinformatics workflow specialist agent
- AgentFactory: Factory for creating and managing agents
- PromptTemplates: Specialized prompts for each agent type
"""

from .agent_config import AgentType, AgentConfig, AgentConfigManager
from .agents import BaseAgent, QAAgent, CodeAssistantAgent, WorkflowAgent
from .agent_factory import AgentFactory, AgentManager
from .prompt_templates import PromptTemplates

__all__ = [
    "AgentType",
    "AgentConfig", 
    "AgentConfigManager",
    "BaseAgent",
    "QAAgent",
    "CodeAssistantAgent", 
    "WorkflowAgent",
    "AgentFactory",
    "AgentManager",
    "PromptTemplates"
]