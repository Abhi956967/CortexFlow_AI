import api from "../utils/axios";

export const sendPrompt = async (formData) => {
  const { data } = await api.post("/api/agent/chat", formData);
  return data;
};

export const streamPrompt = async (formData, { onChunk, onDone, onError, signal }) => {
  const baseURL = api.defaults.baseURL || (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://cortexflow-ai-mrxb.onrender.com"
    : "http://localhost:8000");

  try {
    const response = await fetch(`${baseURL}/api/agent/stream`, {
      method: "POST",
      body: formData,
      credentials: "include",
      signal
    });

    if (!response.ok) {
      throw new Error(`Server returned error status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const raw = line.replace("data: ", "").trim();
          if (raw) {
            try {
              const event = JSON.parse(raw);
              if (event.type === "chunk") {
                onChunk?.(event.text, event.full);
              } else if (event.type === "done") {
                onDone?.(event);
              } else if (event.type === "error") {
                onError?.(event.message);
              }
            } catch (err) {
              console.warn("Error parsing stream chunk:", err);
            }
          }
        }
      }
    }
  } catch (error) {
    if (error.name === "AbortError") {
      console.log("Generation aborted by user");
    } else {
      onError?.(error.message || "Streaming failed");
    }
  }
};