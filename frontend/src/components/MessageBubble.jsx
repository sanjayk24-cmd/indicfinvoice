/**
 * src/components/MessageBubble.jsx - User and Assistant Message Display
 */

import React from 'react';
import { Bot, User, Landmark } from 'lucide-react';

export default function MessageBubble({ message }) {
  const isUser = message.sender === 'user';

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      {/* Avatar */}
      <div className={`avatar-circle ${isUser ? 'avatar-user' : 'avatar-assistant'}`}>
        {isUser ? <User size={20} /> : <Bot size={22} />}
      </div>

      {/* Bubble and Timestamp */}
      <div className="message-bubble-wrapper">
        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {/* Main message text */}
          {message.text && (
            <div style={{ whiteSpace: 'pre-line' }}>{message.text}</div>
          )}

          {/* Embedded Balance Card (matching reference mockup) */}
          {message.account_data && (
            <div className="embedded-balance-card">
              <div className="balance-card-left">
                <div className="bank-badge-icon">
                  <Landmark size={22} />
                </div>
                <div className="balance-card-details">
                  <span className="balance-card-type">
                    {message.account_data.account_type || 'Savings Account'}
                  </span>
                  <span className="balance-card-account">
                    {message.account_data.masked_account || 'XXXX 1234'}
                  </span>
                </div>
              </div>
              <div className="balance-card-amount">
                ₹ {formatCurrency(message.account_data.balance ?? 0)}
              </div>
            </div>
          )}

          {/* Embedded Transaction Table (matching reference mockup) */}
          {message.transactions && message.transactions.length > 0 && (
            <div className="embedded-txns-table-container">
              <table className="txns-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {message.transactions.map((txn, idx) => {
                    const isCredit = txn.type === 'credit';
                    return (
                      <tr key={idx}>
                        <td>{txn.date}</td>
                        <td style={{ fontWeight: 500 }}>{txn.description}<small style={{ display: 'block', color: '#64748b', fontWeight: 400 }}>{txn.reference} · {txn.status || 'completed'}</small></td>
                        <td className={isCredit ? 'txn-amount-credit' : 'txn-amount-debit'}>
                          {isCredit ? '+ ' : '- '}₹ {formatCurrency(Math.abs(txn.amount))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Follow-up text if specified */}
          {message.follow_up && (
            <div style={{ marginTop: '8px', color: '#475569' }}>
              {message.follow_up}
            </div>
          )}

          {/* ASR Model Tag if message was processed via voice */}
          {message.asr_model && (
            <div className="msg-asr-badge">
              🎙️ ASR: {message.asr_model.includes('whisper') ? 'OpenAI Whisper (Medium)' : 'AI4Bharat IndicConformer (600M)'}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="message-timestamp">{message.timestamp || 'Just now'}</span>
      </div>
    </div>
  );
}
