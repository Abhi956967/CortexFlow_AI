import api from "../utils/axios";

export const getConversations = async () => {
  const response = await api.get("/api/chat/get-conversations");
  return response.data;
};

export const updateConversations = async (conversationId, title) => {
  const response = await api.post("/api/chat/update-conversation", {
    conversationId,
    title
  });
  return response.data;
};

export const createConversation = async () => {
  const response = await api.post("/api/chat/create-conversation", {});
  return response.data;
};

export const pinConversation = async (conversationId, isPinned) => {
  const response = await api.post("/api/chat/pin-conversation", {
    conversationId,
    isPinned
  });
  return response.data;
};

export const archiveConversation = async (conversationId, isArchived) => {
  const response = await api.post("/api/chat/archive-conversation", {
    conversationId,
    isArchived
  });
  return response.data;
};

export const deleteConversation = async (conversationId) => {
  const response = await api.delete(`/api/chat/conversations/${conversationId}`);
  return response.data;
};

export const submitMessageFeedback = async (messageId, rating) => {
  const response = await api.post("/api/chat/feedback", {
    messageId,
    rating
  });
  return response.data;
};

export const exportChatHistory = async (conversationId, format = "markdown") => {
  const response = await api.get(`/api/chat/export/${conversationId}?format=${format}`, {
    responseType: "text"
  });
  return response.data;
};