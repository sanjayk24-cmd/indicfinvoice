/**
 * src/components/ChatWindow.jsx - Central Conversation Window
 */

import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { Bot } from 'lucide-react';

export default function ChatWindow({ messages, isLoading, error }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  return (
    <div className="chat-messages-container">
      {messages.map((msg, index) => (
        <MessageBubble key={msg.id || index} message={msg} />
      ))}

      {/* Typing Indicator while awaiting backend response */}
      {isLoading && (
        <div className="message-row assistant-row">
          <div className="avatar-circle avatar-assistant">
            <Bot size={22} />
          </div>
          <div className="message-bubble-wrapper">
            <div className="message-bubble assistant-bubble typing-indicator">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div
          role="alert"
          style={{
            padding: '12px 16px',
            backgroundColor: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: '12px',
            color: '#B91C1C',
            fontSize: '0.88rem',
            textAlign: 'center',
            margin: '8px 0',
          }}
        >
          {error}
        </div>
      )}

      <div ref={bottomRef} style={{ height: '1px' }} />
    </div>
  );
}
