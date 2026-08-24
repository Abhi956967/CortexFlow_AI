import { useState, useEffect, useRef } from "react";
import { 
  Send, 
  Paperclip, 
  Square, 
  Zap, 
  MessageSquare, 
  Code2, 
  Presentation, 
  Image as ImageIcon, 
  Globe, 
  FileText, 
  BarChart3, 
  Users, 
  Database, 
  X, 
  Mic, 
  MicOff 
} from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { addMessage, updateLastAssistantMessage, setArtifacts, setIsLoading, setStreamingText } from "../redux/message.slice";
import { streamPrompt } from "../features/agent.api";
import { createConversation, updateConversations } from "../features/conversation.api";
import { addConversation, setConvTitle, setSelectedConversation } from "../redux/conversation.slice";

export default function ChatInput({ setBanner }) {
  const [selectedAgent, setSelectedAgent] = useState("auto");
  const [value, setValue] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const recognitionRef = useRef(null);
  const fileRef = useRef(null);
  const abortControllerRef = useRef(null);

  const dispatch = useDispatch();
  const { selectedConversation } = useSelector((state) => state.conversation);
  const { isLoading } = useSelector((state) => state.message);

  const placeholders = {
    auto: "Ask CortexAI anything (Auto-routes to best AI agent)...",
    chat: "Chat with conversational AI...",
    coding: "Describe the app, script, or component to code...",
    pdf: "Generate an executive PDF document about...",
    ppt: "Create an 8-slide PowerPoint presentation on...",
    image: "Describe the image you want to generate...",
    search: "Search live web data, weather, news, and facts...",
    data_analysis: "Upload CSV/Excel or describe data to analyze...",
    agents_team: "Assign task to Autonomous Multi-Agent Swarm...",
    pdf_rag: "Upload document to chat and retrieve citations..."
  };

  const agents = [
    { id: "auto", icon: Zap, label: "Auto" },
    { id: "chat", icon: MessageSquare, label: "Chat" },
    { id: "coding", icon: Code2, label: "Coding" },
    { id: "pdf", icon: FileText, label: "PDF" },
    { id: "ppt", icon: Presentation, label: "PPT" },
    { id: "image", icon: ImageIcon, label: "Image" },
    { id: "search", icon: Globe, label: "Search" },
    { id: "data_analysis", icon: BarChart3, label: "Data" },
    { id: "agents_team", icon: Users, label: "Agents" },
    { id: "pdf_rag", icon: Database, label: "RAG" }
  ];

  // Speech to Text Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setValue(transcript);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  const toggleMic = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    dispatch(setIsLoading(false));
  };

  const handleSend = async () => {
    const prompt = value.trim();
    if (!prompt) return;

    dispatch(setIsLoading(true));
    dispatch(setStreamingText(""));

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      let conversation = selectedConversation;

      if (!conversation) {
        const newConversation = await createConversation();
        dispatch(addConversation(newConversation));
        dispatch(setSelectedConversation(newConversation));
        conversation = newConversation;
      }

      if (conversation.title === "New Chat") {
        const generatedTitle = prompt.slice(0, 36);
        await updateConversations(conversation._id || conversation.id, generatedTitle);
        dispatch(setConvTitle({ conversationId: conversation._id || conversation.id, title: generatedTitle }));
      }

      // Add user message
      dispatch(addMessage({ role: "user", content: prompt }));
      setValue("");

      const formData = new FormData();
      formData.append("conversationId", conversation._id || conversation.id);
      formData.append("prompt", prompt);
      formData.append("agent", selectedAgent);

      if (selectedFile) {
        formData.append("file", selectedFile);
      }
      setSelectedFile(null);

      let assistantMessageAdded = false;

      await streamPrompt(formData, {
        signal: abortController.signal,
        onChunk: (chunk, full) => {
          if (!assistantMessageAdded) {
            assistantMessageAdded = true;
            dispatch(addMessage({ role: "assistant", content: full, images: [], artifacts: [] }));
          } else {
            dispatch(updateLastAssistantMessage({ content: full }));
          }
        },
        onDone: (doneEvent) => {
          if (!assistantMessageAdded) {
            dispatch(addMessage({
              role: "assistant",
              content: doneEvent.answer,
              images: doneEvent.images || [],
              artifacts: doneEvent.artifacts || []
            }));
          } else {
            dispatch(updateLastAssistantMessage({
              content: doneEvent.answer,
              images: doneEvent.images || [],
              artifacts: doneEvent.artifacts || []
            }));
          }
          if (doneEvent.artifacts && doneEvent.artifacts.length > 0) {
            dispatch(setArtifacts(doneEvent.artifacts));
          }
          dispatch(setIsLoading(false));
        },
        onError: (err) => {
          if (!assistantMessageAdded) {
            dispatch(addMessage({ role: "assistant", content: `⚠️ Error: ${err}`, images: [], artifacts: [] }));
          } else {
            dispatch(updateLastAssistantMessage({ content: `⚠️ Error: ${err}` }));
          }
          dispatch(setIsLoading(false));
        }
      });
    } catch (error) {
      if (error.name !== "AbortError") {
        setBanner?.({
          open: true,
          title: error.response?.data?.title || "Something went wrong",
          message: error.response?.data?.message || "Please try again."
        });
      }
    } finally {
      dispatch(setIsLoading(false));
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) {
        handleSend();
      }
    }
  };

  return (
    <div className="w-full overflow-hidden px-3 md:px-5 py-3.5 border-t border-white/[0.06] bg-[#0d0f14]">
      <div className="flex flex-col gap-2 bg-[#12141c] border border-white/[0.08] rounded-2xl px-4 pt-3 pb-3 shadow-lg shadow-black/40">
        
        {/* Agent Modes Pill Carousel */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {agents.map((agent) => {
            const Icon = agent.icon;
            const isActive = selectedAgent === agent.id;
            return (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all cursor-pointer ${
                  isActive
                    ? "bg-gradient-to-r from-indigo-500 to-violet-600 text-white border-transparent shadow-[0_1px_8px_rgba(99,102,241,.35)]"
                    : "bg-white/[0.03] text-slate-400 border-white/[0.06] hover:bg-white/[0.07] hover:text-slate-200"
                }`}
              >
                <Icon size={13} className={isActive ? "text-white" : "text-slate-400"} />
                {agent.label}
              </button>
            );
          })}
        </div>

        {/* Selected File Badge */}
        {selectedFile && (
          <div className="my-1">
            <div className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-1.5">
              <FileText size={15} className="text-indigo-400" />
              <div>
                <p className="text-xs font-medium text-white max-w-[200px] truncate">{selectedFile.name}</p>
                <p className="text-[10px] text-slate-400">{Math.ceil(selectedFile.size / 1024)} KB</p>
              </div>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  if (fileRef.current) fileRef.current.value = "";
                }}
                className="ml-1 text-slate-500 hover:text-white"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Textarea */}
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholders[selectedAgent]}
          rows={2}
          disabled={isLoading}
          className="w-full bg-transparent outline-none resize-none text-[14px] text-slate-200 placeholder:text-slate-500 leading-relaxed [scrollbar-width:none] [&::-webkit-scrollbar]:hidden disabled:opacity-60"
        />

        {/* Bottom row — Controls */}
        <div className="flex items-center justify-between pt-1">
          {/* Left Controls — Attachment & Mic */}
          <div className="flex items-center gap-1">
            <input
              ref={fileRef}
              type="file"
              hidden
              accept=".pdf,.csv,.tsv,.xlsx,.docx,.txt,image/*"
              onChange={(e) => {
                const file = e.target.files[0];
                if (file) setSelectedFile(file);
              }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              title="Attach File (.pdf, .csv, .xlsx, .docx, images)"
              className="flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] border border-transparent hover:border-white/[0.06] transition cursor-pointer"
            >
              <Paperclip size={15} />
            </button>

            <button
              onClick={toggleMic}
              title={isListening ? "Stop Listening" : "Voice Input (Speech-to-Text)"}
              className={`flex items-center justify-center w-8 h-8 rounded-lg transition cursor-pointer ${
                isListening ? "bg-rose-500 text-white animate-pulse" : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]"
              }`}
            >
              {isListening ? <MicOff size={15} /> : <Mic size={15} />}
            </button>
          </div>

          {/* Right Controls — Send or Stop */}
          {isLoading ? (
            <button
              onClick={handleStop}
              title="Stop Generation"
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-300 hover:bg-rose-500/30 text-xs font-semibold transition cursor-pointer shadow-md"
            >
              <Square size={12} fill="currentColor" />
              Stop
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!value.trim()}
              title="Send Message"
              className={`flex items-center justify-center w-8 h-8 rounded-xl border-none cursor-pointer transition ${
                value.trim()
                  ? "bg-gradient-to-br from-indigo-500 to-violet-700 hover:from-indigo-400 hover:to-violet-600 text-white shadow-md shadow-indigo-500/25"
                  : "bg-white/[0.05] text-slate-600 cursor-not-allowed"
              }`}
            >
              <Send size={14} />
            </button>
          )}
        </div>
      </div>

      <p className="text-center text-[10.5px] text-slate-500 mt-2">
        CortexAI can make mistakes. Verify critical facts and code.
      </p>
    </div>
  );
}