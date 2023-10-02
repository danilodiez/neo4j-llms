from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain, LLMChain
from langchain.graphs import Neo4jGraph
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.prompts import MessagesPlaceholder, PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.tools import StructuredTool, BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from dotenv import load_dotenv
import os
load_dotenv('.env')

USER = os.getenv('NEO4J_USER')
URL = os.getenv('NEO4J_URL')
NEO4J_PASS = os.getenv('NEO4J_PASS')
OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')

graph = Neo4jGraph(
    url=URL, username=USER, password=NEO4J_PASS
)
llm = ChatOpenAI(openai_api_key=OPEN_AI_KEY, temperature=0)

# Agent for querying the database
CYPHER_GENERATION_TEMPLATE = """
Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Cypher examples:
# How many streamers are from Norway?
MATCH (s:Stream)-[:HAS_LANGUAGE]->(:Language {{name: 'no'}})
RETURN count(s) AS streamers

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
The question is:
{question}
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)
cypher_chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(openai_api_key=OPEN_AI_KEY, temperature=0),
    graph=graph,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT
)

# Agent for creating/updating the neo4j schema is info not enough
GENERATE_GRAPH_PROMPT = '''
    You are a data scientist working for a company that is building a
    graph database. Your task is to extract information from user affirmations
    {input} Add this to the schema
    and convert it into a graph database schema to update the existing neo4j schema.
    Provide a set of Nodes in the form [ENTITY_ID, TYPE, PROPERTIES]
    and a set of relationships in the form [ENTITY_ID_1, RELATIONSHIP,
    ENTITY_ID_2, PROPERTIES].
    It is important that the ENTITY_ID_1 and ENTITY_ID_2 exists as
    nodes with a matching ENTITY_ID.
    If not create those new ENTITIES
    When you find a node or relationship you want to add try to create a
    generic TYPE for it that  describes the entity you can also think of
    it as a label.
    Return it in the form of a Cypher query for creating nodes and
    relationships
'''

cypher_llm = OpenAI(openai_api_key=OPEN_AI_KEY, temperature=0)
populate_chain = LLMChain(
    llm=cypher_llm,
    prompt=PromptTemplate(
        input_variables=["input"],
        template=GENERATE_GRAPH_PROMPT
    )
)

class UpdateDBTool(BaseTool):
    name = "Update-DB"
    description = "Useful to update neo4j schema with the cypher query"

    def _run(self, query, run_manager = None):
        """
        Write the neo4j DB only if the input is in form of a neo4j query

        Args:
        query: any
        Returns:
        None
        """
        graph.query(query)
        graph.refresh_schema()


tools = [
    Tool(
        name="Search",
        func=cypher_chain.run,
        description="useful for query neo4j graph database to answer user questions"
    ),
    Tool(
        name="Cypher",
        func=populate_chain.run,
        description="useful for extracting a cypher schema out of text"
    ),
    UpdateDBTool()
]

agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
}

memory = ConversationBufferMemory(memory_key="memory", return_messages=True)


# This sets an Agent with 2 tools, one for retrieving from Cypher, the other
# for generating new knowledge with cypher queries
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs=agent_kwargs,
    memory=memory,
)


# response = ""
# while (response != "end"):
#     response = input("What do you want to ask the AI model? \n")
#     agent.run(response)


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chat/{input}")
async def call_chat(input):
    return {"response": agent.run(input), "graph": graph.schema}
