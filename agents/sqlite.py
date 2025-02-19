import os
from datetime import datetime
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

_llm = ChatOpenAI(model="gpt-4o")

class SqliteAgent:
    def __init__(self, db: SQLDatabase, cache_urn_dir: str):
        sql_toolkit = SQLDatabaseToolkit(db=db, llm=_llm)
        with open(os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPTS.md")) as f:
            system_prompts = f.read()
        prompt_template = ChatPromptTemplate.from_messages([("system", system_prompts), ("placeholder", "{messages}")])
        self._agent = create_react_agent(_llm, sql_toolkit.get_tools(), prompt=prompt_template, checkpointer=MemorySaver())
        self._config = {"configurable": {"thread_id": os.path.basename(cache_urn_dir)}}
        self._logs_path = os.path.join(cache_urn_dir, "logs.txt")

    def _log(self, message: str):
        with open(self._logs_path, "a") as log:
            log.write(f"[{datetime.now().isoformat()}] {message}\n\n")

    async def prompt(self, prompt: str) -> list[str]:
        self._log(f"User: {prompt}")
        responses = []
        async for step in self._agent.astream({"messages": [("human", prompt)]}, self._config, stream_mode="updates"):
            self._log(f"Assistant: {step}")
            if "agent" in step:
                for message in step["agent"]["messages"]:
                    if isinstance(message.content, str) and message.content:
                        responses.append(message.content)
        return responses