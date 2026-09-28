import os
from pathlib import Path

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.db.sqlite import SqliteDb
from dotenv import load_dotenv
from agno.models.openai import OpenAIResponses
from agno.os import AgentOS
from agno.tools.tavily import TavilyTools

from transcription_reader import get_creator_transcriptions, list_available_creators

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

storage_dir = BASE_DIR / "tmp"
storage_dir.mkdir(exist_ok=True)


def create_db():
    """Use PostgreSQL em produção e SQLite apenas para desenvolvimento local."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return PostgresDb(
            db_url=database_url,
            session_table="agent_sessions",
        )

    return SqliteDb(
        session_table="agent_sessions",
        db_file=str(storage_dir / "storage.db"),
    )


copywriter = Agent(
    model=OpenAIResponses(
        id="gpt-5.6-terra",
        reasoning_effort="medium",
    ),
    name="copywriter",

    update_memory_on_run=True,
    add_memories_to_context=True,
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=10,

    db=create_db(),

    tools=[
        TavilyTools(),
        list_available_creators,
        get_creator_transcriptions
        ], 

    instructions=(BASE_DIR / "prompts/copywriter.md").read_text(encoding="utf-8"),
)

agent_os = AgentOS(agents=[copywriter])
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(
        app="agent:app",
        host=os.getenv("AGENT_OS_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "7777")),
        reload=os.getenv("AGENT_OS_RELOAD", "false").lower() == "true",
    )
