import { useState } from "react";
import { OpenAI } from "langchain/llms/openai";
import "./App.css";
const OPENAI_KEY = import.meta.env.VITE_OPEN_AI_KEY;
import { PromptTemplate } from "langchain/prompts";

function App() {
  const [count, setCount] = useState(0);
  const llm = new OpenAI({
    openAIApiKey: OPENAI_KEY,
  });

  const prompt = PromptTemplate.fromTemplate(
    "What is a good name for a company that makes {product}?"
  );

  const formattedPrompt = async () =>
    await prompt.format({
      product: "colorful socks",
    });
  const getResult = async () => {
    const result = await llm.predict(
      "What would be a good company name for a company that makes colorful socks?"
    );

    console.log(result);
    return result;
  };
  getResult();

  return <>hola</>;
}

export default App;
