import os
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.services.ai.rag_service import get_rag_context

# 1. Define Agent State
class AgentState(TypedDict):
    """
    The state of the agent.
    messages (Annotated[Sequence[BaseMessage], add_messages]) is the conversation history.
    transcript will be the temporary current transcript string so we can extract context.
    rag_context is the contextual information fetched.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    transcript: str
    rag_context: str

# 2. Node definitions

def retrieve_node(state: AgentState):
    """
    Retrieves RAG context using the current transcript.
    """
    transcript = state.get("transcript", "")
    rag_context = get_rag_context(transcript)
    return {"rag_context": rag_context}

def llm_node(state: AgentState):
    """
    Calls the LLM with the context and the conversation history.
    """
    rag_context = state.get("rag_context", "")
    messages = state.get("messages", [])
    
    # We create the dynamic system message based on constraints and local RAG
    system_instruction = (
        "You are Arohan, a concise, highly empathetic Indian Emergency AI Voice Agent. "
        "Respond in the same Indian language the user speaks. Keep answers short (under 2 sentences) "
        "to ensure fast voice rendering. If applicable, use this medical/emergency context: "
        f"{rag_context}"
    )
    
    # Ensure system message is the first
    sys_message = SystemMessage(content=system_instruction)
    
    # Use Gemini API Key from settings or environment
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"messages": [BaseMessage(content="Warning: GEMINI_API_KEY is missing. But I would have answered: Please proceed to the nearest emergency center.", type="ai")]}
    
    # We structure the payload to LLM model: [SystemMessage, *messages]
    llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash", temperature=0.3, google_api_key=api_key)
    
    messages_to_send = [sys_message] + list(messages)
    try:
        response = llm.invoke(messages_to_send)
        return {"messages": [response]}
    except Exception as e:
        print(f"Agent LLM Node Error: {e}")
        return {"messages": [BaseMessage(content="I am experiencing connectivity issues. Please call emergency services directly.", type="ai")]}

# 3. Graph Assembly
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("llm", llm_node)

# Define edges
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "llm")
workflow.add_edge("llm", END)

# Compile graph with a memory saver object for checkpointing
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

def process_voice_agent_text(transcript: str, session_id: str) -> str:
    """
    Entrypoint for the text side of the voice agent.
    Given a transcript and a session identifier, updates the agent state and returns the AI string.
    """
    config = {"configurable": {"thread_id": session_id}}
    
    # Add the current user speech as a human message in the State Graph dict format
    user_input = HumanMessage(content=transcript)
    
    # Run the graph
    try:
        final_state = app_graph.invoke(
            {"messages": [user_input], "transcript": transcript},
            config=config
        )
        # The latest message from the LLM will be at the end of final_state["messages"]
        last_message = final_state["messages"][-1]
        content = last_message.content
        
        # New: Robust check to ensure we only send clean text to the TTS engine
        if isinstance(content, list):
            return " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        return str(content)
    except Exception as e:
        print(f"Graph invocation error: {e}")
        return "I am experiencing connectivity issues. Please call emergency services directly."

