import { useState, useRef } from "react";
import "./App.css";
import ForceGraph2D from "react-force-graph-2d";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessages((prev) => [...prev, input]);
    const response = await fetch("http://127.0.0.1:8000/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: input }),
    });
    const data = await response.json();
    const { graph } = data;
    // data.graph = relationships[]
    let nodes = [];
    let links = [];

    let nodeNames = new Set();

    graph.forEach((entry) => {
      const nNode = entry["n"];
      const rNode = entry["r"][0];
      const mNode = entry["m"];

      // Extracting nodes
      [nNode, rNode, mNode].forEach((node) => {
        if (node.name && !nodeNames.has(node.name)) {
          nodes.push({
            id: node.name,
            name: node.name,
            val: node.department_id || 1, // Default to 1 if not present
          });
          nodeNames.add(node.name);
        }
      });

      // Extracting relationships
      if (nNode.name && mNode.name) {
        links.push({
          source: nNode.name,
          target: mNode.name,
          name: entry["r"][1],
        });
      }
    });

    const result = {
      nodes: nodes,
      links: links,
    };

    setGraphData(result);

    setMessages((prev) => [...prev, data.response]);
    setInput("");
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "40% 1fr",
        gap: "10px",
        width: "100vw",
      }}
    >
      <div style={{ overflowY: "scroll", maxHeight: "90%", overflowX: "hidden"}}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: "10px",
              padding: "10px",
              borderRadius: "5px",
              border:
                index % 2 === 0 ? "2px solid #03cdff" : "2px solid #13c144",
            }}
          >
            {index % 2 === 0 ? "User: " : "AI: "}
            {msg}
          </div>
        ))}
        <form onSubmit={handleSubmit}>
          <input
            style={{
              padding: "10px",
              marginRight: "10px",
              width: "100%",
              marginBottom: "20px",
            }}
            value={input}
            placeholder="Say something..."
            onChange={(e) => setInput(e.target.value)}
          />
          <button onClick={handleSubmit}>Enviar</button>
        </form>
      </div>
      <div>
        <ForceGraph2D
          width={800}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.25}
          graphData={graphData}
          linkLabel="name"
          backgroundColor="white"
        />
      </div>
    </div>
  );
}

export default App;
