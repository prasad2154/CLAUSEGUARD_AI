import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  ExternalLink, 
  Copy, 
  Check, 
  Loader2, 
  HelpCircle,
  MessageSquare,
  ShieldCheck,
  ChevronRight,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { Citation, QueryResponse } from '@/lib/types';
import { useContractStream } from '@/hooks/useContractStream';

interface AgentChatDrawerProps {
  documentId: string;
  documentName?: string;
  onSelectCitation: (clauseId: string, pageNumber: number) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  citations?: Citation[];
  timestamp: string;
  confidence?: number;
}

const QUICK_PROMPTS = [
  "Enlist high risk clauses",
  "Is indemnity or liability uncapped?",
  "What is the termination notice period?",
  "Summarize intellectual property transfer risks",
  "Are there non-solicitation or non-compete terms?"
];

export const AgentChatDrawer: React.FC<AgentChatDrawerProps> = ({
  documentId,
  documentName = "Contract",
  onSelectCitation,
  isExpanded = false,
  onToggleExpand,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'agent',
      text: `Hello. I have indexed the clauses of **${documentName}**. Ask any question to inspect provisions with verified, non-hallucinated citations.`,
      timestamp: 'Just now',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Synchronize documentName into welcome greeting when document loads
  useEffect(() => {
    if (documentName && documentName !== 'Contract') {
      setMessages((prev) => {
        if (prev.length === 1 && prev[0].id === 'welcome') {
          return [
            {
              id: 'welcome',
              sender: 'agent',
              text: `Hello. I have indexed the clauses of **${documentName}**. Ask any question to inspect provisions with verified, non-hallucinated citations.`,
              timestamp: 'Just now',
            },
          ];
        }
        return prev;
      });
    }
  }, [documentName]);

  const { isStreaming, streamedText, activeCitations, startQAStream } = useContractStream();
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, streamedText]);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || inputValue).trim();
    if (!q || isStreaming) return;

    setInputValue('');

    const userMessageId = `usr_${Date.now()}`;
    const newMsg: ChatMessage = {
      id: userMessageId,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, newMsg]);

    await startQAStream(documentId, q, (finalResponse: QueryResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          id: finalResponse.query_id || `agent_${Date.now()}`,
          sender: 'agent',
          text: finalResponse.answer,
          citations: finalResponse.citations,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          confidence: finalResponse.confidence,
        },
      ]);
    });
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="h-full flex flex-col min-h-0 bg-[#0c121e] border-l border-white/10 text-gray-200">
      {/* Chat Header */}
      <div className="flex-none p-3.5 border-b border-white/10 bg-[#0f1624]/90 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white flex items-center space-x-1.5">
              <span>ClauseGuard Agentic Q&A</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </h3>
            <p className="text-[10px] text-gray-400">Zero-hallucination citation engine</p>
          </div>
        </div>

        {onToggleExpand && (
          <button
            onClick={onToggleExpand}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Quick Prompts Carousel */}
      <div className="flex-none px-3 py-2 border-b border-white/5 bg-[#090d16]/50 flex items-center space-x-2 overflow-x-auto custom-scrollbar">
        <span className="text-[10px] uppercase font-bold text-gray-500 shrink-0">Prompts:</span>
        {QUICK_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            disabled={isStreaming}
            className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-indigo-600/20 text-gray-300 hover:text-indigo-300 border border-white/10 hover:border-indigo-500/30 transition disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div 
        ref={chatScrollRef}
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-4 space-y-4"
      >
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
            >
              <div className="flex items-center space-x-1.5 text-[10px] text-gray-400 px-1">
                {isUser ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3 text-indigo-400" />}
                <span>{isUser ? 'You' : 'Autonomous Reviewer'}</span>
                <span>•</span>
                <span>{msg.timestamp}</span>
                {msg.confidence !== undefined && (
                  <>
                    <span>•</span>
                    <span className="text-emerald-400 font-mono">{(msg.confidence * 100).toFixed(0)}% confident</span>
                  </>
                )}
              </div>

              <div
                className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-[92%] relative group ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-br-sm shadow-md'
                    : 'bg-[#151f30] text-gray-200 border border-white/10 rounded-bl-sm shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.text}</div>

                {/* Grounded Citation Badges */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-white/10 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block w-full mb-0.5">
                      Verified Clause Citations:
                    </span>
                    {msg.citations.map((c, idx) => (
                      <button
                        key={idx}
                        onClick={() => onSelectCitation(c.clause_id, c.page)}
                        className="inline-flex items-center space-x-1 px-2 py-1 rounded-md bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono transition group/cit"
                      >
                        <ExternalLink className="w-2.5 h-2.5 group-hover/cit:scale-110 transition" />
                        <span>{c.clause_id} • Page {c.page}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Action button */}
                {!isUser && (
                  <button
                    onClick={() => handleCopy(msg.text, msg.id)}
                    className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-white/10 text-gray-400 hover:text-white transition"
                    title="Copy Answer"
                  >
                    {copiedId === msg.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {/* Live Streaming Bubble */}
        {isStreaming && (
          <div className="flex flex-col items-start space-y-1.5 animate-fadeIn">
            <div className="flex items-center space-x-1.5 text-[10px] text-gray-400 px-1">
              <Bot className="w-3 h-3 text-indigo-400 animate-pulse" />
              <span>ClauseGuard Agent</span>
              <span>•</span>
              <span className="text-indigo-400 animate-pulse">Streaming Response...</span>
            </div>
            <div className="p-3.5 rounded-2xl rounded-bl-sm text-xs leading-relaxed max-w-[92%] bg-[#151f30] text-gray-200 border border-indigo-500/40 shadow-xl">
              <div className="whitespace-pre-wrap">{streamedText || 'Analyzing document vectors...'}</div>
              
              {activeCitations.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-white/10 flex flex-wrap gap-1.5">
                  <span className="text-[10px] font-semibold text-gray-400 uppercase block w-full">Grounded Evidence:</span>
                  {activeCitations.map((c, i) => (
                    <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {c.clause_id} (Page {c.page})
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="flex-none p-3.5 border-t border-white/10 bg-[#0f1624]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isStreaming}
            placeholder="Ask question with clause citations..."
            className="w-full pl-3.5 pr-10 py-2.5 rounded-xl bg-[#090d16] border border-white/10 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !inputValue.trim()}
            className="absolute right-1.5 p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 transition"
          >
            {isStreaming ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          </button>
        </form>
      </div>
    </div>
  );
};
