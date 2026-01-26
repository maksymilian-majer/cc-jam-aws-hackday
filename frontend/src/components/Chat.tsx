import { useState, useRef, useEffect } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Sparkles, MessageSquare, Zap } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import EventCard from './EventCard';
import type { EventData } from './EventCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  events?: EventData[];
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  events?: EventData[];
}

export default function Chat() {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (e?: FormEvent) => {
    e?.preventDefault();

    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmedInput,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: trimmedInput,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatResponse = await response.json();

      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        events: data.events && data.events.length > 0 ? data.events : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, there was an error processing your message. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const isBrutalist = theme === 'brutalist';

  return (
    <div className={`flex flex-col h-full overflow-hidden ${
      isBrutalist
        ? 'theme-card'
        : 'theme-card theme-card-glow rounded-3xl'
    }`}>
      {/* Chat header */}
      <div className={`px-6 py-4 ${
        isBrutalist
          ? 'border-b-4 border-black bg-black'
          : 'border-b border-white/10'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 flex items-center justify-center ${
            isBrutalist
              ? 'bg-yellow-400'
              : 'rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500'
          }`}>
            {isBrutalist ? (
              <MessageSquare className="w-5 h-5 text-black" />
            ) : (
              <MessageSquare className="w-5 h-5 text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${
              isBrutalist
                ? 'text-yellow-400 uppercase tracking-wider font-display text-xl'
                : 'text-white'
            }`}>Event Finder</h2>
            <p className={`text-sm ${
              isBrutalist
                ? 'text-yellow-400/70 uppercase tracking-wide text-xs'
                : 'text-white/50'
            }`}>
              {isBrutalist ? 'ASK ME ANYTHING' : 'Ask me to find events or create scrapers'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages container */}
      <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${
        isBrutalist ? 'bg-white' : ''
      }`}>
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className={`w-20 h-20 mx-auto mb-6 flex items-center justify-center ${
              isBrutalist
                ? 'bg-black border-4 border-black'
                : 'rounded-3xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20'
            }`}>
              {isBrutalist ? (
                <Zap className="w-10 h-10 text-yellow-400" />
              ) : (
                <Sparkles className="w-10 h-10 text-violet-400" />
              )}
            </div>
            <h3 className={`text-xl mb-2 ${
              isBrutalist
                ? 'font-display text-3xl text-black uppercase tracking-wider'
                : 'font-semibold text-white'
            }`}>
              {isBrutalist ? 'WELCOME, HACKER' : 'Welcome to Schedule Hacker'}
            </h3>
            <p className={`mb-6 max-w-md mx-auto ${
              isBrutalist
                ? 'text-black/70 uppercase tracking-wide text-sm'
                : 'text-white/50'
            }`}>
              {isBrutalist
                ? 'TELL ME WHAT EVENTS YOU SEEK'
                : 'Discover events through conversation. Just tell me what you\'re looking for.'}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'Find me tech events in SF',
                'Hackathons this weekend',
                'AI meetups near me',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className={`px-4 py-2 text-sm transition-all ${
                    isBrutalist
                      ? 'bg-white border-3 border-black text-black hover:bg-yellow-400 hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_black]'
                      : 'rounded-xl text-white/70 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20'
                  }`}
                  style={isBrutalist ? { borderWidth: '3px' } : {}}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] sm:max-w-[75%] px-4 py-3 ${
                message.role === 'user'
                  ? `theme-message-user ${isBrutalist ? '' : 'rounded-2xl rounded-br-md'}`
                  : `theme-message-assistant ${isBrutalist ? '' : 'rounded-2xl rounded-bl-md'}`
              }`}
            >
              {message.role === 'user' ? (
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              ) : (
                <div className={`prose prose-sm max-w-none ${
                  isBrutalist
                    ? 'theme-prose'
                    : 'theme-prose prose-p:my-2 prose-headings:my-2 prose-ul:my-2 prose-li:my-0.5'
                }`}>
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
              {/* Event cards */}
              {message.events && message.events.length > 0 && (
                <div className="mt-4 space-y-3">
                  {message.events.map((event) => (
                    <EventCard key={event.id} event={event} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className={`px-4 py-3 ${
              isBrutalist
                ? 'theme-message-assistant'
                : 'theme-message-assistant rounded-2xl rounded-bl-md'
            }`}>
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  <div className={`w-2 h-2 rounded-full loading-dot ${
                    isBrutalist ? 'bg-black' : 'bg-violet-400'
                  }`}></div>
                  <div className={`w-2 h-2 rounded-full loading-dot ${
                    isBrutalist ? 'bg-black' : 'bg-cyan-400'
                  }`}></div>
                  <div className={`w-2 h-2 rounded-full loading-dot ${
                    isBrutalist ? 'bg-black' : 'bg-pink-400'
                  }`}></div>
                </div>
                <span className={`text-sm ${
                  isBrutalist
                    ? 'text-black uppercase tracking-wide'
                    : 'text-white/50'
                }`}>
                  {isBrutalist ? 'HUNTING EVENTS...' : 'Searching events...'}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={sendMessage} className={`p-4 ${
        isBrutalist
          ? 'border-t-4 border-black bg-yellow-400'
          : 'border-t border-white/10'
      }`}>
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isBrutalist ? 'TYPE YOUR QUERY...' : 'Ask about events, hackathons, meetups...'}
            disabled={isLoading}
            className={`flex-1 px-4 py-3 theme-input disabled:opacity-50 disabled:cursor-not-allowed ${
              isBrutalist ? '' : 'rounded-xl'
            }`}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className={`px-5 py-3 theme-button disabled:opacity-50 flex items-center justify-center ${
              isBrutalist ? '' : 'rounded-xl'
            }`}
          >
            {isLoading ? (
              <div className={`w-5 h-5 border-2 rounded-full animate-spin ${
                isBrutalist
                  ? 'border-yellow-400/30 border-t-yellow-400'
                  : 'border-white/30 border-t-white'
              }`} />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
