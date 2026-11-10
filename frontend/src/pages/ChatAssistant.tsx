import React, { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';
import { Bot, LoaderCircle, MessageCircle, Send, Sparkles, UserRound } from 'lucide-react';
import DashboardLayout from '../layouts/DashboardLayout';
import { chatService } from '../services/api';
import type { ChatMessage } from '../services/api';

const suggestedQuestions = [
  'How can I help preserve my EV battery?',
  'What is the difference between AC and DC charging?',
  'How should I plan a long EV trip?',
];

const ChatAssistant: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const conversationRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    conversationRef.current?.scrollTo({
      top: conversationRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, loading]);

  const sendMessage = async (event?: FormEvent) => {
    event?.preventDefault();
    const content = input.trim();
    if (!content || loading) return;

    const updatedMessages = [...messages, { role: 'user' as const, content }];
    setMessages(updatedMessages);
    setInput('');
    setError('');
    setLoading(true);

    try {
      const { reply } = await chatService.sendMessage(updatedMessages.slice(-12));
      setMessages([...updatedMessages, { role: 'assistant', content: reply }]);
    } catch (requestError: unknown) {
      const detail = axios.isAxiosError<{ detail?: string }>(requestError)
        ? requestError.response?.data?.detail
        : undefined;
      setMessages(messages);
      setInput(content);
      setError(detail || 'Could not reach the assistant. Check that the backend is running and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mx-auto flex h-[calc(100vh-5rem)] max-w-5xl flex-col gap-5">
        <header>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-2.5">
              <MessageCircle className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight">EVolt Assistant</h1>
              <p className="mt-1 text-sm text-gray-400">Ask about EVs, charging, and battery health.</p>
            </div>
          </div>
        </header>

        <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-[#1e293b] bg-[#0f172a]/70">
          <div ref={conversationRef} className="flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
            {messages.length === 0 ? (
              <div className="flex h-full min-h-64 flex-col items-center justify-center text-center">
                <div className="mb-4 rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4">
                  <Bot className="h-9 w-9 text-cyan-400" />
                </div>
                <h2 className="text-xl font-bold text-white">How can I help?</h2>
                <p className="mt-2 max-w-md text-sm text-gray-400">
                  I can answer general questions about electric vehicles, charging, and battery care.
                </p>
                <div className="mt-6 flex max-w-2xl flex-wrap justify-center gap-2">
                  {suggestedQuestions.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => setInput(question)}
                      className="rounded-xl border border-[#334155] px-3 py-2 text-left text-xs text-gray-300 transition hover:border-cyan-500/50 hover:text-cyan-300"
                    >
                      <Sparkles className="mr-1.5 inline h-3.5 w-3.5 text-cyan-400" />
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={`${index}-${message.role}`}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400">
                      <Bot className="h-5 w-5" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[75%] ${
                      message.role === 'user'
                        ? 'bg-cyan-500/15 text-cyan-50'
                        : 'border border-[#334155] bg-[#111827] text-gray-200'
                    }`}
                  >
                    {message.content}
                  </div>
                  {message.role === 'user' && (
                    <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400">
                      <UserRound className="h-5 w-5" />
                    </div>
                  )}
                </div>
              ))
            )}
            {loading && (
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400">
                  <Bot className="h-5 w-5" />
                </div>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                EVolt is thinking...
              </div>
            )}
          </div>

          <div className="border-t border-[#1e293b] p-4 sm:p-5">
            {error && (
              <p role="alert" className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
            <form onSubmit={sendMessage} className="flex items-end gap-3">
              <textarea
                aria-label="Message EVolt Assistant"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    void sendMessage();
                  }
                }}
                maxLength={4000}
                rows={1}
                placeholder="Ask a question..."
                className="max-h-36 min-h-12 flex-1 resize-y rounded-xl border border-[#334155] bg-[#0b0f19] px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition focus:border-cyan-500"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                aria-label="Send message"
                className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? <LoaderCircle className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </button>
            </form>
            <p className="mt-2 text-center text-xs text-gray-500">
              AI responses can be inaccurate. Press Enter to send; Shift+Enter for a new line.
            </p>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
};

export default ChatAssistant;
