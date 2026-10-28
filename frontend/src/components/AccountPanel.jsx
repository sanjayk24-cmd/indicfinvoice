/**
 * src/components/AccountPanel.jsx - Right Sidebar with Account Summary, Quick Actions & Languages
 */

import React from 'react';
import {
  Landmark,
  CreditCard,
  Clock,
  Lock,
  Headphones,
} from 'lucide-react';

export default function AccountPanel({
  accountData,
  currentLang,
  onSelectLang,
  onQuickAction,
}) {
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(val ?? 0);
  };

  const quickActions = [
    { id: 'balance', label: 'View Balance', icon: CreditCard },
    { id: 'transactions', label: 'Recent Transactions', icon: Clock },
    { id: 'block_card', label: 'Block Card', icon: Lock },
    { id: 'support', label: 'Open Support Ticket', icon: Headphones },
  ];

  const languages = [
    { code: 'en', label: 'English (en)', flag: '🇺🇸' },
    { code: 'hi', label: 'हिंदी (hi)', flag: '🇮🇳' },
    { code: 'ta', label: 'தமிழ் (ta)', flag: '🇮🇳' },
  ];

  return (
    <aside className="right-sidebar">
      {/* Account Summary */}
      <div className="account-summary-section">
        <h3 className="account-summary-title">Account Summary</h3>
        <div className="account-summary-card">
          <div className="account-summary-top">
            <div className="summary-bank-icon">
              <Landmark size={22} />
            </div>
            <div>
              <div className="summary-name">
                {accountData?.account_type || 'Savings Account'}
              </div>
              <div className="summary-mask">
                {accountData?.masked_account || 'XXXX 1234'}
              </div>
            </div>
          </div>
          <div className="summary-balance-number">
            ₹ {formatCurrency(accountData?.balance)}
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

      {/* Automatic language detection */}
      <div className="supported-languages-section">
        <h4 className="section-label">Automatic language detection</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {languages.map((l) => {
            const isSelected = currentLang === l.code;
            return (
              <button
                key={l.code}
                className={`language-item-badge ${isSelected ? 'selected' : ''}`}
                title="Language is detected automatically from your message"
              >
                <span className="flag-icon">{l.flag}</span>
                <span>{l.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
