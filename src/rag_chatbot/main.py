import chainlit as cl
from langchain_google_genai import ChatGoogleGenerativeAI
from rag_chatbot.config import settings 


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,  
    temperature=0.7
)

@cl.on_message
async def main(message: cl.Message):
    response = await llm.ainvoke(message.content)
    await cl.Message(content=response.content).send()

if __name__ == "__main__":
    cl.run()