"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Stethoscope, AlertCircle } from "lucide-react";

// --- Types ---
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ConsultPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Suggested prompts for the empty state
  const suggestedPrompts = [
    "What are the alternatives to Ceftazidime for a renal-impaired patient?",
    "Explain the CpxR efflux pump mechanism in E. coli.",
    "Is it safe to prescribe Augmentin if there is a mild penicillin allergy?",
    "Summarize the latest hospital antibiogram trends."
  ];

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const newUserMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    setIsLoading(true);

    try {
      // Calling our Python Backend
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Pass the new message AND the history so the AI remembers the conversation
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ role: m.role, content: m.content }))
        }),
      });

      if (!res.ok) throw new Error("API Network Error");
      
      const data = await res.json();
      
      const newAiMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, newAiMsg]);

    } catch (error) {
      console.error("Chat Error:", error);
      const errorMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: "⚠️ Connection to the AI Specialist failed. Please ensure the backend server is running." };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-slate-950 text-slate-900 dark:text-white">
      
      {/* HEADER */}
      <div className="flex-none px-8 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center border border-indigo-200 dark:border-indigo-800">
          <Stethoscope className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold">Infectious Disease AI Copilot</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">Powered by Agentic RAG Pipeline</p>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar scroll-smooth">
        <div className="max-w-4xl mx-auto space-y-8">
          
          {/* EMPTY STATE */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center mt-20 space-y-8 animate-in fade-in duration-700">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <div className="space-y-2">
                <h2 className="text-3xl font-semibold tracking-tight">How can I assist you today, Doctor?</h2>
                <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  I can review patient cases, analyze local resistance patterns, or provide second opinions on empiric therapy.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mt-8">
                {suggestedPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="p-4 text-left text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-indigo-50 dark:hover:bg-indigo-900/20 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* MESSAGE BUBBLES */}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              {/* AVATAR */}
              <div className={`w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center ${
                msg.role === "user" 
                  ? "bg-blue-600 text-white" 
                  : "bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
              }`}>
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              
              {/* MESSAGE CONTENT */}
              <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 ${
                msg.role === "user"
                  ? "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tr-sm"
                  : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm rounded-tl-sm text-slate-800 dark:text-slate-200 leading-relaxed"
              }`}>
                {msg.role === "assistant" && <span className="text-xs font-bold text-indigo-500 dark:text-indigo-400 uppercase tracking-wider mb-2 block">AI Specialist</span>}
                <div className="whitespace-pre-wrap text-[15px]">{msg.content}</div>
              </div>
            </div>
          ))}

          {/* LOADING INDICATOR */}
          {isLoading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 flex-shrink-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* INPUT AREA */}
      <div className="flex-none p-4 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-4xl mx-auto relative flex items-end gap-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-3xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500/50 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the AI Specialist a clinical question..."
            className="w-full bg-transparent border-none outline-none resize-none max-h-32 min-h-[44px] px-4 py-3 text-[15px] text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 custom-scrollbar"
            rows={1}
            style={{ height: "auto" }}
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 flex-shrink-0 rounded-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white flex items-center justify-center transition-colors mb-0.5 mr-0.5"
          >
            <Send className="w-4 h-4 ml-[-2px]" />
          </button>
        </div>
        <div className="text-center mt-2 text-[11px] text-slate-400 dark:text-slate-500 flex items-center justify-center gap-1">
          <AlertCircle className="w-3 h-3" />
          AI can make mistakes. Consider verifying critical clinical information.
        </div>
      </div>
    </div>
  );
}