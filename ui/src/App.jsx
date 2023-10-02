import { useState } from "react";
import { OpenAI } from "langchain/llms/openai";
import "./App.css";
const OPENAI_KEY = import.meta.env.VITE_OPEN_AI_KEY;
import { PromptTemplate } from "langchain/prompts";
import { useChat } from "ai/react";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  // const { messages, input, handleInputChange, handleSubmit } = useChat();
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessages(prev => [...prev, input])
    const response = await fetch('http://127.0.0.1:8000/chat/' + input)
    const data = await response.json()
    setMessages(prev => [...prev, data.response])
    setInput("");
  };

  return (
    <div>
    {messages.map((msg, index) => (
        <div key={index}>
          {index % 2 === 0 ? "User: " : "AI: "}{msg}
        </div>
      ))}
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          placeholder="Say something..."
          onChange={(e) => setInput(e.target.value)}
        />
      </form>
    </div>
  );
}

export default App;
