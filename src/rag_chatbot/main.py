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
    """Format retrieved documents with language-aware code blocks"""
    if not results:
        return "No relevant documents found."
    
    context_parts = []
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        source_file = metadata.get('source_file', 'Unknown')
        repo_name = metadata.get('repo_name', '')
        language = metadata.get('language', '')
        file_category = metadata.get('file_category', 'unknown')
        content = result['content']
        similarity = result['similarity']
        
        # Build source description
        source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
        
        # Format content based on type
        if file_category == 'code' and language:
            # Wrap code in language-specific markdown blocks
            formatted_content = f"```{language}\n{content}\n```"
        else:
            formatted_content = content
        
        context_parts.append(
            f"[Source {i}: {source_desc} ({file_category}) - relevance: {similarity:.2f}]\n{formatted_content}\n"
        )
    
    return "\n---\n".join(context_parts)
def detect_query_intent(query: str) -> Dict[str, Any]:
    """Detect what the user is asking about"""
    query_lower = query.lower()
    
    intent = {
        'is_code_question': False,
        'is_version_question': False,
        'is_workflow_question': False,
        'language_hints': [],
        'search_boost': {}
    }
    
    # Detect version questions
    if any(word in query_lower for word in ['version', 'what version', 'which version']):
        intent['is_version_question'] = True
        intent['search_boost'] = {'file_category': 'code'}  # Prioritize code files
    
    # Detect workflow questions
    if any(word in query_lower for word in ['workflow', 'task', 'wdl', 'pipeline']):
        intent['is_workflow_question'] = True
        intent['language_hints'] = ['wdl']
    
    # Detect code-specific questions
    if any(word in query_lower for word in ['function', 'class', 'method', 'code', 'implementation']):
        intent['is_code_question'] = True
        intent['search_boost'] = {'file_category': 'code'}
    
    # Detect tool questions
    if any(word in query_lower for word in ['tool', 'tools', 'software', 'markduplicates', 'picard', 'bwa']):
        intent['is_code_question'] = True
        intent['search_boost'] = {'file_category': 'code'}
    
    return intent

def create_rag_prompt(user_question: str, context: str) -> str:
    """Create an enhanced prompt that handles both documentation and code"""
    return f"""You are a helpful technical assistant specializing in bioinformatics pipelines, workflows, and code.

Use the following context to answer the user's question. The context may include:
- Documentation (markdown files)
- Code files (WDL workflows, Python, Java, etc.)
- Configuration files

CONTEXT:
{context}

QUESTION: {user_question}

INSTRUCTIONS:
- Answer based on the provided context
- For code-related questions, quote relevant code snippets with line references
- When referencing code, mention the file name and what the code does
- If looking for tool versions or specific commands, check both code and documentation
- For WDL workflows: look for task definitions, runtime blocks, and docker images
- For version questions: check docker images, runtime requirements, and dependency lists
- If context lacks information, clearly state what's missing
- Be specific and technical when appropriate

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
        # Detect query intent
        intent = detect_query_intent(user_question)
        
        # Send initial thinking message
        await cl.Message(content="🔍 Searching documentation and code...").send()
        
        # Search with more results if it's a code question
        n_results = 15 if intent['is_code_question'] or intent['is_version_question'] else 10
        search_results = vector_service.search(user_question, n_results=n_results)
        
        # Filter by language if detected
        if intent['language_hints']:
            lang_results = [r for r in search_results if r['metadata'].get('language') in intent['language_hints']]
            if lang_results:
                search_results = lang_results + [r for r in search_results if r not in lang_results]
        
        # Prioritize code results for code questions
        if intent['is_code_question'] or intent['is_version_question']:
            code_results = [r for r in search_results if r['metadata'].get('file_category') == 'code']
            doc_results = [r for r in search_results if r['metadata'].get('file_category') != 'code']
            mixed_results = code_results[:4] + doc_results[:1]  # Heavily favor code
        else:
            doc_results = [r for r in search_results if r['metadata'].get('source_type') == 'markdown_document']
            code_results = [r for r in search_results if r['metadata'].get('source_type') == 'repository']
            mixed_results = code_results[:2] + doc_results[:3]  # Balanced mix
        
        # Ensure we have at least some results
        if not mixed_results and search_results:
            mixed_results = search_results[:5]
        
        # Show what we found
        result_summary = f"Found {len([r for r in search_results if r['metadata'].get('file_category') == 'code'])} code files and {len([r for r in search_results if r['metadata'].get('source_type') == 'markdown_document'])} documentation files"
        await cl.Message(content=f"📊 {result_summary}").send()
        
        # Format context for LLM
        context = format_retrieved_context(mixed_results)
        
        # Create RAG prompt
        rag_prompt = create_rag_prompt(user_question, context)
        
        # Send generating message
        await cl.Message(content="💭 Generating response...").send()
        
        # Get LLM response
        response = await llm.ainvoke(rag_prompt)
        
        # Prepare enhanced source information
        sources_info = "\n\n**Sources:**\n"
        for i, result in enumerate(mixed_results, 1):
            source_file = result['metadata'].get('source_file', 'Unknown')
            repo_name = result['metadata'].get('repo_name', '')
            language = result['metadata'].get('language', '')
            similarity = result['similarity']
            
            source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
            if language:
                source_desc += f" ({language})"
            
            sources_info += f"{i}. {source_desc} - relevance: {similarity:.2f}\n"
        
        # Send final response
        final_response = response.content + sources_info
        await cl.Message(content=final_response).send()
        
    except Exception as e:
        error_msg = f"❌ Error processing your question: {str(e)}"
        await cl.Message(content=error_msg).send()
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cl.run()