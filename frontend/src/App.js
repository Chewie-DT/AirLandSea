import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const socket = io("ws://localhost:8000");

const App = () => {
  const [gameState, setGameState] = useState(null);

  useEffect(() => {
    socket.on("message", (data) => {
      setGameState(data);
    });
  }, []);

  const playCard = (card, theater) => {
    socket.emit("play_card", { action: "play_card", card, theater });
  };

  return (
    <div>
      <h1>Air, Land & Sea</h1>
      <button onClick={() => playCard("Fighter Jet", "Air")}>Play Fighter Jet</button>
      <div>
        <pre>{JSON.stringify(gameState, null, 2)}</pre>
      </div>
    </div>
  );
};

export default App;
