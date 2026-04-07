"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type AssistantMetadata = {
  sources: string[];
  scriptureReferences: string[];
  denominationNotes: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: AssistantMetadata;
};

type MessageListProps = {
  messages: ChatMessage[];
  pending: boolean;
};

export function MessageList({ messages, pending }: MessageListProps) {
  const bottomAnchorRef = useRef<HTMLDivElement | null>(null);
  const [expandedMetadata, setExpandedMetadata] = useState<
    Record<string, boolean>
  >({});

  useEffect(() => {
    bottomAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const messageCount = useMemo(() => messages.length, [messages.length]);

  const toggleMetadata = (messageId: string) => {
    setExpandedMetadata((previous) => ({
      ...previous,
      [messageId]: !previous[messageId],
    }));
  };

  const buildMetadataSummary = (metadata: AssistantMetadata): string => {
    const details: string[] = [];

    if (metadata.sources.length) {
      details.push(
        `${metadata.sources.length} source${metadata.sources.length === 1 ? "" : "s"}`,
      );
    }

    if (metadata.scriptureReferences.length) {
      details.push(
        `${metadata.scriptureReferences.length} scripture reference${metadata.scriptureReferences.length === 1 ? "" : "s"}`,
      );
    }

    if (metadata.denominationNotes.trim()) {
      details.push("notes");
    }

    return details.join(" • ");
  };

  if (!messages.length && !pending) {
    return (
      <div className="chat-empty-state">
        <p>
          Start a conversation with Serenity. Responses are rendered in markdown
          and include scripture references, sources, and denomination notes when
          available.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {messageCount ? (
        <p className="mb-3 text-right text-xs font-semibold uppercase tracking-[0.09em] text-(--text-muted)">
          {messageCount} message{messageCount === 1 ? "" : "s"}
        </p>
      ) : null}

      {messages.map((message) => (
        <article key={message.id} className={`message-row ${message.role}`}>
          <div className="message-body">
            <div
              className={`chat-markdown ${message.role === "user" ? "chat-markdown-user" : ""}`}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || "No answer was returned by the agent."}
              </ReactMarkdown>
            </div>

            {message.role === "assistant" && message.metadata ? (
              <div className="chat-meta-wrap">
                <button
                  type="button"
                  className="chat-meta-toggle"
                  aria-expanded={Boolean(expandedMetadata[message.id])}
                  onClick={() => toggleMetadata(message.id)}
                >
                  <span>
                    {buildMetadataSummary(message.metadata) ||
                      "Response metadata"}
                  </span>
                  <span>
                    {expandedMetadata[message.id] ? "Hide" : "Expand"}
                  </span>
                </button>

                {expandedMetadata[message.id] ? (
                  <div className="chat-meta-panel">
                    {message.metadata.denominationNotes ? (
                      <section className="chat-meta-section">
                        <h3>Denomination Notes</h3>
                        <p className="whitespace-pre-wrap">
                          {message.metadata.denominationNotes}
                        </p>
                      </section>
                    ) : null}

                    {message.metadata.scriptureReferences.length ? (
                      <section className="chat-meta-section">
                        <h3>Scripture References</h3>
                        <ul>
                          {message.metadata.scriptureReferences.map(
                            (reference) => (
                              <li key={reference}>{reference}</li>
                            ),
                          )}
                        </ul>
                      </section>
                    ) : null}

                    {message.metadata.sources.length ? (
                      <section className="chat-meta-section">
                        <h3>Sources</h3>
                        <ul>
                          {message.metadata.sources.map((source) => (
                            <li key={source}>{source}</li>
                          ))}
                        </ul>
                      </section>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </article>
      ))}

      {pending ? (
        <article className="message-row assistant">
          <p className="thinking-row">Thinking...</p>
        </article>
      ) : null}

      <div ref={bottomAnchorRef} />
    </div>
  );
}
