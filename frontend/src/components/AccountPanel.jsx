/**
 * src/components/AccountPanel.jsx - Right Sidebar with Visual Card, Quick Actions & Languages
 */

import React, { useState } from 'react';
import {
  CreditCard,
  Clock,
  Lock,
  Headphones,
  Eye,
  EyeOff,
  Wifi,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react';

export default function AccountPanel({
  accountData,
  currentLang = 'auto',
  onSelectLang,
  onQuickAction,
  voiceEnabled = true,
  onToggleVoice,
  voiceGender = 'female',
  onSelectGender,
}) {
  const [showBalance, setShowBalance] = useState(true);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val ?? 0);
  };

  const quickActions = [
    { id: 'balance', label: 'Check Balance', icon: CreditCard },
    { id: 'transactions', label: 'Recent Transactions', icon: Clock },
    { id: 'block_card', label: 'Card Controls & Block', icon: Lock },
    { id: 'support', label: 'Support & Helpline', icon: Headphones },
  ];

  const languages = [
    { code: 'auto', label: 'Auto Detect', native: 'Automatic', flag: '🌐' },
    { code: 'en', label: 'English', native: 'English', flag: '🇺🇸' },
    { code: 'hi', label: 'Hindi', native: 'हिंदी', flag: '🇮🇳' },
    { code: 'ta', label: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
  ];

  return (
    <aside className="right-sidebar">
      {/* Visual Debit Card */}
      <div className="visual-debit-card">
        <div className="card-gloss-overlay" />
        
        <div className="card-top-row">
          <span className="card-bank-brand">INDICFIN BANK</span>
          <span className="card-network-badge">PLATINUM</span>
        </div>

        <div className="card-chip-container">
          <div className="card-emv-chip" />
          <Wifi size={16} className="card-contactless-icon" style={{ transform: 'rotate(90deg)' }} />
        </div>

        <div className="card-number-masked">
          •••• •••• •••• {accountData?.masked_account?.replace(/[^0-9]/g, '') || '1234'}
        </div>

        <div className="card-bottom-row">
          <div>
            <div className="card-holder-name">
              {accountData?.account_type || 'PRIMARY SAVINGS'}
            </div>
          </div>
          <div className="card-balance-display">
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span className="card-balance-label">AVAILABLE</span>
              <button
                type="button"
                onClick={() => setShowBalance(!showBalance)}
                style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: 0 }}
                title={showBalance ? 'Hide balance' : 'Show balance'}
              >
                {showBalance ? <EyeOff size={12} /> : <Eye size={12} />}
              </button>
            </div>
            <div className="card-balance-val">
              {showBalance ? `₹ ${formatCurrency(accountData?.balance)}` : '••••••••'}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions-section">
        <h4 className="section-label">Quick Actions</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.id}
                className="quick-action-btn"
                onClick={() => onQuickAction(action.id)}
              >
                <span className="quick-action-icon">
                  <Icon size={18} />
                </span>
                <span>{action.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Voice Assistant & Output Persona */}
      <div className="voice-settings-section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h4 className="section-label">Voice Assistant Output</h4>
          {voiceEnabled ? (
            <Volume2 size={15} style={{ color: '#2563EB' }} />
          ) : (
            <VolumeX size={15} style={{ color: '#94A3B8' }} />
          )}
        </div>

        {/* Voice Toggle Switch Card */}
        <div className={`voice-toggle-card ${!voiceEnabled ? 'muted' : ''}`}>
          <div className="voice-toggle-info">
            <span className="voice-toggle-title">
              {voiceEnabled ? 'Voice Replies Active' : 'Voice Replies Muted'}
            </span>
            <span className="voice-toggle-sub">
              {voiceEnabled ? 'Model speaks answers aloud' : 'Only text output rendered'}
            </span>
          </div>
          <button
            type="button"
            className={`voice-switch-btn ${voiceEnabled ? 'active' : ''}`}
            onClick={onToggleVoice}
            aria-label="Toggle voice output"
            title={voiceEnabled ? 'Click to mute spoken responses' : 'Click to enable spoken responses'}
          >
            <span className="voice-switch-handle" />
          </button>
        </div>

        {/* Persona Selector (Male / Female) */}
        <div className="voice-persona-card">
          <div className="voice-persona-header">
            <span>Voice Persona</span>
            <span className="voice-persona-engine">Microsoft Neural</span>
          </div>

          <div className="voice-persona-grid">
            <button
              type="button"
              className={`persona-option-btn ${voiceGender === 'female' ? 'selected' : ''}`}
              onClick={() => onSelectGender && onSelectGender('female')}
              disabled={!voiceEnabled}
              title="Select Female Voice (Neerja / Swara / Pallavi)"
            >
              <div className="persona-btn-top">
                <span className="persona-emoji">👩</span>
                <span className="persona-name">Female</span>
                {voiceGender === 'female' && <span className="persona-check">✓</span>}
              </div>
              <span className="persona-voice-meta">
                {currentLang === 'hi'
                  ? 'Swara · हिंदी'
                  : currentLang === 'ta'
                  ? 'Pallavi · தமிழ்'
                  : 'Neerja · Indian EN'}
              </span>
            </button>

            <button
              type="button"
              className={`persona-option-btn ${voiceGender === 'male' ? 'selected' : ''}`}
              onClick={() => onSelectGender && onSelectGender('male')}
              disabled={!voiceEnabled}
              title="Select Male Voice (Prabhat / Madhur / Valluvar)"
            >
              <div className="persona-btn-top">
                <span className="persona-emoji">👨</span>
                <span className="persona-name">Male</span>
                {voiceGender === 'male' && <span className="persona-check">✓</span>}
              </div>
              <span className="persona-voice-meta">
                {currentLang === 'hi'
                  ? 'Madhur · हिंदी'
                  : currentLang === 'ta'
                  ? 'Valluvar · தமிழ்'
                  : 'Prabhat · Indian EN'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Language Selection & Automatic Detection */}
      <div className="supported-languages-section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h4 className="section-label">Speech & Chat Language</h4>
          <Sparkles size={13} style={{ color: '#059669' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {languages.map((l) => {
            const isSelected = currentLang === l.code;
            return (
              <button
                key={l.code}
                type="button"
                className={`language-item-badge ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectLang && onSelectLang(l.code)}
                style={{ cursor: 'pointer', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px' }}
                title={`Set speech and chat language to ${l.label} (${l.native})`}
              >
                <span className="flag-icon">{l.flag}</span>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: isSelected ? '700' : '600', fontSize: '0.86rem' }}>{l.label}</span>
                  <span style={{ fontSize: '0.72rem', color: isSelected ? '#065F46' : '#64748B' }}>{l.native}</span>
                </div>
                {isSelected && (
                  <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#059669', fontWeight: '700' }}>
                    ● Active
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
