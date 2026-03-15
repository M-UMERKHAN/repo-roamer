import os
import sys
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.tools import tool


@tool
def list_files(directory: str=".")->str:
    """list all the files in the given directory to explore project structure"""
    try:
        file_list = []
        for root, _,files in os.walk(directory):
            if any(x in root for x in [".git", "venv", "__pycache__"]):
                continue
            for file in files:
                rel_path=os.path.relpath(os.path.join(root, file), directory)
                file_list.append(rel_path)
        return "\n".join(file_list) if file_list else "No files found."
    except Exception as e:
        return f"error: {str(e)}"
    
@tool
def read_file(file_path: str)->str:
    """read the full content of a file to understand its purpose and how it works"""
    try:
        if not os.path.exists(file_path):
            return f"error: file '{file_path}' does not exist."
        with open(file_path, 'r', encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"error: {str(e)}"
    
tools=[list_files,read_file]


@dataclass
class AgentContext:
    user_role: str="Senior Engineer"


@dynamic_prompt
def roamer_prompt(request: ModelRequest) -> str:
    """Generate the system prompt for the codebase exploration agent."""
    # We pull the context OUT of the request right here:
    context = request.runtime.context
    
    return f"""You are a {context.user_role}. Use tools to analyze the codebase."""

llm=ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent=create_agent(
    model=llm,
    tools=tools,
    middleware=[roamer_prompt],
    context_schema=AgentContext
)

if __name__=="__main__":
    print("\nREPO ROAMER v1.0 IS LIVE!")
    while True:
        user_input=input("\nask a question about the codebase (or type 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        print("\n Roamer is thinking...")
        try:
            response=agent.invoke(
                {"input":user_input},
                context=AgentContext(user_role="Senior Engineer")
            )

            result=response["messages"][-1].content
            print("\n Roamer's response:\n", result)
        except Exception as e:
            print("\n An error occurred:", str(e))









