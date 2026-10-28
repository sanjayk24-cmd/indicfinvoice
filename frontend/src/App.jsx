/**
 * src/App.jsx - Main Application Component for IndicFinVoice
 */

import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import AccountPanel from './components/AccountPanel';
import {
  sendChatMessage,
  sendVoiceMessage,
  getAccountSummary,
  checkHealth,
} from './api/client';

export default function App() {
  const [currentLang, setCurrentLang] = useState('auto');
  const [sessionId, setSessionId] = useState(() => 'sess-' + Math.random().toString(36).substring(2, 9));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeNav, setActiveNav] = useState('chat');
  const [accountData, setAccountData] = useState({
    account_type: 'Savings Account',
    masked_account: 'XXXX 1234',
    balance: 45230.50,
  });

  const [messages, setMessages] = useState([]);
  const [customerId, setCustomerId] = useState('C001');
  const [customers, setCustomers] = useState([]);
  useEffect(() => {
    fetch((import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000') + '/demo/customers')
      .then((r) => r.json()).then(setCustomers).catch(() => {});
  }, []);

  // Load live account summary on startup
  useEffect(() => {
    checkHealth();
    getAccountSummary(customerId).then((res) => {
      if (res) {
        setAccountData(res);
      }
    });
  }, [customerId]);

  const formatCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    setError(null);
    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text,
      timestamp: formatCurrentTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await sendChatMessage(text, 'auto', sessionId, customerId);

      if (res.lang) setCurrentLang(res.lang);
      if (res.session_id) {
        setSessionId(res.session_id);
      }

      const botMsg = {
        id: 'bot-' + Date.now(),
        sender: 'assistant',
        text: res.reply,
        account_data: res.account_data,
        transactions: res.transactions,
        intent: res.intent,
        action: res.action,
        timestamp: formatCurrentTime(),
      };

      setMessages((prev) => [...prev, botMsg]);

      if (res.account_data) {
        setAccountData((prev) => ({
          ...prev,
          ...res.account_data,
        }));
      }
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to connect to backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendVoice = async (audioBlob) => {
    setError(null);
    const tempUserMsgId = 'voice-' + Date.now();
    const tempUserMsg = {
      id: tempUserMsgId,
      sender: 'user',
      text: `🎙️ [Detecting language and transcribing speech...]`,
      timestamp: formatCurrentTime(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      // Default STT architecture: AI4Bharat IndicConformer
      const res = await sendVoiceMessage(audioBlob, 'auto', sessionId, customerId);
      if (!res.transcript?.trim()) {
        throw new Error(res.reply || 'No speech recognized. Check the microphone and selected language, then try again.');
      }

      if (res.lang) setCurrentLang(res.lang);
      if (res.session_id) {
        setSessionId(res.session_id);
      }

      // Update user message with the actual transcript and ASR model tag
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempUserMsgId
            ? {
                ...m,
                text: res.transcript ? `🎙️ "${res.transcript}"` : '🎙️ (No clear speech detected)',
                asr_model: res.asr_model || 'ai4bharat/indic-conformer-600m-multilingual',
              }
            : m
        )
      );

      const botMsg = {
        id: 'bot-' + Date.now(),
        sender: 'assistant',
        text: res.reply,
        account_data: res.account_data,
        transactions: res.transactions,
        intent: res.intent,
        action: res.action,
        asr_model: res.asr_model || 'ai4bharat/indic-conformer-600m-multilingual',
        timestamp: formatCurrentTime(),
      };

      setMessages((prev) => [...prev, botMsg]);

      if (res.account_data) {
        setAccountData((prev) => ({
          ...prev,
          ...res.account_data,
        }));
      }
    } catch (err) {
      console.error('Voice processing error:', err);
      setError(err.message || 'Voice transcription failed.');
      // Remove temporary message on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsgId));
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (actionId) => {
    if (actionId === 'balance') {
      if (currentLang === 'hi') handleSendMessage('मेरा बचत खाता का बैलेंस क्या है');
      else if (currentLang === 'ta') handleSendMessage('எனது சேமிப்பு கணக்கு இருப்பு என்ன');
      else handleSendMessage('What is my account balance?');
    } else if (actionId === 'transactions') {
      if (currentLang === 'hi') handleSendMessage('मेरे पिछले कुछ लेनदेन दिखाओ');
      else if (currentLang === 'ta') handleSendMessage('என் சமீபத்திய பரிவர்த்தனைகளைக் காட்டு');
      else handleSendMessage('Show my recent transactions');
    } else if (actionId === 'block_card') {
      if (currentLang === 'hi') handleSendMessage('मुझे मेरा कार्ड ब्लॉक करना है');
      else if (currentLang === 'ta') handleSendMessage('என் கார்டை பிளாக் செய்ய வேண்டும்');
      else handleSendMessage('I want to block my card');
    } else if (actionId === 'support') {
      if (currentLang === 'hi') handleSendMessage('मुझे बैंक हेल्पलाइन नंबर चाहिए');
      else if (currentLang === 'ta') handleSendMessage('வங்கி உதவி எண் தேவை');
      else handleSendMessage('I need bank customer care support');
    }
  };

  const handleNavSelect = (navId) => {
    setActiveNav(navId);
    if (navId === 'account_info') {
      handleQuickAction('balance');
    } else if (navId === 'transactions') {
      handleQuickAction('transactions');
    } else if (navId === 'help') {
      handleSendMessage('Help');
    }
  };

  return (
    <>
      <Header
        currentLang={currentLang}
        onSelectLang={(lang) => setCurrentLang(lang)}
      />

      <main className="app-container">
        {/* Left Sidebar */}
        <Sidebar
          activeNav={activeNav}
          onSelectNav={handleNavSelect}
          onSelectPrompt={(prompt) => handleSendMessage(prompt)}
        />

        {/* Central Chat Area */}
        <section className="chat-center">
          <div className="workspace-toolbar">
            <div><strong>Your banking workspace</strong><small>English · हिंदी · தமிழ் — detected automatically</small></div>
            <select aria-label="Demo customer" value={customerId} disabled={isLoading} onChange={(e) => {
              setCustomerId(e.target.value); setMessages([]); setSessionId('sess-' + crypto.randomUUID());
            }}>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.name} · {c.scenario}</option>)}
            </select>
          </div>
          {!messages.length && <div className="welcome-panel"><span className="eyebrow">INDICFINVOICE / DEMO BANK</span><h1>Banking, in your own words.</h1><p>Ask about your balance, recent payments, loan due dates or insurance claims. Type or speak in English, Hindi or Tamil.</p><div className="welcome-chips">{['What is my savings account balance?', 'Show my recent transactions', 'When is my crop loan due?'].map((q) => <button key={q} onClick={() => handleSendMessage(q)}>{q} ↗</button>)}</div></div>}
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            error={error}
          />
          <MessageInput
            onSendMessage={handleSendMessage}
            onSendVoice={handleSendVoice}
            isLoading={isLoading}
          />
        </section>

        {/* Right Sidebar */}
        <AccountPanel
          accountData={accountData}
          currentLang={currentLang}
          onSelectLang={(lang) => setCurrentLang(lang)}
          onQuickAction={handleQuickAction}
        />
      </main>
    </>
  );
}
