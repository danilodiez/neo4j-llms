import { OpenAI } from "langchain/llms/openai";
import { PromptTemplate } from "langchain/prompts";
import { SimpleSequentialChain, LLMChain } from "langchain/chains";
import { read } from "../../lib/neo4j";

const OPENAI_KEY = process.env.PUBLIC_OPEN_AI_KEY;

export default async function Home() {
  const res = await read("MATCH p=()-[:Has]->() RETURN p LIMIT 25");
  const llm = new OpenAI({
    openAIApiKey: OPENAI_KEY,
  });

  const template = `You are an neo4j expert which goal is to answer a given {question}
  to the user, but for this, you FIRST have to 
  take that question and recognise the entities and
  relationships between them. Return those entities and relationships you
  have as neo4j Cypher queries in the form :
  cypher:
  `;
  const prompt = new PromptTemplate({
    template,
    inputVariables: ["question"],
  });

  const questionChain = new LLMChain({ llm, prompt });

  // This is an LLM to query neo4j
  const cypherLLM = new OpenAI({
    openAIApiKey: OPENAI_KEY,
  });
  const reviewTemplate = `You are an expert in neo4j, your
  task is to take the {cypher} and see if you have that info on your knowledge
  IF NOT, you have to ask for feedback to create new relationships and entities
  `;
  const reviewerPromptTemplate = new PromptTemplate({
    template: reviewTemplate,
    inputVariables: ["cypher"],
  });
  const reviewChain = new LLMChain({
  llm: cypherLLM,
  prompt: reviewerPromptTemplate,
});
  const generalChain = new SimpleSequentialChain({
    chains: [questionChain, reviewChain],
    verbose: true,
  });

  const review = await generalChain.run("How many dogs does Messi have?");
  console.log({ review });
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24"></main>
  );
}

