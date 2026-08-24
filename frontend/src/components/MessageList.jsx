import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";
import MessageBubble from "./MessageBubble";
import { getMessages } from "../features/message.api";
import { setArtifacts, setMessages, addMessage, setIsLoading, updateLastAssistantMessage } from "../redux/message.slice";
import { streamPrompt } from "../features/agent.api";

function NeuralPulse() {
  return (
    <div className="relative w-8 h-8 flex items-center justify-center shrink-0">
      {[0, 0.45, 0.9].map((delay, i) => (
        <motion.span
          key={i}
          className="absolute inset-0 rounded-full border border-indigo-400/30"
          initial={{ scale: 0.3, opacity: 0.55 }}
          animate={{ scale: 1.7, opacity: 0 }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            delay,
            ease: "easeOut",
          }}
        />
      ))}
      <motion.span
        className="w-2.5 h-2.5 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500"
        style={{ boxShadow: "0 0 14px rgba(99,102,241,0.6)" }}
        animate={{ scale: [1, 1.25, 1] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}

const THINKING_LABELS = ["Thinking...", "Analyzing context...", "Synthesizing response...", "Formulating output..."];

function GeneratingIndicator() {
  const [labelIndex, setLabelIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setLabelIndex((prev) => (prev + 1) % THINKING_LABELS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  const label = THINKING_LABELS[labelIndex];

  return (
    <div className="flex items-center gap-3 max-w-[72%] py-1 pl-1">
      <NeuralPulse />
      <div className="flex overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={label}
            className="flex"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <span className="text-[13px] font-medium tracking-wide text-slate-400">
              {label}
            </span>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function MessageList() {
  const bottomRef = useRef(null);
  const { messages, isLoading } = useSelector((state) => state.message);
  const { selectedConversation } = useSelector((state) => state.conversation);
  const dispatch = useDispatch();

  useEffect(() => {
    requestAnimationFrame(() => {
      bottomRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    });
  }, [messages.length, isLoading]);

  useEffect(() => {
    if (!selectedConversation || selectedConversation.title === "New Chat") return;
    const fetchChatMessages = async () => {
      try {
        const data = await getMessages(selectedConversation._id || selectedConversation.id);
        dispatch(setMessages(data));
        const latestArtifactMessage = [...data].reverse().find(
          (msg) => msg.artifacts && msg.artifacts.length > 0
        );
        if (latestArtifactMessage) {
          dispatch(setArtifacts(latestArtifactMessage.artifacts));
        }
      } catch (err) {
        console.log("Error fetching messages:", err);
      }
    };
    fetchChatMessages();
  }, [selectedConversation?._id, selectedConversation?.id, dispatch]);

  const handleRegenerate = async () => {
    if (messages.length < 2 || isLoading) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUserMsg) return;

    dispatch(setIsLoading(true));
    dispatch(addMessage({ role: "assistant", content: "", images: [], artifacts: [] }));

    const formData = new FormData();
    formData.append("conversationId", selectedConversation?._id || selectedConversation?.id || "");
    formData.append("prompt", lastUserMsg.content);
    formData.append("agent", "auto");

    await streamPrompt(formData, {
      onChunk: (chunk, full) => {
        dispatch(updateLastAssistantMessage({ content: full }));
      },
      onDone: (doneEvent) => {
        dispatch(updateLastAssistantMessage({
          content: doneEvent.answer,
          images: doneEvent.images,
          artifacts: doneEvent.artifacts
        }));
        if (doneEvent.artifacts) dispatch(setArtifacts(doneEvent.artifacts));
        dispatch(setIsLoading(false));
      },
      onError: (err) => {
        dispatch(updateLastAssistantMessage({ content: `⚠️ Error: ${err}` }));
        dispatch(setIsLoading(false));
      }
    });
  };

  const handleEditMessage = async (newText) => {
    if (!newText || isLoading) return;
    dispatch(setIsLoading(true));
    dispatch(addMessage({ role: "user", content: newText }));
    dispatch(addMessage({ role: "assistant", content: "", images: [], artifacts: [] }));

    const formData = new FormData();
    formData.append("conversationId", selectedConversation?._id || selectedConversation?.id || "");
    formData.append("prompt", newText);
    formData.append("agent", "auto");

    await streamPrompt(formData, {
      onChunk: (chunk, full) => {
        dispatch(updateLastAssistantMessage({ content: full }));
      },
      onDone: (doneEvent) => {
        dispatch(updateLastAssistantMessage({
          content: doneEvent.answer,
          images: doneEvent.images,
          artifacts: doneEvent.artifacts
        }));
        if (doneEvent.artifacts) dispatch(setArtifacts(doneEvent.artifacts));
        dispatch(setIsLoading(false));
      },
      onError: (err) => {
        dispatch(updateLastAssistantMessage({ content: `⚠️ Error: ${err}` }));
        dispatch(setIsLoading(false));
      }
    });
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {messages.length === 0 && !isLoading ? (
        <div className="h-full flex flex-col items-center justify-center gap-4 text-center px-4">
          <div className="flex flex-col gap-1.5 items-center">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-700 flex items-center justify-center shadow-lg shadow-indigo-500/25 mb-2">
              <span className="text-xl">🧠</span>
            </div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">CortexAI Intelligence Workspace</h1>
            <p className="text-xs text-slate-400 max-w-[340px] leading-relaxed">
              Autonomous multi-agent platform for full-stack coding, slide decks, PDF reports, data analysis, and live web research.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-2 max-w-lg">
            {[
              "📊 Analyze quarterly sales CSV",
              "💻 Build a full-stack Kanban board in React",
              "📄 Generate a comprehensive AI research report (PDF)",
              "📊 Create an 8-slide pitch deck for a SaaS startup (PPTX)"
            ].map((s) => (
              <button
                key={s}
                onClick={() => handleEditMessage(s)}
                className="text-[11.5px] text-slate-300 bg-[#131620] border border-white/[0.08] px-3.5 py-2 rounded-xl hover:bg-white/[0.08] hover:text-white transition cursor-pointer shadow-sm"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          {messages.map((msg, i) => (
            <motion.div
              key={msg._id || msg.id || i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              <MessageBubble
                role={msg.role}
                content={msg.content}
                images={msg?.images || []}
                messageId={msg._id || msg.id}
                feedback={msg.feedback}
                onRegenerate={i === messages.length - 1 && msg.role === "assistant" ? handleRegenerate : undefined}
                onEdit={msg.role === "user" ? handleEditMessage : undefined}
              />
            </motion.div>
          ))}

          {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              <GeneratingIndicator />
            </motion.div>
          )}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}