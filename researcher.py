from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.tavily import TavilyTools

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

agent = Agent(
    model=Groq(id="openai/gpt-oss-20b"),
    tools=[TavilyTools()],
)

agent.print_response(
    "Use suas ferramentas para pesquisar a temperatura de hoje em São Paulo."
)