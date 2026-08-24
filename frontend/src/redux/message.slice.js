import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  messages: [],
  isLoading: false,
  artifacts: [],
  streamingText: ""
};

export const messageSlice = createSlice({
  name: 'message',
  initialState,
  reducers: {
    setMessages: (state, action) => {
      state.messages = action.payload || [];
    },

    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },

    updateLastAssistantMessage: (state, action) => {
      const { content, images, artifacts } = action.payload;
      for (let i = state.messages.length - 1; i >= 0; i--) {
        if (state.messages[i].role === "assistant") {
          state.messages[i].content = content;
          if (images) state.messages[i].images = images;
          if (artifacts) state.messages[i].artifacts = artifacts;
          break;
        }
      }
    },

    updateMessageContent: (state, action) => {
      const { index, content } = action.payload;
      if (state.messages[index]) {
        state.messages[index].content = content;
      }
    },

    updateMessageFeedback: (state, action) => {
      const { index, feedback } = action.payload;
      if (state.messages[index]) {
        state.messages[index].feedback = feedback;
      }
    },

    setIsLoading: (state, action) => {
      state.isLoading = action.payload;
    },

    setArtifacts: (state, action) => {
      state.artifacts = action.payload || [];
    },

    setStreamingText: (state, action) => {
      state.streamingText = action.payload;
    }
  },
});

export const {
  setMessages,
  addMessage,
  updateLastAssistantMessage,
  updateMessageContent,
  updateMessageFeedback,
  setIsLoading,
  setArtifacts,
  setStreamingText
} = messageSlice.actions;

export default messageSlice.reducer;