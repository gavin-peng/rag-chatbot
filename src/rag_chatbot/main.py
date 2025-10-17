import chainlit as cl
from langchain_openai import ChatOpenAI
from rag_chatbot.config import settings

llm = ChatOpenAI(
    api_key=settings.openai_api_key,
    model="gpt-3.5-turbo",
    temperature=0.7
)

@cl.on_message
async def main(message: cl.Message):
    # Simple echo for now - we'll add RAG later
    response = await llm.ainvoke(message.content)
    await cl.Message(content=response.content).send()

if __name__ == "__main__":
    cl.run()