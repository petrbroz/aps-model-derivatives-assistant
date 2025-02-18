from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

def create_agent(llm, database_path):
    db = SQLDatabase.from_uri(f"sqlite:///{database_path}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    system_prompt = [
        "You are an AI assistant providing data analytics for design properties stored in sqlite database.",
        "Dimension values stored in the database use standard units such as 'm', 'm^2', 'm^3', or '°'.",
        """
            Whenever you are referring to one or more specific elements, include an HTML link in your response
            with all the element IDs listed in the `data-dbids` attribute.
            Example: `<a href="#" data-dbids="1,2,3,4">Show in Viewer</a>`.
        """
    ]
    prompt_template = ChatPromptTemplate.from_messages([("system", system_prompt), ("placeholder", "{messages}")])
    return create_react_agent(llm, toolkit.get_tools(), prompt=prompt_template, checkpointer=MemorySaver())