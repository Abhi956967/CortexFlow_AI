import axios from "axios";

// Default to live Render backend if VITE_SERVER_URL is not explicitly set in production
const defaultBaseUrl = typeof window !== "undefined" && window.location.hostname !== "localhost"
  ? "https://cortexflow-ai-mrxb.onrender.com"
  : "http://localhost:8000";

const api = axios.create({
  baseURL: import.meta.env.VITE_SERVER_URL || defaultBaseUrl,
  withCredentials: true
});

export default api;