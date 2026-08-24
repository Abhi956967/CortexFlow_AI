import { useEffect, useState } from "react";
import { 
  Plus, 
  MessageSquare, 
  LogOut, 
  User, 
  PenSquare, 
  Menu, 
  X, 
  CoinsIcon, 
  Pin, 
  Archive, 
  Trash2, 
  Edit2, 
  MoreVertical, 
  Search, 
  Check 
} from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import api from "../utils/axios";
import { setUserData } from "../redux/user.slice";
import { 
  createConversation, 
  getConversations, 
  updateConversations, 
  pinConversation, 
  archiveConversation, 
  deleteConversation 
} from "../features/conversation.api";
import { 
  addConversation, 
  setConversations, 
  setSelectedConversation, 
  setConvTitle, 
  togglePinConversation, 
  toggleArchiveConversation, 
  deleteConversationFromState,
  setSearchQuery,
  setFilterTab
} from "../redux/conversation.slice";
import { getMessages } from "../features/message.api";
import { setArtifacts, setMessages } from "../redux/message.slice";
import BillingDrawer from "./BillingDrawer";
import ProfileModal from "./ProfileModal";
import AuthModal from "./AuthModal";

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [showBilling, setShowBilling] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showAuth, setShowAuth] = useState(false);

  const [activeMenuId, setActiveMenuId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");

  const { userData } = useSelector((state) => state.user);
  const { conversations, selectedConversation, searchQuery, filterTab } = useSelector((state) => state.conversation);
  const dispatch = useDispatch();

  const logout = async () => {
    try {
      await api.post("/api/auth/logout");
    } catch (error) {
      console.log(error);
    } finally {
      dispatch(setUserData(null));
    }
  };

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const data = await getConversations();
        dispatch(setConversations(data));
      } catch (error) {
        console.log(error);
      }
    };
    fetchConversations();
  }, [userData?.id, userData?._id, dispatch]);

  const handleCreateConversation = async () => {
    try {
      const newConv = await createConversation();
      dispatch(addConversation(newConv));
      dispatch(setSelectedConversation(newConv));
      dispatch(setMessages([]));
      dispatch(setArtifacts([]));
    } catch (e) {
      dispatch(setSelectedConversation(null));
      dispatch(setMessages([]));
      dispatch(setArtifacts([]));
    }
    setMobileOpen(false);
  };

  const handleSelectConversation = async (conversation) => {
    setMobileOpen(false);
    dispatch(setSelectedConversation(conversation));
    const messages = await getMessages(conversation._id || conversation.id);
    dispatch(setMessages(messages));
    dispatch(setArtifacts(messages.artifacts || []));
  };

  const handleTogglePin = async (e, chat) => {
    e.stopPropagation();
    setActiveMenuId(null);
    const convId = chat._id || chat.id;
    const newPinned = !chat.isPinned;
    dispatch(togglePinConversation({ conversationId: convId, isPinned: newPinned }));
    try {
      await pinConversation(convId, newPinned);
    } catch (err) {
      console.log(err);
    }
  };

  const handleToggleArchive = async (e, chat) => {
    e.stopPropagation();
    setActiveMenuId(null);
    const convId = chat._id || chat.id;
    const newArchived = !chat.isArchived;
    dispatch(toggleArchiveConversation({ conversationId: convId, isArchived: newArchived }));
    try {
      await archiveConversation(convId, newArchived);
    } catch (err) {
      console.log(err);
    }
  };

  const handleDelete = async (e, chat) => {
    e.stopPropagation();
    setActiveMenuId(null);
    const convId = chat._id || chat.id;
    if (confirm(`Delete conversation "${chat.title}"?`)) {
      dispatch(deleteConversationFromState(convId));
      try {
        await deleteConversation(convId);
      } catch (err) {
        console.log(err);
      }
    }
  };

  const handleStartRename = (e, chat) => {
    e.stopPropagation();
    setActiveMenuId(null);
    setEditingId(chat._id || chat.id);
    setEditingTitle(chat.title);
  };

  const handleSaveRename = async (e, chat) => {
    e.stopPropagation();
    const convId = chat._id || chat.id;
    if (editingTitle.trim()) {
      dispatch(setConvTitle({ conversationId: convId, title: editingTitle.trim() }));
      try {
        await updateConversations(convId, editingTitle.trim());
      } catch (err) {
        console.log(err);
      }
    }
    setEditingId(null);
  };

  // Filter conversations
  const filteredConversations = conversations.filter((c) => {
    const matchesSearch = !searchQuery || c.title.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;
    if (filterTab === "pinned") return c.isPinned;
    if (filterTab === "archived") return c.isArchived;
    if (filterTab === "recent") return !c.isArchived;
    return !c.isArchived; // default "all" excludes archived
  });

  const PanelIcon = () => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>
    </svg>
  );

  /* ── Collapsed Rail ── */
  const CollapsedRail = () => (
    <div className="hidden lg:flex flex-col items-center w-[56px] h-screen bg-[#0d0f14] border-r border-white/[0.06] py-4 gap-1 shrink-0">
      <button
        onClick={() => setCollapsed(false)}
        className="flex items-center justify-center w-9 h-9 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/[0.05] transition bg-transparent border-none cursor-pointer mb-1"
      >
        <PanelIcon />
      </button>

      <button
        onClick={handleCreateConversation}
        className="flex items-center justify-center w-9 h-9 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/[0.05] transition bg-transparent border-none cursor-pointer"
      >
        <Plus size={17} />
      </button>

      <div className="flex-1 flex flex-col items-center gap-1 overflow-y-auto w-full px-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden mt-1">
        {filteredConversations.map((chat) => {
          const isActive = (selectedConversation?._id || selectedConversation?.id) === (chat._id || chat.id);
          return (
            <button
              key={chat._id || chat.id}
              onClick={() => handleSelectConversation(chat)}
              title={chat.title}
              className={`flex items-center justify-center w-9 h-9 rounded-xl transition border-none cursor-pointer ${
                isActive ? "bg-indigo-500/15 text-indigo-400" : "bg-transparent text-slate-500 hover:bg-white/[0.05] hover:text-slate-300"
              }`}
            >
              <MessageSquare size={15} />
            </button>
          );
        })}
      </div>

      <div className="mt-auto">
        {userData ? (
          <button
            onClick={() => setShowProfile(true)}
            className="relative p-0 bg-transparent border-none cursor-pointer"
          >
            <img 
              src={userData.avatar || "https://api.dicebear.com/7.x/bottts/svg?seed=Cortex"} 
              alt={userData.name} 
              className="w-8 h-8 rounded-[8px] object-cover border-2 border-indigo-500/25 bg-[#171923]" 
            />
            <span className="absolute -bottom-px -right-px w-2 h-2 bg-emerald-500 rounded-full border-[1.5px] border-[#0d0f14] block" />
          </button>
        ) : (
          <button
            onClick={() => setShowAuth(true)}
            className="w-8 h-8 rounded-[8px] bg-indigo-600/20 text-indigo-400 flex items-center justify-center cursor-pointer border border-indigo-500/30"
          >
            <User size={14} />
          </button>
        )}
      </div>
    </div>
  );

  /* ── Full Sidebar Content ── */
  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3.5 border-b border-white/[0.06]">
        <button
          onClick={() => setCollapsed(true)}
          className="hidden lg:flex items-center justify-center w-7 h-7 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/[0.05] transition bg-transparent border-none cursor-pointer"
        >
          <PanelIcon />
        </button>

        <button
          onClick={() => setMobileOpen(false)}
          className="lg:hidden flex items-center justify-center w-7 h-7 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/[0.05] transition bg-transparent border-none cursor-pointer"
        >
          <X size={15} />
        </button>

        <span className="text-[15px] font-bold text-slate-100 tracking-tight flex-1 flex items-center gap-1.5">
          <span className="text-indigo-400">⚡</span> CortexAI
        </span>

        <span className="text-[10px] font-medium text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full uppercase">
          {userData?.plan ?? "free"}
        </span>

        <button
          onClick={handleCreateConversation}
          title="New Chat"
          className="flex items-center justify-center w-7 h-7 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition bg-transparent border-none cursor-pointer"
        >
          <PenSquare size={14} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-3.5 pt-3 pb-1">
        <button
          onClick={handleCreateConversation}
          className="w-full flex items-center justify-center gap-2 text-xs font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl py-2.5 border-none cursor-pointer hover:opacity-90 transition shadow-md shadow-indigo-500/20"
        >
          <Plus size={15} />
          New Chat
        </button>
      </div>

      {/* Live Search Bar */}
      <div className="px-3.5 pt-2 pb-1">
        <div className="relative flex items-center">
          <Search size={13} className="absolute left-3 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => dispatch(setSearchQuery(e.target.value))}
            placeholder="Search chats..."
            className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 outline-none focus:border-indigo-500/40"
          />
          {searchQuery && (
            <button
              onClick={() => dispatch(setSearchQuery(""))}
              className="absolute right-2.5 text-slate-500 hover:text-white"
            >
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 px-3.5 py-1.5 text-[11px] font-medium border-b border-white/[0.04]">
        {[
          { id: "all", label: "All" },
          { id: "pinned", label: "Pinned" },
          { id: "archived", label: "Archived" }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => dispatch(setFilterTab(tab.id))}
            className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
              filterTab === tab.id
                ? "bg-white/[0.08] text-indigo-300 font-semibold"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-2.5 py-2 space-y-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {filteredConversations.length === 0 ? (
          <div className="px-3 py-8 text-center text-xs text-slate-500">
            {searchQuery ? "No matching conversations" : "No chats in this folder"}
          </div>
        ) : (
          filteredConversations.map((chat) => {
            const convId = chat._id || chat.id;
            const isActive = (selectedConversation?._id || selectedConversation?.id) === convId;
            const isEditingThis = editingId === convId;

            return (
              <div
                key={convId}
                onClick={() => !isEditingThis && handleSelectConversation(chat)}
                className={`group relative flex items-center justify-between px-3 py-2 rounded-xl text-xs transition cursor-pointer border ${
                  isActive
                    ? "bg-indigo-500/12 border-indigo-500/25 text-white font-medium shadow-sm"
                    : "bg-transparent border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                }`}
              >
                {/* Left title / edit box */}
                <div className="flex items-center gap-2 min-w-0 flex-1 pr-1">
                  {chat.isPinned ? (
                    <Pin size={13} className="text-indigo-400 shrink-0" />
                  ) : (
                    <MessageSquare size={13} className={isActive ? "text-indigo-400 shrink-0" : "text-slate-500 shrink-0"} />
                  )}

                  {isEditingThis ? (
                    <div className="flex items-center gap-1 flex-1" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        autoFocus
                        onKeyDown={(e) => e.key === "Enter" && handleSaveRename(e, chat)}
                        className="w-full bg-black/40 border border-indigo-500/50 rounded px-1.5 py-0.5 text-xs text-white outline-none"
                      />
                      <button
                        onClick={(e) => handleSaveRename(e, chat)}
                        className="p-1 text-emerald-400 hover:text-emerald-300"
                      >
                        <Check size={13} />
                      </button>
                    </div>
                  ) : (
                    <span className="truncate flex-1">{chat.title}</span>
                  )}
                </div>

                {/* 3-dots Menu Button */}
                {!isEditingThis && (
                  <div className="relative shrink-0" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setActiveMenuId(activeMenuId === convId ? null : convId)}
                      className={`p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-white/10 transition ${
                        activeMenuId === convId ? "opacity-100 bg-white/10" : ""
                      }`}
                    >
                      <MoreVertical size={13} className="text-slate-400" />
                    </button>

                    {/* Dropdown Menu */}
                    {activeMenuId === convId && (
                      <div className="absolute right-0 top-6 w-36 bg-[#151822] border border-white/[0.09] rounded-xl p-1 shadow-2xl z-50 space-y-0.5">
                        <button
                          onClick={(e) => handleTogglePin(e, chat)}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-slate-300 hover:text-white hover:bg-white/[0.06] rounded-lg transition text-left"
                        >
                          <Pin size={12} className="text-indigo-400" />
                          {chat.isPinned ? "Unpin Chat" : "Pin Chat"}
                        </button>
                        <button
                          onClick={(e) => handleStartRename(e, chat)}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-slate-300 hover:text-white hover:bg-white/[0.06] rounded-lg transition text-left"
                        >
                          <Edit2 size={12} className="text-amber-400" />
                          Rename
                        </button>
                        <button
                          onClick={(e) => handleToggleArchive(e, chat)}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-slate-300 hover:text-white hover:bg-white/[0.06] rounded-lg transition text-left"
                        >
                          <Archive size={12} className="text-blue-400" />
                          {chat.isArchived ? "Unarchive" : "Archive"}
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, chat)}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-rose-400 hover:bg-rose-500/10 rounded-lg transition text-left"
                        >
                          <Trash2 size={12} />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Divider */}
      <div className="mx-2.5 h-px bg-white/[0.06]" />

      {/* User Profile Footer */}
      <div className="px-3.5 py-3">
        {userData ? (
          <div
            onClick={() => setShowProfile(true)}
            className="flex items-center gap-2.5 cursor-pointer rounded-xl px-3 py-2 hover:bg-white/[0.05] transition"
          >
            <div className="relative shrink-0">
              <img
                src={userData.avatar || "https://api.dicebear.com/7.x/bottts/svg?seed=Cortex"}
                alt={userData.name}
                className="w-8 h-8 rounded-[10px] object-cover border-2 border-indigo-500/25 bg-[#171923]"
                onError={() => setImageError(true)}
              />
              <span className="absolute -bottom-px -right-px w-2 h-2 bg-emerald-500 rounded-full border-2 border-[#0d0f14] block" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold text-slate-100 truncate">{userData.name}</p>
              <p className="text-[10.5px] text-slate-500 mt-px">{userData.plan || "Free Plan"} • {userData.credits || 100} cr</p>
            </div>
            <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setShowBilling(true)}
                title="Upgrade Plan / Billing"
                className="p-1 text-yellow-500 hover:text-yellow-400 transition"
              >
                <CoinsIcon size={15}/>
              </button>
              <button
                onClick={logout}
                title="Log Out"
                className="p-1 text-slate-500 hover:text-rose-400 transition"
              >
                <LogOut size={14} />
              </button>
            </div>
          </div>
        ) : (
          <div className="px-1">
            <button
              onClick={() => setShowAuth(true)}
              className="w-full flex items-center justify-center gap-2 text-xs font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 rounded-xl py-2.5 cursor-pointer hover:opacity-90 shadow-md shadow-indigo-500/25 transition"
            >
              Sign In / Register
            </button>
          </div>
        )}
      </div>
    </div>
  );

  if (collapsed) return <CollapsedRail />;

  return (
    <>
      {/* Mobile Hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-3 left-4 z-50 flex items-center justify-center w-8 h-8 rounded-lg bg-[#0d0f14] border border-white/[0.08] text-slate-400 hover:text-slate-200 transition"
      >
        <Menu size={16} />
      </button>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        />
      )}

      {/* Sidebar Panel */}
      <div
        className={`fixed lg:static inset-y-0 left-0 z-50 w-[270px] h-screen shrink-0 bg-[#0d0f14] border-r border-white/[0.06] transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <SidebarContent />
      </div>

      <BillingDrawer
        open={showBilling}
        onClose={() => setShowBilling(false)}
      />

      <ProfileModal
        isOpen={showProfile}
        onClose={() => setShowProfile(false)}
      />

      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
      />
    </>
  );
}