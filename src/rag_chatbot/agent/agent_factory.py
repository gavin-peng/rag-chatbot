from typing import Dict, Optional

from rag_chatbot.agent.agent_config import AgentConfigManager, AgentType, AgentConfig
from rag_chatbot.agent.agents import BaseAgent, QAAgent, CodeAssistantAgent, WorkflowAgent
from rag_chatbot.services.vector_service import VectorService
from rag_chatbot.config import settings

class AgentFactory:
    """Factory class for creating and managing different agent types"""
    
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
        self.config_manager = AgentConfigManager()
        self._agents: Dict[AgentType, BaseAgent] = {}
        
    def create_agent(self, agent_type: AgentType) -> BaseAgent:
        """Create an agent of the specified type"""
        config = self.config_manager.get_config(agent_type)
        if not config:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        
        # Create agent based on type
        if agent_type == AgentType.QA_AGENT:
            return QAAgent(config, self.vector_service)
        elif agent_type == AgentType.CODE_ASSISTANT:
            return CodeAssistantAgent(config, self.vector_service)
        elif agent_type == AgentType.WORKFLOW_AGENT:
            return WorkflowAgent(config, self.vector_service)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get an existing agent or create a new one"""
        if agent_type not in self._agents:
            self._agents[agent_type] = self.create_agent(agent_type)
        return self._agents[agent_type]
    
    def get_default_agent(self) -> BaseAgent:
        """Get the default agent based on configuration"""
        default_type = self.config_manager.get_default_agent()
        return self.get_agent(default_type)
    
    def switch_agent(self, agent_type: AgentType) -> BaseAgent:
        """Switch to a different agent type"""
        return self.get_agent(agent_type)
    
    def list_available_agents(self) -> list:
        """List all available agent types with descriptions"""
        return self.config_manager.list_available_agents()
    
    def get_current_agent_info(self, agent: BaseAgent) -> Dict[str, str]:
        """Get information about the current agent"""
        return {
            "name": agent.config.name,
            "type": agent.config.agent_type.value,
            "description": agent.config.description,
            "model": agent.config.model_name,
            "temperature": str(agent.config.temperature)
        }

class AgentManager:
    """High-level manager for agent operations in the chat interface"""
    
    def __init__(self, vector_service: VectorService):
        self.factory = AgentFactory(vector_service)
        self.current_agent = self.factory.get_default_agent()
        self.agent_switching_enabled = True
    
    async def handle_agent_commands(self, message_content: str) -> Optional[str]:
        """Handle special commands for agent management"""
        content = message_content.lower().strip()
        
        # List available agents
        if content in ['/agents', '/list-agents', '!agents']:
            agents = self.factory.list_available_agents()
            response = "🤖 **Available Agents:**\n\n"
            for agent in agents:
                response += f"**{agent['name']}** (`{agent['type']}`)\n"
                response += f"_{agent['description']}_\n\n"
            
            current_info = self.factory.get_current_agent_info(self.current_agent)
            response += f"🔹 **Current Agent:** {current_info['name']}\n"
            response += "Use `/switch <agent_type>` to change agents."
            return response
        
        # Switch agent
        if content.startswith('/switch ') or content.startswith('!switch '):
            agent_type_str = content.split(' ', 1)[1].strip()
            try:
                agent_type = AgentType(agent_type_str)
                old_agent_info = self.factory.get_current_agent_info(self.current_agent)
                self.current_agent = self.factory.switch_agent(agent_type)
                new_agent_info = self.factory.get_current_agent_info(self.current_agent)
                
                return (f"🔄 **Agent Switched**\n"
                       f"From: {old_agent_info['name']}\n"
                       f"To: {new_agent_info['name']}\n\n"
                       f"_{new_agent_info['description']}_")
            except ValueError:
                available = [agent['type'] for agent in self.factory.list_available_agents()]
                return (f"❌ Unknown agent type: `{agent_type_str}`\n"
                       f"Available types: {', '.join(available)}")
        
        # Show current agent
        if content in ['/current', '/current-agent', '!current']:
            info = self.factory.get_current_agent_info(self.current_agent)
            return (f"🤖 **Current Agent:** {info['name']}\n"
                   f"**Type:** `{info['type']}`\n"
                   f"**Model:** {info['model']}\n"
                   f"**Temperature:** {info['temperature']}\n\n"
                   f"_{info['description']}_")
        
        # Help command
        if content in ['/help', '!help', '/agent-help']:
            return ("""🔧 **Agent Commands:**

`/agents` - List all available agents
`/switch <agent_type>` - Switch to a different agent
`/current` - Show current agent information
`/help` - Show this help message

**Available Agent Types:**
- `qa_agent` - General Q&A and documentation
- `code_assistant` - Code analysis and development 
- `workflow_agent` - Bioinformatics workflows and pipelines

**Examples:**
- `/switch code_assistant`
- `/switch workflow_agent`
- `/switch qa_agent`""")
        
        return None
    
    async def process_message(self, message) -> str:
        """Process a message with the current agent"""
        return await self.current_agent.process_message(message)
    
    def get_welcome_message(self) -> str:
        """Generate welcome message with current agent info"""
        stats = self.factory.vector_service.get_collection_stats()
        current_info = self.factory.get_current_agent_info(self.current_agent)
        available_agents = self.factory.list_available_agents()
        
        welcome_msg = f"""🤖 **Welcome to the Multi-Agent RAG Chatbot!**

**Current Agent:** {current_info['name']}
_{current_info['description']}_

**Available Agents:** {', '.join([agent['type'] for agent in available_agents])}

📊 **Knowledge Base:** {stats.get('total_chunks', 'many')} indexed document chunks

**Quick Commands:**
- `/agents` - List all agents
- `/switch <type>` - Change agent
- `/help` - Show help

**Agent Capabilities:**
🔍 **Q&A Agent** - Documentation and general questions
💻 **Code Assistant** - Code analysis, debugging, development
🧬 **Workflow Agent** - Bioinformatics pipelines and WDL workflows

Try asking: "What is Shesmu?" or "/switch code_assistant" to change agents!
"""
        return welcome_msg