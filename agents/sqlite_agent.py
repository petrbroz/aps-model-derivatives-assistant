import os
from datetime import datetime
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

with open(os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPTS.md")) as f:
    SYSTEM_PROMPTS = f.read().replace("{", "{{").replace("}", "}}")

class Agent:
    def __init__(self, llm: BaseChatModel, prompt_template: ChatPromptTemplate, tools: list[BaseTool], cache_urn_dir: str):
        self._agent = create_react_agent(llm, tools, prompt=prompt_template, checkpointer=MemorySaver())
        self._config = {"configurable": {"thread_id": os.path.basename(cache_urn_dir)}}
        self._logs_path = os.path.join(cache_urn_dir, "logs.txt")

    def _log(self, message: str):
        with open(self._logs_path, "a") as log:
            log.write(f"[{datetime.now().isoformat()}] {message}\n\n")

    async def prompt(self, prompt: str) -> list[str]:
        self._log(f"User: {prompt}")
        responses = []
        async for step in self._agent.astream({"messages": [("human", prompt)]}, config=self._config, stream_mode="updates"):
            if "agent" in step:
                for message in step["agent"]["messages"]:
                    self._log(message.pretty_repr())
                    if isinstance(message.content, str) and message.content:
                        responses.append(message.content)
            if "tools" in step:
                for message in step["tools"]["messages"]:
                    self._log(message.pretty_repr())
        return responses

async def create_sqlite_agent(db: SQLDatabase, cache_urn_dir: str):
    llm = ChatOpenAI(model="gpt-4o")
    sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    prompt_template = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPTS), ("placeholder", "{messages}")])
    return Agent(llm, prompt_template, sql_toolkit.get_tools(), cache_urn_dir)
