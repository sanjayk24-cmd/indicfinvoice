/**
 * src/components/Sidebar.jsx - Left Navigation & Categorized Prompts
 */

import React from 'react';
import {
  MessageSquare,
  CreditCard,
  SlidersHorizontal,
  HelpCircle,
  Sparkles,
  ArrowUpRight,
  Shield,
} from 'lucide-react';

export default function Sidebar({ onSelectPrompt, activeNav = 'chat', onSelectNav }) {
  const navItems = [
    { id: 'chat', label: 'Chat Assistant', icon: MessageSquare, badge: 'Live' },
    { id: 'account_info', label: 'Account Details', icon: CreditCard },
    { id: 'transactions', label: 'Recent Activity', icon: SlidersHorizontal },
    { id: 'help', label: 'Help & FAQ', icon: HelpCircle },
  ];

  const promptCategories = [
    {
      category: 'Balance & Accounts',
      prompts: [
        { text: 'What is my account balance?', lang: 'EN' },
        { text: 'मेरा बचत खाता बैलेंस क्या है', lang: 'HI' },
      ],
    },
    {
      category: 'Payments & Activity',
      prompts: [
        { text: 'Show my recent transactions', lang: 'EN' },
        { text: 'என் சமீபத்திய பரிவர்த்தனைகள்', lang: 'TA' },
      ],
    },
    {
      category: 'Cards & Security',
      prompts: [
        { text: 'I want to block my card', lang: 'EN' },
        { text: 'When is my loan EMI due?', lang: 'EN' },
      ],
    },
  ];

  return (
    <aside className="left-sidebar">
      {/* Navigation Menu */}
      <nav className="nav-menu">
        <div className="sidebar-group-label">NAVIGATION</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectNav(item.id)}
            >
              <span className="nav-item-icon">
                <Icon size={18} />
              </span>
              <span className="nav-item-label">{item.label}</span>
              {item.badge && <span className="nav-item-badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>

      {/* Suggested Prompts by Category */}
      <div className="try-asking-section">
        <div className="sidebar-group-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={13} style={{ color: '#2563EB' }} />
          <span>TRY ASKING</span>
        </div>

        <div className="prompt-categories-container">
          {promptCategories.map((cat, cIdx) => (
            <div key={cIdx} className="prompt-category-group">
              <span className="prompt-category-title">{cat.category}</span>
              <div className="prompt-pill-group">
                {cat.prompts.map((p, pIdx) => (
                  <button
                    key={pIdx}
                    className="prompt-pill-btn"
                    onClick={() => onSelectPrompt(p.text)}
                    title={`Click to send in ${p.lang}`}
                  >
                    <span className="prompt-text">{p.text}</span>
                    <span className="prompt-lang-tag">{p.lang}</span>
                    <ArrowUpRight size={13} className="prompt-arrow-icon" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Security Footer */}
      <div className="sidebar-footer">
        <Shield size={14} className="footer-shield-icon" />
        <span>Bank-grade 256-bit SSL protection</span>
      </div>
    </aside>
  );
}
