import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FiExternalLink, FiX } from "react-icons/fi";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { 
  Copy, 
  Check, 
  Volume2, 
  VolumeX, 
  ThumbsUp, 
  ThumbsDown, 
  RotateCw, 
  Edit3, 
  Sparkles, 
  User 
} from "lucide-react";
import { submitMessageFeedback } from "../features/conversation.api";

function MessageBubble({ 
  role, 
  content = "", 
  images = [], 
  messageId, 
  feedback: initialFeedback,
  onRegenerate, 
  onEdit 
}) {
  const isUser = role === "user";
  const [lightboxSrc, setLightboxSrc] = useState(null);
  const [copiedText, setCopiedText] = useState(false);
  const [copiedCode, setCopiedCode] = useState("");
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [feedback, setFeedback] = useState(initialFeedback || null);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(content || "");

  const utteranceRef = useRef(null);

  // If assistant message has no content yet, render a sleek typing indicator
  const hasContent = content && content.trim().length > 0;

  // Copy full message text
  const handleCopyText = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  // Copy code block
  const copyCode = async (code) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(""), 2000);
  };

  // Text to Speech Read Aloud
  const toggleSpeech = () => {
    if (!('speechSynthesis' in window)) {
      alert("Text-to-Speech is not supported in this browser.");
      return;
    }

    if (isPlayingAudio) {
      window.speechSynthesis.cancel();
      setIsPlayingAudio(false);
    } else {
      window.speechSynthesis.cancel();
      const cleanText = (content || "").replace(/```[\s\S]*?```/g, "").replace(/[#*_`]/g, "");
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      setIsPlayingAudio(true);
    }
  };

  // Handle Like / Dislike
  const handleFeedback = async (rating) => {
    const newRating = feedback === rating ? null : rating;
    setFeedback(newRating);
    if (messageId) {
      try {
        await submitMessageFeedback(messageId, newRating || "none");
      } catch (e) {
        console.log("Feedback error:", e);
      }
    }
  };

  const handleSaveEdit = () => {
    if (editText.trim() && onEdit) {
      onEdit(editText.trim());
      setIsEditing(false);
    }
  };

  const markdown = (content || "")
    .replace(/```review/gi, "```")
    .replace(/```text/gi, "```")
    .replace(/```[a-zA-Z0-9_-]+\s+id="[^"]*"/g, "```");

  return (
    <div className={`group flex flex-col ${isUser ? "items-end" : "items-start"} mb-4`}>
      <div className="flex items-start gap-2.5 max-w-[92vw] md:max-w-[78%]">
        
        {/* Assistant Avatar Icon */}
        {!isUser && (
          <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center shrink-0 mt-1 shadow-sm shadow-indigo-500/20">
            <Sparkles size={14} className="text-indigo-400" />
          </div>
        )}

        <div
          className={`relative px-4 py-3 rounded-2xl break-words overflow-hidden leading-relaxed text-[13.5px] ${
            isUser
              ? "bg-gradient-to-br from-indigo-500 to-violet-700 text-white rounded-tr-sm shadow-md shadow-indigo-600/20"
              : "bg-[#14161f] border border-white/[0.08] text-slate-200 rounded-tl-sm shadow-md shadow-black/30"
          }`}
        >
          {/* User Edit Mode */}
          {isEditing ? (
            <div className="space-y-2 min-w-[260px]">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full bg-black/30 border border-white/20 rounded-xl p-2.5 text-xs text-white outline-none resize-none"
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-3 py-1 bg-white text-indigo-900 rounded-lg text-xs font-semibold hover:bg-slate-200"
                >
                  Save & Resend
                </button>
              </div>
            </div>
          ) : !hasContent && !isUser ? (
            <div className="flex items-center gap-2 py-1 px-1">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          ) : (
            <>
              {/* Image Previews */}
              {images.length > 0 && (
                <div className="flex flex-wrap gap-2.5 mb-3">
                  {images.map((img, i) => (
                    <img
                      key={i}
                      src={img}
                      loading="lazy"
                      onClick={() => setLightboxSrc(img)}
                      onError={(e) => e.currentTarget.remove()}
                      className="w-36 h-28 rounded-xl object-cover border border-white/10 cursor-zoom-in hover:opacity-90 transition shadow-md"
                    />
                  ))}
                </div>
              )}

              {/* Markdown Content */}
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold mt-4 mb-2 text-white">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold mt-3 mb-2 text-indigo-200">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-semibold mt-2 mb-1 text-indigo-300">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-2.5 whitespace-pre-wrap break-words leading-relaxed">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-5 space-y-1 my-2 text-slate-300">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-5 space-y-1 my-2 text-slate-300">{children}</ol>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-3 rounded-xl border border-white/10 bg-white/[0.02]">
                      <table className="min-w-full text-xs">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border-b border-white/10 bg-white/5 px-3 py-2 text-left font-semibold text-slate-200">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border-b border-white/5 px-3 py-2 text-slate-300">{children}</td>
                  ),
                  a: ({ href, children }) => {
                    let linkHref = href || "";
                    if (linkHref.includes("localhost:8000/storage/")) {
                      const backendBase = import.meta.env.VITE_SERVER_URL || "https://cortexflow-ai-mrxb.onrender.com";
                      linkHref = linkHref.replace("http://localhost:8000", backendBase.replace(/\/$/, ""));
                    }
                    return (
                      <a
                        href={linkHref}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 underline inline-flex items-center gap-1 font-medium hover:text-indigo-300"
                      >
                        {children}
                        <FiExternalLink size={11} />
                      </a>
                    );
                  },
                  code({ className, children }) {
                    const value = String(children).replace(/^\s*```[^\n]*\n/, "").replace(/\n```\s*$/, "").trim();
                    if (!className) {
                      return (
                        <code className="px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-300 font-mono text-[12px] border border-indigo-500/20">
                          {value}
                        </code>
                      );
                    }
                    const language = className.replace("language-", "");
                    return (
                      <div className="my-3 overflow-hidden rounded-xl border border-white/10 bg-[#0d1017] shadow-lg">
                        <div className="flex items-center justify-between bg-[#151922] border-b border-white/10 px-3.5 py-1.5">
                          <span className="uppercase text-[11px] font-semibold text-indigo-400 tracking-wider">
                            {language}
                          </span>
                          <button
                            onClick={() => copyCode(value)}
                            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white transition"
                          >
                            {copiedCode === value ? (
                              <>
                                <Check size={13} className="text-emerald-400" />
                                <span className="text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={13} />
                                <span>Copy Code</span>
                              </>
                            )}
                          </button>
                        </div>
                        <SyntaxHighlighter
                          language={language}
                          style={oneDark}
                          wrapLongLines
                          showLineNumbers
                          customStyle={{
                            margin: 0,
                            padding: "14px",
                            background: "#0d1017",
                            fontSize: "12.5px"
                          }}
                        >
                          {value}
                        </SyntaxHighlighter>
                      </div>
                    );
                  }
                }}
              >
                {markdown}
              </ReactMarkdown>
            </>
          )}
        </div>
      </div>

      {/* Action Toolbar Below Message */}
      {!isEditing && hasContent && (
        <div className={`flex items-center gap-1 mt-1.5 px-2 ${isUser ? "justify-end" : "justify-start pl-9"} opacity-60 hover:opacity-100 transition-opacity`}>
          {/* Copy Message */}
          <button
            onClick={handleCopyText}
            title="Copy Message"
            className="p-1 rounded-lg hover:bg-white/[0.06] text-slate-400 hover:text-slate-200 transition cursor-pointer"
          >
            {copiedText ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
          </button>

          {/* Text-to-Speech */}
          {!isUser && (
            <button
              onClick={toggleSpeech}
              title={isPlayingAudio ? "Stop Reading" : "Read Aloud (Voice Output)"}
              className={`p-1 rounded-lg hover:bg-white/[0.06] transition cursor-pointer ${
                isPlayingAudio ? "text-indigo-400 bg-indigo-500/10" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {isPlayingAudio ? <VolumeX size={13} /> : <Volume2 size={13} />}
            </button>
          )}

          {/* Like / Dislike */}
          {!isUser && (
            <>
              <button
                onClick={() => handleFeedback("like")}
                title="Good response"
                className={`p-1 rounded-lg hover:bg-white/[0.06] transition cursor-pointer ${
                  feedback === "like" ? "text-emerald-400 bg-emerald-500/10" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <ThumbsUp size={13} />
              </button>
              <button
                onClick={() => handleFeedback("dislike")}
                title="Poor response"
                className={`p-1 rounded-lg hover:bg-white/[0.06] transition cursor-pointer ${
                  feedback === "dislike" ? "text-rose-400 bg-rose-500/10" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <ThumbsDown size={13} />
              </button>
            </>
          )}

          {/* Regenerate Response */}
          {!isUser && onRegenerate && (
            <button
              onClick={onRegenerate}
              title="Regenerate response"
              className="p-1 rounded-lg hover:bg-white/[0.06] text-slate-400 hover:text-slate-200 transition cursor-pointer"
            >
              <RotateCw size={13} />
            </button>
          )}

          {/* Edit User Message */}
          {isUser && onEdit && (
            <button
              onClick={() => setIsEditing(true)}
              title="Edit Prompt"
              className="p-1 rounded-lg hover:bg-white/[0.06] text-slate-400 hover:text-slate-200 transition cursor-pointer"
            >
              <Edit3 size={13} />
            </button>
          )}
        </div>
      )}

      {/* Image Lightbox Modal */}
      {lightboxSrc && (
        <div
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-6"
          onClick={() => setLightboxSrc(null)}
        >
          <button
            type="button"
            onClick={() => setLightboxSrc(null)}
            className="absolute top-5 right-5 text-white/80 hover:text-white bg-white/10 rounded-full p-2.5 cursor-pointer"
          >
            <FiX size={20} />
          </button>
          <img
            src={lightboxSrc}
            onClick={(e) => e.stopPropagation()}
            className="max-w-[90vw] max-h-[85vh] rounded-2xl border border-white/10 shadow-2xl object-contain"
          />
        </div>
      )}
    </div>
  );
}

export default MessageBubble;