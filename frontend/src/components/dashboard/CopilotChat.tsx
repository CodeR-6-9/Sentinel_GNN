"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";

interface CopilotChatProps {
  patientProfile: any;
  strategy: string;
  selectedDrug: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function CopilotChat({ patientProfile, strategy, selectedDrug }: CopilotChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with a context-aware greeting
  useEffect(() => {
    if (messages.length === 0 && strategy) {
      const age = patientProfile?.Age || "unknown";
      const allergy = patientProfile?.Penicillin_Allergy ? "a Penicillin allergy" : "no known allergies";
      setMessages([
        {
          id: "intro",
          role: "assistant",
          content: `I've reviewed the ${age}-year-old patient's file (noting ${allergy}) and the recommendation for ${selectedDrug || "the primary therapy"}. Are there any other medical constraints or prior history I should factor in?`
        }
      ]);
    }
  }, [strategy, patientProfile, selectedDrug, messages.length]);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => scrollToBottom(), [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const text = input;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          context: {
            patient_profile: patientProfile,
            strategy: strategy,
            drug: selectedDrug
          }
        }),
      });

      if (!res.ok) throw new Error("API Error");
      const data = await res.json();
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: data.reply }]);
    } catch (error) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: "⚠️ Connection to the AI Specialist failed." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden flex flex-col h-[400px]">
      {/* Header */}
      <div className="bg-indigo-50 dark:bg-indigo-900/10 px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-indigo-500" />
        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          Case Discussion Copilot
        </h4>
        <span className="ml-auto text-[10px] bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 px-2 py-0.5 rounded-full font-bold">
          CONTEXT SYNCED
        </span>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-50/50 dark:bg-slate-950/50">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-6 h-6 flex-shrink-0 rounded-full flex items-center justify-center mt-1 ${
              msg.role === "user" ? "bg-blue-600 text-white" : "bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
            }`}>
              {msg.role === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
            </div>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-[13px] ${
              msg.role === "user"
                ? "bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tr-sm"
                : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 rounded-tl-sm shadow-sm"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-6 h-6 flex-shrink-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mt-1"><Bot className="w-3 h-3 text-white" /></div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" />
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 rounded-full px-4 py-1.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Add patient history or refine strategy..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400"
          />
          <button onClick={handleSend} disabled={!input.trim() || isLoading} className="p-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 rounded-full text-white transition-colors">
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}