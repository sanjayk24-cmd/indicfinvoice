/**
 * src/components/Sidebar.jsx - Left Navigation & Try Asking Prompts
 */

import React from 'react';
import {
  MessageSquare,
  CreditCard,
  SlidersHorizontal,
  Settings,
  HelpCircle,
} from 'lucide-react';

export default function Sidebar({ onSelectPrompt, activeNav = 'chat', onSelectNav }) {
  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'account_info', label: 'Account Info', icon: CreditCard },
    { id: 'transactions', label: 'Transactions', icon: SlidersHorizontal },
    { id: 'services', label: 'Services', icon: Settings },
    { id: 'help', label: 'Help', icon: HelpCircle },
  ];

  const suggestedPrompts = [
    'What is my account balance?',
    'Show my recent transactions',
    'I want to block my card',
    'Help me with a loan query',
    'How do I check my FD details?',
  ];

  return (
    <aside className="left-sidebar">
      {/* Navigation Menu */}
      <nav className="nav-menu">
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
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Try Asking Section */}
      <div className="try-asking-section">
        <h3 className="sidebar-section-title">Try asking</h3>
        <div className="try-asking-list">
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              className="prompt-pill-btn"
              onClick={() => onSelectPrompt(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
