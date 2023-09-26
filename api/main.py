from fastapi import FastAPI
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain, LLMChain
from langchain.graphs import Neo4jGraph
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.prompts import MessagesPlaceholder, PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI

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

cypher_chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(openai_api_key=OPEN_AI_KEY, temperature=0), graph=graph,
    verbose=True
)

GENERATE_GRAPH_PROMPT=''' You are a data scientist working for a company that is building a graph database. Your task is to extract information from user {input} and convert it into a graph database.
Provide a set of Nodes in the form [ENTITY_ID, TYPE, PROPERTIES] and a set of relationships in the form [ENTITY_ID_1, RELATIONSHIP, ENTITY_ID_2, PROPERTIES].
It is important that the ENTITY_ID_1 and ENTITY_ID_2 exists as nodes with a matching ENTITY_ID. If you can't pair a relationship with a pair of nodes don't add it.
When you find a node or relationship you want to add try to create a generic TYPE for it that  describes the entity you can also think of it as a label.
Return it in the form of a Cypher query for creating nodes and relationships
'''

cypher_llm = OpenAI(openai_api_key=OPEN_AI_KEY, temperature=0)
cypher_chain = LLMChain(
    llm=cypher_llm,
    prompt=PromptTemplate(
        input_variables=["input"],
        template=GENERATE_GRAPH_PROMPT)
)
# cypher_chain.run("Which Deparment has employees?")


tools = [
    Tool(
        name="Search",
        func=cypher_chain.run,
        description='''
         useful for query the ONLY neo4j graph database to answer user questions,
         if you don't have an answer ask to the user
        '''
    ),
    Tool(
        name="Cypher",
        func=cypher_chain.run,
        description="useful for extracting a cypher schema out of text"
    )
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

# agent.run("my name is Danilo")
# agent.run("Could you help me by answering how many sons does Leo Messi Have?")
# agent.run({
#     "input": "Convert to cypher: Leo Messi is a football player, and he is married with Antonella Rocuzzo",
# })

# start asking for the users input??
response = ""
while (response != "end"):
    response = input("What do you want to ask the AI model? \n")
    agent.run(response)

# app = FastAPI()


# @app.get("/")
# async def root():
#     return {"message": "Hello World"}
