import { useState } from "react";
import { Share2, Download, MessageSquare, Check, Copy, X, FileText } from "lucide-react";
import { useSelector } from "react-redux";
import { exportChatHistory } from "../features/conversation.api";

export default function Navbar() {
  const { selectedConversation } = useSelector((state) => state.conversation);
  const { messages } = useSelector((state) => state.message);

  const [showShareModal, setShowShareModal] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  const conversationId = selectedConversation?._id || selectedConversation?.id;

  const handleCopyShareLink = () => {
    const shareUrl = `${window.location.origin}/chat/${conversationId || "shared"}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleExport = async (format) => {
    setShowExportMenu(false);
    if (!conversationId) return;

    try {
      const data = await exportChatHistory(conversationId, format);
      const blob = new Blob([data], { type: format === "markdown" ? "text/markdown" : "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedConversation?.title || "conversation"}.${format === "markdown" ? "md" : "txt"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.log("Export failed:", e);
    }
  };

  return (
    <>
      <div className="h-14 flex items-center justify-between px-5 border-b border-white/[0.06] bg-[#0d0f14] shrink-0">
        {/* Left — chat title */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 shrink-0">
            <MessageSquare size={13} className="text-indigo-400" />
          </div>
          <h2 className="text-[14px] font-semibold text-slate-100 tracking-tight truncate max-w-[200px] sm:max-w-[320px]">
            {selectedConversation?.title || "New Chat"}
          </h2>
          <span className="hidden sm:inline-flex text-[10px] font-medium text-slate-500 bg-white/[0.04] border border-white/[0.06] px-2 py-0.5 rounded-full shrink-0">
            {messages.length} Messages
          </span>
        </div>

        {/* Right — Actions */}
        <div className="flex items-center gap-1.5 relative">
          {/* Export Button & Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              title="Export Conversation"
              className="flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition cursor-pointer"
            >
              <Download size={15} />
            </button>

            {showExportMenu && (
              <div className="absolute right-0 top-10 w-44 bg-[#14161f] border border-white/[0.08] rounded-xl p-1.5 shadow-xl shadow-black/50 z-40 space-y-1">
                <button
                  onClick={() => handleExport("markdown")}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/[0.05] rounded-lg transition text-left cursor-pointer"
                >
                  <FileText size={13} className="text-indigo-400" />
                  Export as Markdown (.md)
                </button>
                <button
                  onClick={() => handleExport("text")}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/[0.05] rounded-lg transition text-left cursor-pointer"
                >
                  <FileText size={13} className="text-violet-400" />
                  Export as Plain Text (.txt)
                </button>
              </div>
            )}
          </div>

          {/* Share Button */}
          <button
            onClick={() => setShowShareModal(true)}
            title="Share Conversation"
            className="flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition cursor-pointer"
          >
            <Share2 size={15} />
          </button>
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
          onClick={() => setShowShareModal(false)}
        >
          <div 
            className="relative w-full max-w-[400px] bg-[#11131a] border border-white/[0.09] rounded-2xl p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowShareModal(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-white p-1 rounded-lg"
            >
              <X size={16} />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center text-indigo-400">
                <Share2 size={18} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">Share Conversation</h3>
                <p className="text-xs text-slate-400">Anyone with the link can view this chat history.</p>
              </div>
            </div>

            <div className="flex items-center gap-2 bg-black/40 border border-white/[0.06] rounded-xl p-2 font-mono text-xs text-slate-300">
              <span className="truncate flex-1">
                {window.location.origin}/chat/{conversationId || "cortex_shared"}
              </span>
              <button
                onClick={handleCopyShareLink}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-sans text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shrink-0"
              >
                {copiedLink ? <Check size={13} /> : <Copy size={13} />}
                {copiedLink ? "Copied" : "Copy Link"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}