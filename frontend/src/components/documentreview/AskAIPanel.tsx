import { useState, useRef, useEffect } from 'react';
import { X, Send, MessageCircle, ChevronDown, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { askDocument } from '../../api/ask-api';
import type { CitedSource } from '../../api/ask-api';

interface ChatMessage {
    id: string;
    role: 'user' | 'ai';
    content: string;
    sources?: CitedSource[];
}

interface AskAIPanelProps {
    documentId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function AskAIPanel({ documentId, isOpen, onClose }: AskAIPanelProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) inputRef.current?.focus();
    }, [isOpen]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    const handleSend = async () => {
        const question = input.trim();
        if (!question || isLoading) return;

        const userMsg: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: question,
        };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await askDocument(documentId, question);
            const aiMsg: ChatMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                content: response.answer,
                sources: response.sources,
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (err) {
            const errorMsg: ChatMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                content: err instanceof Error ? err.message : 'Failed to get a response. Please try again.',
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleSources = (msgId: string) => {
        setExpandedSources((prev) => {
            const next = new Set(prev);
            if (next.has(msgId)) next.delete(msgId);
            else next.add(msgId);
            return next;
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-y-0 right-0 w-[520px] z-50 flex flex-col bg-card border-l border-border shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/50">
                <div className="flex items-center gap-2">
                    <img src="/EllisIcon.png" alt="" className="w-6 h-6" />
                    <h3 className="font-medium">Ask AI</h3>
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                    title="Close (Esc)"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground text-sm gap-3">
                        <MessageCircle className="w-10 h-10 opacity-30" />
                        <p>Ask questions about this document.</p>
                        <p className="text-xs">e.g. "What was the inspection date?" or "Were any defects found?"</p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-last' : ''}`}>
                            <div
                                className={`px-3 py-2 rounded-lg text-sm ${
                                    msg.role === 'user'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-muted'
                                }`}
                            >
                                {msg.role === 'ai' ? (
                                    <div className="prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-pre:my-2 prose-code:text-xs prose-code:bg-background/50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    msg.content
                                )}
                            </div>

                            {/* Sources */}
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-1.5">
                                    <button
                                        onClick={() => toggleSources(msg.id)}
                                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {expandedSources.has(msg.id)
                                            ? <ChevronDown className="w-3 h-3" />
                                            : <ChevronRight className="w-3 h-3" />
                                        }
                                        {msg.sources.length} source{msg.sources.length > 1 ? 's' : ''}
                                    </button>
                                    {expandedSources.has(msg.id) && (
                                        <div className="mt-1.5 space-y-1.5">
                                            {msg.sources.map((src, idx) => (
                                                <div
                                                    key={idx}
                                                    className="p-2 bg-muted/50 border border-border rounded text-xs text-muted-foreground"
                                                >
                                                    <p className="line-clamp-3">{src.text}</p>
                                                    <p className="mt-1 text-[10px] opacity-60">
                                                        Relevance: {Math.round(src.relevance_score * 100)}%
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="px-3 py-2 rounded-lg bg-muted">
                            <div className="flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse" />
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse [animation-delay:0.2s]" />
                                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse [animation-delay:0.4s]" />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-border p-3">
                <div className="flex items-center gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a question about this document..."
                        className="flex-1 px-3 py-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
