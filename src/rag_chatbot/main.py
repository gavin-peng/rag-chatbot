import chainlit as cl
from typing import Optional

# Import agent components
from rag_chatbot.agent.agent_factory import AgentManager
from rag_chatbot.services.vector_service import VectorService
from rag_chatbot.config import settings

# Initialize services
vector_service = VectorService()
agent_manager = AgentManager(vector_service)

@cl.on_chat_start
async def start():
    """Initialize the chat session with multi-agent support"""
    # Store agent manager in user session
    cl.user_session.set("agent_manager", agent_manager)
    
    # Send welcome message with agent information
    welcome_msg = agent_manager.get_welcome_message()
    await cl.Message(content=welcome_msg).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with multi-agent support"""
    try:
        # Get agent manager from session
        agent_manager = cl.user_session.get("agent_manager")
        if not agent_manager:
            await cl.Message(content="❌ Session error. Please refresh the page.").send()
            return
        
        user_input = message.content.strip()
        
        # Check for agent management commands first
        command_response = await agent_manager.handle_agent_commands(user_input)
        if command_response:
            await cl.Message(content=command_response).send()
            return
        
        # Show processing message
        current_agent_info = agent_manager.factory.get_current_agent_info(agent_manager.current_agent)
        processing_msg = f"🔍 {current_agent_info['name']} is processing your request..."
        await cl.Message(content=processing_msg).send()
        
        # Process message with current agent
        response = await agent_manager.process_message(message)
        
        # Send the response
        await cl.Message(content=response).send()
        
    except Exception as e:
        error_msg = f"❌ Error processing your request: {str(e)}"
        await cl.Message(content=error_msg).send()
        
        # Print traceback for debugging
        import traceback
        traceback.print_exc()

@cl.on_chat_end
async def end():
    """Clean up when chat session ends"""
    # Clear any persistent state if needed
    pass

async def switch_agent_programmatically(agent_type: str) -> bool:
    """Switch agent programmatically from code"""
    try:
        agent_manager = cl.user_session.get("agent_manager")
        if agent_manager:
            from rag_chatbot.agent.agent_config import AgentType
            agent_type_enum = AgentType(agent_type)
            agent_manager.current_agent = agent_manager.factory.switch_agent(agent_type_enum)
            return True
    except Exception as e:
        print(f"Error switching agent: {e}")
        return False
    return False

def configure_agents_from_env():
    """Configure agents based on environment variables"""
    # Allow environment variable overrides
    if hasattr(settings, 'default_agent'):
        print(f"Using default agent from settings: {settings.default_agent}")
    
    if hasattr(settings, 'enable_code_execution'):
        print(f"Code execution enabled: {settings.enable_code_execution}")
    
    # Add any other environment-based configurations here

if __name__ == "__main__":
    # Configure from environment
    configure_agents_from_env()
    
    # Run the Chainlit app
    cl.run(
        host=getattr(settings, 'host', "0.0.0.0"),
        port=getattr(settings, 'port', 8000),
        debug=getattr(settings, 'debug', False)
    )