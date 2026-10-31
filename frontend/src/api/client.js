/**
 * src/api/client.js - API client for IndicFinVoice Backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Health check failed:', err);
    return { status: 'offline', error: err.message };
  }
}

export async function sendChatMessage(
  message,
  lang = 'en',
  sessionId = null,
  customerId = 'C001',
  voiceGender = 'female',
  ttsEnabled = true
) {
  const payload = {
    message,
    lang,
    session_id: sessionId,
    customer_id: customerId,
    voice_gender: voiceGender,
    tts_enabled: ttsEnabled,
  };

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Server error (HTTP ${res.status})`);
  }

  return await res.json();
}

export async function transcribeAudio(audioBlob, lang = 'hi', model = 'auto') {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.wav');
  formData.append('lang', lang);
  formData.append('model', model);

  const res = await fetch(`${API_BASE_URL}/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Transcription failed (HTTP ${res.status})`);
  }

  return await res.json();
}

export async function sendVoiceMessage(
  audioBlob,
  lang = 'hi',
  sessionId = null,
  customerId = 'C001',
  model = 'auto',
  voiceGender = 'female',
  ttsEnabled = true
) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'voice_query.wav');
  formData.append('lang', lang);
  formData.append('model', model);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  formData.append('customer_id', customerId);
  formData.append('gender', voiceGender);
  formData.append('tts_enabled', ttsEnabled);

  const res = await fetch(`${API_BASE_URL}/voice`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Voice processing failed (HTTP ${res.status})`);
  }

  return await res.json();
}

export async function synthesizeSpeech(text, lang = 'en', gender = 'female') {
  const res = await fetch(`${API_BASE_URL}/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, lang, gender }),
  });

  if (!res.ok) {
    throw new Error(`TTS synthesis failed with status ${res.status}`);
  }

  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function getAccountSummary(customerId = 'C001') {
  try {
    const res = await fetch(`${API_BASE_URL}/account/summary?customer_id=${customerId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Account summary failed:', err);
    return null;
  }
}
