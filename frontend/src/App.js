import React, { useEffect, useState } from "react";
import io from "socket.io-client";

const socket = io(process.env.REACT_APP_WS_URL || "ws://localhost:8000");

const GameBoard = ({ gameState }) => (
  <div>
    <pre>{JSON.stringify(gameState, null, 2)}</pre>
  </div>
);

const App = () => {
  const [gameState, setGameState] = useState(null);

  useEffect(() => {
    socket.on("message", (data) => {
      setGameState(data);
    });

    socket.on("connect_error", (err) => {
      console.error("Connection error:", err);
    });

    return () => {
      socket.off("message");
      socket.off("connect_error");
    };
  }, []);

  const playCard = (card, theater) => {
    socket.emit("play_card", { action: "play_card", card, theater });
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Air, Land & Sea</h1>
      <button style={{ margin: "10px" }} onClick={() => playCard("Fighter Jet", "Air")}>
        Play Fighter Jet
      </button>
      <GameBoard gameState={gameState} />
    </div>
  );
};

export default App;
