import React from 'react';
import { Landmark, Sparkles } from 'lucide-react';
export default function Header({currentLang}) {
  return <header className="app-header"><div className="header-brand"><div className="brand-icon-wrapper"><Landmark size={26}/></div><div className="brand-titles"><span className="brand-title">IndicFinVoice</span><span className="brand-subtitle">Your multilingual banking companion</span></div></div><div className="header-right"><span className="header-asr-badge"><Sparkles size={14}/> Automatic language · {({en:'English', hi:'हिंदी', ta:'தமிழ்'})[currentLang] || 'Ready'}</span><span className="demo-pill">SYNTHETIC DEMO</span></div></header>;
}
