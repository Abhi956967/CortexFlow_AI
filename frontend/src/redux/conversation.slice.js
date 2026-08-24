import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  conversations: [],
  selectedConversation: null,
  searchQuery: "",
  filterTab: "all" // "all" | "pinned" | "recent" | "archived"
};

export const conversationSlice = createSlice({
  name: 'conversation',
  initialState,
  reducers: {
    setConversations: (state, action) => {
      state.conversations = action.payload || [];
    },

    addConversation: (state, action) => {
      state.conversations.unshift(action.payload);
    },

    setSelectedConversation: (state, action) => {
      state.selectedConversation = action.payload;
    },

    setConvTitle: (state, action) => {
      const { conversationId, title } = action.payload;
      state.conversations = state.conversations.map((conv) =>
        (conv._id === conversationId || conv.id === conversationId)
          ? { ...conv, title }
          : conv
      );

      if (state.selectedConversation?._id === conversationId || state.selectedConversation?.id === conversationId) {
        state.selectedConversation = {
          ...state.selectedConversation,
          title
        };
      }
    },

    togglePinConversation: (state, action) => {
      const { conversationId, isPinned } = action.payload;
      state.conversations = state.conversations.map((c) =>
        (c._id === conversationId || c.id === conversationId)
          ? { ...c, isPinned }
          : c
      );
      if (state.selectedConversation?._id === conversationId || state.selectedConversation?.id === conversationId) {
        state.selectedConversation = { ...state.selectedConversation, isPinned };
      }
    },

    toggleArchiveConversation: (state, action) => {
      const { conversationId, isArchived } = action.payload;
      state.conversations = state.conversations.map((c) =>
        (c._id === conversationId || c.id === conversationId)
          ? { ...c, isArchived }
          : c
      );
      if (state.selectedConversation?._id === conversationId || state.selectedConversation?.id === conversationId) {
        state.selectedConversation = { ...state.selectedConversation, isArchived };
      }
    },

    deleteConversationFromState: (state, action) => {
      const conversationId = action.payload;
      state.conversations = state.conversations.filter(
        (c) => (c._id !== conversationId && c.id !== conversationId)
      );
      if (state.selectedConversation?._id === conversationId || state.selectedConversation?.id === conversationId) {
        state.selectedConversation = null;
      }
    },

    setSearchQuery: (state, action) => {
      state.searchQuery = action.payload;
    },

    setFilterTab: (state, action) => {
      state.filterTab = action.payload;
    }
  },
});

export const {
  setConversations,
  addConversation,
  setSelectedConversation,
  setConvTitle,
  togglePinConversation,
  toggleArchiveConversation,
  deleteConversationFromState,
  setSearchQuery,
  setFilterTab
} = conversationSlice.actions;

export default conversationSlice.reducer;