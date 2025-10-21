from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import chainlit as cl
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_chatbot.agent.agent_config import AgentConfig, AgentType
from rag_chatbot.agent.prompt_templates import PromptTemplates
from rag_chatbot.services.vector_service import VectorService
from rag_chatbot.config import settings

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig, vector_service: VectorService):
        self.config = config
        self.vector_service = vector_service
        self.conversation_state = {}
        
        # Initialize LLM with agent-specific settings
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=settings.google_api_key,
            temperature=config.temperature
        )
    
    @abstractmethod
    async def process_message(self, message: cl.Message) -> str:
        """Process user message and return response"""
        pass
    
    def apply_search_strategy(self, query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply agent-specific search strategy to filter and rank results"""
        if self.config.search_strategy == "balanced":
            return self._balanced_search_strategy(search_results)
        elif self.config.search_strategy == "code_focused":
            return self._code_focused_strategy(search_results)
        elif self.config.search_strategy == "workflow_focused":
            return self._workflow_focused_strategy(search_results)
        else:
            return search_results[:self.config.max_search_results]
    
    def _balanced_search_strategy(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Balanced search mixing documentation and code"""
        weighted_results = []
        for result in results:
            file_category = result['metadata'].get('file_category', 'unknown')
            weight = self.config.file_category_weights.get(file_category, 0.5)
            weighted_score = result['similarity'] * weight
            result['weighted_score'] = weighted_score
            weighted_results.append(result)
        
        weighted_results.sort(key=lambda x: x['weighted_score'], reverse=True)
        return weighted_results[:self.config.max_search_results]
    
    def _code_focused_strategy(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize code files and technical content"""
        code_results = [r for r in results if r['metadata'].get('file_category') == 'code']
        doc_results = [r for r in results if r['metadata'].get('file_category') != 'code']
        
        # Take more code results
        mixed_results = code_results[:8] + doc_results[:2]
        return mixed_results[:self.config.max_search_results]
    
    def _workflow_focused_strategy(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Focus on workflow and pipeline related content"""
        # Prioritize WDL and workflow-related files
        workflow_results = []
        other_results = []
        
        for result in results:
            language = result['metadata'].get('language', '').lower()
            filename = result['metadata'].get('source_file', '').lower()
            
            if ('wdl' in language or 'workflow' in filename or 
                'pipeline' in filename or '.wdl' in filename):
                workflow_results.append(result)
            else:
                other_results.append(result)
        
        mixed_results = workflow_results[:6] + other_results[:2]
        return mixed_results[:self.config.max_search_results]
    
    def format_retrieved_context(self, results: List[Dict[str, Any]]) -> str:
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
            similarity = result.get('similarity', 0.0)
            
            # Build source description
            source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
            
            # Format content based on type
            if file_category == 'code' and language:
                formatted_content = f"```{language}\n{content}\n```"
            else:
                formatted_content = content
            
            context_parts.append(
                f"[Source {i}: {source_desc} ({file_category}) - relevance: {similarity:.2f}]\n{formatted_content}\n"
            )
        
        return "\n---\n".join(context_parts)

class QAAgent(BaseAgent):
    """Q&A Agent for documentation questions"""
    
    async def process_message(self, message: cl.Message) -> str:
        user_question = message.content
        
        # Search for relevant documents
        search_results = self.vector_service.search(user_question, n_results=15)
        filtered_results = self.apply_search_strategy(user_question, search_results)
        
        # Format context and create prompt
        context = self.format_retrieved_context(filtered_results)
        prompt = PromptTemplates.get_prompt_by_template_name(
            self.config.prompt_template, user_question, context
        )
        
        # Get LLM response
        response = await self.llm.ainvoke(prompt)
        
        # Format sources
        sources_info = self._format_sources(filtered_results)
        
        return response.content + sources_info
    
    def _format_sources(self, results: List[Dict[str, Any]]) -> str:
        """Format source information"""
        if not results:
            return ""
        
        sources_info = "\n\n**Sources:**\n"
        for i, result in enumerate(results, 1):
            source_file = result['metadata'].get('source_file', 'Unknown')
            repo_name = result['metadata'].get('repo_name', '')
            similarity = result.get('similarity', 0.0)
            
            source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
            sources_info += f"{i}. {source_desc} - relevance: {similarity:.2f}\n"
        
        return sources_info

class CodeAssistantAgent(BaseAgent):
    """Code Assistant Agent for development tasks"""
    
    def __init__(self, config: AgentConfig, vector_service: VectorService):
        super().__init__(config, vector_service)
        # Initialize conversation state for code assistance
        self.conversation_state = {
            'current_task': '',
            'working_files': [],
            'code_context': {}
        }
    
    async def process_message(self, message: cl.Message) -> str:
        user_question = message.content
        
        # Detect code-specific intent
        intent = self._detect_code_intent(user_question)
        
        # Update conversation state based on intent
        self._update_conversation_state(intent, user_question)
        
        # Search with code-focused strategy
        search_results = self.vector_service.search(user_question, n_results=20)
        filtered_results = self.apply_search_strategy(user_question, search_results)
        
        # Format context and create prompt
        context = self.format_retrieved_context(filtered_results)
        prompt = PromptTemplates.get_prompt_by_template_name(
            self.config.prompt_template, user_question, context, self.conversation_state
        )
        
        # Get LLM response
        response = await self.llm.ainvoke(prompt)
        
        # Format sources with code-specific information
        sources_info = self._format_code_sources(filtered_results)
        
        return response.content + sources_info
    
    def _detect_code_intent(self, query: str) -> Dict[str, Any]:
        """Detect what kind of code assistance is needed"""
        query_lower = query.lower()
        
        intent = {
            'is_debugging': any(word in query_lower for word in ['debug', 'error', 'fix', 'issue', 'problem']),
            'is_implementation': any(word in query_lower for word in ['implement', 'create', 'build', 'develop']),
            'is_analysis': any(word in query_lower for word in ['analyze', 'review', 'explain', 'understand']),
            'is_optimization': any(word in query_lower for word in ['optimize', 'improve', 'faster', 'performance']),
            'languages': []
        }
        
        # Detect mentioned languages
        for lang in self.config.language_priorities:
            if lang.lower() in query_lower:
                intent['languages'].append(lang)
        
        return intent
    
    def _update_conversation_state(self, intent: Dict[str, Any], query: str):
        """Update conversation state based on detected intent"""
        if intent['is_debugging']:
            self.conversation_state['current_task'] = 'debugging'
        elif intent['is_implementation']:
            self.conversation_state['current_task'] = 'implementation'
        elif intent['is_analysis']:
            self.conversation_state['current_task'] = 'code_analysis'
        elif intent['is_optimization']:
            self.conversation_state['current_task'] = 'optimization'
    
    def _format_code_sources(self, results: List[Dict[str, Any]]) -> str:
        """Format sources with code-specific details"""
        if not results:
            return ""
        
        sources_info = "\n\n**Code Sources:**\n"
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source_file = metadata.get('source_file', 'Unknown')
            repo_name = metadata.get('repo_name', '')
            language = metadata.get('language', '')
            similarity = result.get('similarity', 0.0)
            
            source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
            if language:
                source_desc += f" ({language})"
            
            sources_info += f"{i}. {source_desc} - relevance: {similarity:.2f}\n"
        
        return sources_info

class WorkflowAgent(BaseAgent):
    """Workflow Agent for pipeline and workflow questions"""
    
    def __init__(self, config: AgentConfig, vector_service: VectorService):
        super().__init__(config, vector_service)
        self.conversation_state = {
            'current_pipeline': '',
            'workflow_context': {},
            'tools_discussed': []
        }
    
    async def process_message(self, message: cl.Message) -> str:
        user_question = message.content
        
        # Detect workflow-specific context
        workflow_context = self._detect_workflow_context(user_question)
        self._update_workflow_state(workflow_context)
        
        # Search with workflow-focused strategy
        search_results = self.vector_service.search(user_question, n_results=15)
        filtered_results = self.apply_search_strategy(user_question, search_results)
        
        # Format context and create prompt
        context = self.format_retrieved_context(filtered_results)
        prompt = PromptTemplates.get_prompt_by_template_name(
            self.config.prompt_template, user_question, context, self.conversation_state
        )
        
        # Get LLM response
        response = await self.llm.ainvoke(prompt)
        
        # Format sources with workflow-specific information
        sources_info = self._format_workflow_sources(filtered_results)
        
        return response.content + sources_info
    
    def _detect_workflow_context(self, query: str) -> Dict[str, Any]:
        """Detect workflow-related context"""
        query_lower = query.lower()
        
        context = {
            'has_wdl': 'wdl' in query_lower,
            'has_pipeline': any(word in query_lower for word in ['pipeline', 'workflow']),
            'tools_mentioned': [],
            'workflow_stage': None
        }
        
        # Common bioinformatics tools
        tools = ['bwa', 'picard', 'gatk', 'samtools', 'bcftools', 'markduplicates']
        for tool in tools:
            if tool in query_lower:
                context['tools_mentioned'].append(tool)
        
        return context
    
    def _update_workflow_state(self, context: Dict[str, Any]):
        """Update workflow conversation state"""
        if context['tools_mentioned']:
            self.conversation_state['tools_discussed'].extend(context['tools_mentioned'])
        
        if context['has_pipeline']:
            self.conversation_state['current_pipeline'] = 'active_discussion'
    
    def _format_workflow_sources(self, results: List[Dict[str, Any]]) -> str:
        """Format sources with workflow-specific details"""
        if not results:
            return ""
        
        sources_info = "\n\n**Workflow Sources:**\n"
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source_file = metadata.get('source_file', 'Unknown')
            repo_name = metadata.get('repo_name', '')
            language = metadata.get('language', '')
            similarity = result.get('similarity', 0.0)
            
            source_desc = f"{repo_name}/{source_file}" if repo_name else source_file
            if language:
                source_desc += f" ({language})"
            
            # Add workflow-specific indicators
            if '.wdl' in source_file:
                source_desc += " [WDL Workflow]"
            elif 'pipeline' in source_file.lower():
                source_desc += " [Pipeline]"
            
            sources_info += f"{i}. {source_desc} - relevance: {similarity:.2f}\n"
        
        return sources_info