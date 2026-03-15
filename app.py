import os
from dotenv import load_dotenv
import streamlit as st
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.tools import tool

# 1. Load the hidden API key from your local .env file
load_dotenv()

# 2. Build the Web Page Header
st.title("🚀 Repo Roamer: Web Edition")
st.markdown("I am your AI codebase agent. Ask me to read your files!")

# --- STEP 1: TOOLS (Exactly the same as before) ---
@tool
def list_files(directory: str = ".") -> str:
    """List all file paths in the given directory to explore project structure."""
    try:
        file_list = []
        for root, _, files in os.walk(directory):
            if any(x in root for x in [".git", "venv", "__pycache__"]):
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                file_list.append(rel_path)
        return "\n".join(file_list) if file_list else "No files found."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def read_file(file_path: str) -> str:
    """Read the full content of a specific file."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
        with open(file_path, 'r', encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

tools = [list_files, read_file]

# --- STEP 2: DYNAMIC CONTEXT (Exactly the same as before) ---
@dataclass
class AgentContext:
    user_role: str = "Senior Engineer"

@dynamic_prompt
def roamer_prompt(request: ModelRequest) -> str:
    """Generates the system prompt."""
    context = request.runtime.context
    return f"You are a {context.user_role}. Use tools to analyze the codebase."

# --- STEP 3: INITIALIZE AI ---
# @st.cache_resource tells Streamlit to only build the brain once, 
# so it doesn't waste time rebuilding it every single time you type a message.
@st.cache_resource
def get_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_agent(
        model=llm,
        tools=tools,
        middleware=[roamer_prompt],
        context_schema=AgentContext
    )

agent = get_agent()

# --- STEP 4: STREAMLIT CHAT INTERFACE ---

# A. Create a "Memory Bank" for the chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# B. Draw all past messages on the screen
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# C. The new "Input Box" at the bottom of the screen
user_input = st.chat_input("Ask me about your code...")

# D. What happens when the user presses Enter:
if user_input:
    # 1. Save and draw the user's message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Show a loading spinner while the AI thinks
    with st.chat_message("assistant"):
        with st.spinner("Roamer is navigating the files..."):
            try:
                # Fire the LangChain agent!
                response = agent.invoke(
                    {"input": user_input},
                    context=AgentContext(user_role="Senior Architect")
                )
                final_answer = response["messages"][-1].content
                
                # Draw the AI's answer and save it to memory
                st.markdown(final_answer)
                st.session_state.chat_history.append({"role": "assistant", "content": final_answer})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")