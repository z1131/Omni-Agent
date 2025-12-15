import React, { useState } from 'react';
import clsx from 'clsx';
import { Bot, User, ChevronDown, ChevronRight, BrainCircuit } from 'lucide-react';

const MessageBubble = ({ message }) => {
    const isUser = message.role === 'user';
    const [isThoughtOpen, setIsThoughtOpen] = useState(false);

    return (
        <div className={clsx('flex w-full mb-6', isUser ? 'justify-end' : 'justify-start')}>
            <div className={clsx('flex max-w-[80%] md:max-w-[70%]', isUser ? 'flex-row-reverse' : 'flex-row')}>
                {/* Avatar */}
                <div className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1',
                    isUser ? 'ml-3 bg-primary/20 text-primary' : 'mr-3 bg-accent/20 text-accent'
                )}>
                    {isUser ? <User size={16} /> : <Bot size={16} />}
                </div>

                {/* Content */}
                <div className="flex flex-col">
                    {/* Thought Process (Agent Only) */}
                    {!isUser && message.thought && (
                        <div className="mb-2">
                            <button
                                onClick={() => setIsThoughtOpen(!isThoughtOpen)}
                                className="flex items-center text-xs text-gray-400 hover:text-white transition-colors bg-white/5 px-3 py-1.5 rounded-lg border border-white/5"
                            >
                                <BrainCircuit size={12} className="mr-2" />
                                <span className="mr-1">思考过程</span>
                                {isThoughtOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                            </button>

                            {isThoughtOpen && (
                                <div className="mt-2 text-sm text-gray-400 bg-black/20 p-3 rounded-lg border-l-2 border-accent/30 font-mono text-xs leading-relaxed animate-in fade-in slide-in-from-top-2 duration-200">
                                    {message.thought}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Message Body */}
                    <div className={clsx(
                        'p-4 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm',
                        isUser
                            ? 'bg-primary text-white rounded-tr-none'
                            : 'bg-surface border border-white/10 text-gray-100 rounded-tl-none'
                    )}>
                        {message.content}
                        {/* Streaming cursor indicator */}
                        {message.isStreaming && (
                            <span className="inline-block w-2 h-4 ml-1 bg-accent animate-pulse rounded-sm" />
                        )}
                    </div>

                    {/* Timestamp */}
                    <span className={clsx('text-[10px] text-gray-500 mt-1', isUser ? 'text-right' : 'text-left')}>
                        {message.timestamp || 'Just now'}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default MessageBubble;
