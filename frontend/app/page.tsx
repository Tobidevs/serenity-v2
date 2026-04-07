"use client";

import { useState } from "react";
import { ChatBox } from "./components/chat-box";
import { ChatMessage, MessageList } from "./components/message-list";
import { AgentMode, Denomination, postChat } from "@/lib/chat-api";

function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [denomination, setDenomination] = useState<Denomination>("catholic");
  const [mode, setMode] = useState<AgentMode>("devotional");

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || pending) {
      return;
    }

    setErrorMessage(null);
    setInput("");

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmedInput,
    };
    setMessages((previous) => [...previous, userMessage]);

    setPending(true);
    try {
      const response = await postChat({
        message: trimmedInput,
        denomination,
        mode,
        thread_id: threadId ?? undefined,
      });

      setThreadId(response.thread_id);

      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: response.answer,
        metadata: {
          sources: response.sources,
          scriptureReferences: response.scripture_references,
          denominationNotes: response.denomination_notes,
        },
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to reach Serenity right now. Please try again.";
      setErrorMessage(message);
    } finally {
      setPending(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setThreadId(null);
    setInput("");
    setErrorMessage(null);
  };

  return (
    <div className="chat-app-shell">
      <main className="chat-thread-scroll">
        <div className="chat-thread-shell">
          {messages.length ? (
            <div className="mb-2 flex justify-end">
              <button
                type="button"
                className="rounded-full border border-(--border-soft) bg-(--surface-muted) px-3 py-1.5 text-xs font-semibold tracking-wide text-(--text-secondary) transition hover:bg-[#e2d1be] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--border-strong)"
                onClick={handleNewChat}
                disabled={pending}
              >
                New chat
              </button>
            </div>
          ) : null}

          <MessageList messages={messages} pending={pending} />
        </div>
      </main>

      <div className="">
        <ChatBox
          input={input}
          onInputChange={setInput}
          onSend={handleSend}
          denomination={denomination}
          onDenominationChange={setDenomination}
          mode={mode}
          onModeChange={setMode}
          pending={pending}
          errorMessage={errorMessage}
        />
      </div>
    </div>
  );
}
