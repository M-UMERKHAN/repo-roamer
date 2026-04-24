import os
import requests
from dotenv import load_dotenv
import streamlit as st
from dataclasses import dataclass

# ⚡ YOUR CUSTOM ARCHITECTURE IMPORTS
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.tools import tool

# ⚡ STANDARD OPENAI IMPORT
from langchain_openai import ChatOpenAI

# 1. Load the hidden API keys
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 2. Build the Web Page Header & Sidebar
st.set_page_config(page_title="Repo Roamer", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS FOR PREMIUM UI ---
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* Global Typography & Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #0f172a, #111827, #000000);
        color: #f8fafc;
    }

    /* Hero Section */
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-top: 2rem;
        margin-bottom: 0.5rem;
        animation: fadeInDown 1s ease-out;
    }
    
    .hero-subtitle {
        text-align: center;
        font-size: 1.25rem;
        color: #94a3b8;
        margin-bottom: 3rem;
        font-weight: 300;
        animation: fadeInUp 1s ease-out;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.03);
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #38bdf8;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }

    /* Chat Input Container */
    [data-testid="stChatInput"] {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-2px);
    }
    
    /* User Message distinct style */
    [data-testid="stChatMessage"][data-baseweb="card"] {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.1);
    }

    /* Animations */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🚀 Repo Roamer</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Agentic AI codebase explorer. Give me a public GitHub repo, and ask me anything!</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔧 Configuration")
target_repo = st.sidebar.text_input("GitHub Repo (username/repo):", "M-UMERKHAN/Secure-Chat-Project")

# --- STEP 1: TOOLS (Thread-Safe + Rate Limit Checking) ---
@tool
def generate_codebase_tree(repo_string: str) -> str:
    """Step 1: Generates a hierarchical tree structure of the GitHub repository."""
    print(f"\n[TOOL] AI TRIGGERED TOOL: Mapping tree for {repo_string}...")
    try:
        url = f"https://api.github.com/repos/{repo_string}/git/trees/main?recursive=1"
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: Could not fetch tree. You may be rate-limited by GitHub."
            print(f"[ERROR] {error_msg}")
            return error_msg
            
        data = response.json()
        tree_paths = [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]
        return "Hierarchical Codebase Tree:\n" + "\n".join(tree_paths) if tree_paths else "No files found."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def read_github_file(repo_string: str, file_path: str) -> str:
    """Step 3: Extracts the exact context from a specific file."""
    print(f"[TOOL] AI TRIGGERED TOOL: Reading file -> {file_path}...")
    try:
        url = f"https://raw.githubusercontent.com/{repo_string}/main/{file_path}"
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}: File '{file_path}' not found."
            print(f"[ERROR] {error_msg}")
            return error_msg
            
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

tools = [generate_codebase_tree, read_github_file]

# --- STEP 2: DYNAMIC CONTEXT (Strict Error Handling) ---
@dataclass
class AgentContext:
    user_role: str = "Senior Software Architect"
    github_repo: str = ""  

@dynamic_prompt
def roamer_prompt(request: ModelRequest) -> str:
    context = request.runtime.context
    
    return f"""You are a {context.user_role} analyzing the GitHub repository: '{context.github_repo}'.

    MANDATORY WORKFLOW:
    1. FIRST, use `generate_codebase_tree`.
    2. IF the tool returns an 'API Error' (like a rate limit), STOP. Tell the user exactly what the error is. DO NOT GUESS FILE NAMES.
    3. IF successful, find the exact file requested (e.g., 'Alice.py') in the tree.
    4. THIRD, use `read_github_file` to download it.

    CRITICAL RULES:
    - NEVER read 'README.md' unless the user explicitly asks for a summary.
    - NEVER guess file names. If a tool fails, report the failure."""
# --- STEP 3: INITIALIZE AI (GPT-4o inside YOUR wrapper) ---
def get_agent():
    # ⚡ UPGRADED TO gpt-4o FOR MAXIMUM REASONING CAPABILITY
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # ⚡ Back to your specific create_agent wrapper!
    return create_agent(
        model=llm,
        tools=tools,
        middleware=[roamer_prompt],
        context_schema=AgentContext
    )

agent = get_agent()

# --- STEP 4: STREAMLIT CHAT INTERFACE (STATELESS) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask me about the architecture...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("GPT-4o is navigating the codebase..."):
            try:
                # Stateless execution: It only sees the new question and your custom context
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    context=AgentContext(user_role="Senior Architect", github_repo=target_repo)
                )

                final_answer = response["messages"][-1].content

                st.markdown(final_answer)
                st.session_state.chat_history.append({"role": "assistant", "content": final_answer})

            except Exception as e:
                st.error(f"Error: {str(e)}")
