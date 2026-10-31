/**
 * src/components/Header.jsx - Main Application Navigation Bar
 */

import React from 'react';
import { Landmark, Sparkles, ShieldCheck, Globe } from 'lucide-react';

export default function Header({ currentLang = 'auto' }) {
  const langLabels = {
    auto: 'Auto Detect',
    en: 'English (en)',
    hi: 'हिंदी (hi)',
    ta: 'தமிழ் (ta)',
  };

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon-wrapper">
          <div className="brand-icon-glow">
            <Landmark size={22} />
          </div>
        </div>
        <div className="brand-titles">
          <div className="brand-title-row">
            <span className="brand-title">IndicFinVoice</span>
            <span className="brand-version-badge">AI 2.0</span>
          </div>
          <span className="brand-subtitle">Multilingual Neural Voice Banking Assistant</span>
        </div>
      </div>

      <div className="header-right">
        {/* Live Assistant Status */}
        <div className="header-status-pill">
          <span className="status-dot-pulse" />
          <span className="status-text">AI Core Ready</span>
        </div>

        {/* Active Speech Language Pill */}
        <div className="header-lang-pill">
          <Globe size={14} style={{ color: '#93C5FD' }} />
          <span>Speech: <strong>{langLabels[currentLang] || currentLang.toUpperCase()}</strong></span>
        </div>

        {/* Security Indicator */}
        <div className="header-security-badge" title="End-to-End Encrypted Session">
          <ShieldCheck size={14} style={{ color: '#6EE7B7' }} />
          <span>256-Bit Secure</span>
        </div>
      </div>
    </header>
  );
}
