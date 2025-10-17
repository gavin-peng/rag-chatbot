import chainlit as cl
from langchain_google_genai import ChatGoogleGenerativeAI
from rag_chatbot.config import settings
from rag_chatbot.services.vector_service import VectorService
from typing import List, Dict, Any

# Initialize services
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,  
    temperature=0.7
)

vector_service = VectorService()

def format_retrieved_context(results: List[Dict[str, Any]]) -> str:
    """Format retrieved documents for LLM context"""
    if not results:
        return "No relevant documents found."
    
    context_parts = []
    for i, result in enumerate(results, 1):
        source = result['metadata'].get('source_file', 'Unknown')
        content = result['content']
        similarity = result['similarity']
        
        context_parts.append(
            f"[Source {i}: {source} (relevance: {similarity:.2f})]\n{content}\n"
        )
    
    return "\n---\n".join(context_parts)

def create_rag_prompt(user_question: str, context: str) -> str:
    """Create a prompt that combines user question with retrieved context"""
    return f"""You are a helpful assistant that answers questions based on provided documentation. 

Use the following context to answer the user's question. If the context doesn't contain relevant information, say so clearly.

CONTEXT:
{context}

QUESTION: {user_question}

INSTRUCTIONS:
- Answer based primarily on the provided context
- If you use information from the context, mention which source it came from
- If the context doesn't have enough information, be honest about the limitations
- Provide a clear, helpful response

ANSWER:"""

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    # Get collection stats to show user
    stats = vector_service.get_collection_stats()
    welcome_msg = f"""Welcome to the RAG Chatbot!

I can answer questions about your documentation using {stats.get('total_chunks', 'many')} indexed document chunks.

Ask me anything about:
- Infrastructure and systems
- Workflows and processes  
- Technical concepts and definitions
- Any topic covered in your documentation

Try asking: "What is Shesmu?" or "How does the infrastructure work?"
"""
    await cl.Message(content=welcome_msg).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with RAG"""
    user_question = message.content
    
    try:
        # Send initial thinking message
        await cl.Message(content=" Searching documentation...").send()
        
        # 1. Retrieve relevant documents
        search_results = vector_service.search(user_question, n_results=3)
        
        # 2. Format context for LLM
        context = format_retrieved_context(search_results)
        
        # 3. Create RAG prompt
        rag_prompt = create_rag_prompt(user_question, context)
        
        # Send generating message
        await cl.Message(content=" Generating response...").send()
        
        # 4. Get LLM response
        response = await llm.ainvoke(rag_prompt)
        
        # 5. Prepare source information
        sources_info = "\n\n**Sources:**\n"
        for i, result in enumerate(search_results, 1):
            source_file = result['metadata'].get('source_file', 'Unknown')
            similarity = result['similarity']
            sources_info += f"- {source_file} (relevance: {similarity:.2f})\n"
        
        # 6. Send final response
        final_response = response.content + sources_info
        await cl.Message(content=final_response).send()
        
    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}\n\nLet me try to help with general knowledge..."
        await cl.Message(content=error_msg).send()
        
        # Fallback to direct LLM response
        try:
            fallback_response = await llm.ainvoke(user_question)
            await cl.Message(content=f" General response:\n{fallback_response.content}").send()
        except Exception as fallback_error:
            await cl.Message(content=f"Sorry, I encountered an error: {fallback_error}").send()

if __name__ == "__main__":
    cl.run()