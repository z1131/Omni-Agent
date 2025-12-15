import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Sparkles } from 'lucide-react';
import MessageBubble from './MessageBubble';

const ChatWindow = ({ compact = false }) => {
    const [input, setInput] = useState('');
    const [isComposing, setIsComposing] = useState(false); // 中文输入法状态
    const [messages, setMessages] = useState([
        {
            id: 1,
            role: 'agent',
            content: '你好！我是 Omni-Agent 智能助手。有什么可以帮助你的吗？',
            thought: '初始化对话状态，等待用户输入。',
            timestamp: '10:00 AM'
        }
    ]);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const newMessage = {
            id: messages.length + 1,
            role: 'user',
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        const currentInput = input;
        setMessages(prev => [...prev, newMessage]);
        setInput('');

        // Prepare API messages
        // Convert 'agent' role to 'assistant' for API compatibility
        // Also ensure the messages start with a user message (skip initial welcome message)
        const historyMessages = messages
            .filter(m => m.content && (m.role === 'user' || m.role === 'agent' || m.role === 'assistant'))
            .map(m => ({
                role: m.role === 'agent' ? 'assistant' : m.role,
                content: m.content
            }));
        
        // Find the first user message index to ensure we start with user role
        const firstUserIndex = historyMessages.findIndex(m => m.role === 'user');
        const validHistory = firstUserIndex >= 0 ? historyMessages.slice(firstUserIndex) : [];
        
        const apiMessages = [
            ...validHistory,
            { role: 'user', content: currentInput }
        ];

        // Create placeholder message for streaming response
        const assistantMessageId = messages.length + 2;
        setMessages(prev => [...prev, {
            id: assistantMessageId,
            role: 'agent',
            content: '',
            thought: '思考中...',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isStreaming: true
        }]);

        try {
            // Use streaming API
            const response = await fetch('http://localhost:8000/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ messages: apiMessages }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.error) {
                                throw new Error(data.error);
                            }
                            
                            if (data.content !== undefined) {
                                // Update the assistant message with new content
                                setMessages(prev => prev.map(msg => 
                                    msg.id === assistantMessageId
                                        ? { 
                                            ...msg, 
                                            content: data.content,
                                            thought: data.done ? '回复完成。' : '生成中...',
                                            isStreaming: !data.done
                                        }
                                        : msg
                                ));
                            }
                        } catch (e) {
                            // Ignore JSON parse errors for incomplete chunks
                            if (line.slice(6).trim()) {
                                console.warn('Failed to parse SSE data:', line);
                            }
                        }
                    }
                }
            }
        } catch (err) {
            console.error('Error fetching chat response:', err);
            setMessages(prev => {
                // Remove the streaming placeholder and add error message
                const filtered = prev.filter(msg => msg.id !== assistantMessageId);
                return [...filtered, {
                    id: assistantMessageId,
                    role: 'system',
                    content: `错误: ${err.message || '无法连接到 Omni-Agent 服务器'}`,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }];
            });
        }
    };

    const handleKeyDown = (e) => {
        // 如果正在使用中文输入法（IME），不触发发送
        if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
            e.preventDefault();
            handleSend();
        }
    };

    // 中文输入法事件处理
    const handleCompositionStart = () => {
        setIsComposing(true);
    };

    const handleCompositionEnd = () => {
        setIsComposing(false);
    };

    return (
        <div className="flex flex-col h-full relative">
            {/* Header */}
            {!compact && (
                <div className="absolute top-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md z-10 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center">
                        <div className="w-2 h-2 rounded-full bg-secondary animate-pulse mr-2"></div>
                        <span className="text-sm font-medium text-gray-300">Omni-Agent 在线</span>
                    </div>
                    <button className="text-xs text-primary hover:text-primary-glow transition-colors flex items-center">
                        <Sparkles size={12} className="mr-1" />
                        新建对话
                    </button>
                </div>
            )}

            {/* Messages Area */}
            <div className={`flex-1 overflow-y-auto p-4 ${compact ? '' : 'pt-20'} pb-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent`}>
                <div className="max-w-3xl mx-auto">
                    {messages.map(msg => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="p-4 bg-background/80 backdrop-blur-md border-t border-white/5">
                <div className="max-w-3xl mx-auto relative">
                    <div className="bg-surface rounded-2xl border border-white/10 focus-within:border-primary/50 focus-within:shadow-[0_0_15px_rgba(59,130,246,0.1)] transition-all duration-300 flex flex-col">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onCompositionStart={handleCompositionStart}
                            onCompositionEnd={handleCompositionEnd}
                            placeholder="输入消息，或按 / 使用命令..."
                            className="w-full bg-transparent text-white placeholder-gray-500 p-4 min-h-[60px] max-h-[200px] resize-none focus:outline-none text-sm"
                            rows={1}
                        />

                        <div className="flex justify-between items-center px-2 pb-2">
                            <div className="flex items-center space-x-1">
                                <button className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                                    <Paperclip size={18} />
                                </button>
                                <button className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                                    <Mic size={18} />
                                </button>
                            </div>

                            <button
                                onClick={handleSend}
                                disabled={!input.trim()}
                                className="p-2 bg-primary text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-primary/20"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                    <div className="text-center mt-2 text-[10px] text-gray-600">
                        Omni-Agent 可能会犯错，请核实重要信息。
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatWindow;
