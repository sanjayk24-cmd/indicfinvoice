/**
 * src/utils/speechPlayer.js - Smart Audio Playback & Browser Speech Synthesis Fallback
 */

let activeAudioElement = null;

export function stopAllSpeech() {
  if (activeAudioElement) {
    try {
      activeAudioElement.pause();
      activeAudioElement.currentTime = 0;
    } catch {}
    activeAudioElement = null;
  }
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch {}
  }
}

export function playAudioDataUri(audioUri, onStart, onEnded, onError) {
  stopAllSpeech();

  if (!audioUri) {
    if (onError) onError(new Error('No audio data URI provided'));
    return;
  }

  try {
    const audio = new Audio(audioUri);
    activeAudioElement = audio;

    audio.onplay = () => {
      if (onStart) onStart();
    };

    audio.onended = () => {
      if (activeAudioElement === audio) activeAudioElement = null;
      if (onEnded) onEnded();
    };

    audio.onerror = (e) => {
      if (activeAudioElement === audio) activeAudioElement = null;
      if (onError) onError(e);
    };

    audio.play().catch((err) => {
      // Browser autoplay policy might block un-interacted audio
      console.warn('[speechPlayer] Audio autoplay blocked or interrupted:', err);
      if (onError) onError(err);
    });

    return audio;
  } catch (err) {
    console.error('[speechPlayer] Error initializing audio:', err);
    if (onError) onError(err);
  }
}

export function speakBrowserNative(text, lang = 'en', gender = 'female', onStart, onEnded) {
  stopAllSpeech();

  if (typeof window === 'undefined' || !window.speechSynthesis) {
    console.warn('[speechPlayer] window.speechSynthesis not supported');
    return;
  }

  try {
    // Clean text for speech
    const cleanText = text
      .replace(/[\U00010000-\U0010ffff]/g, '')
      .replace(/[🎙️⚠️✅●■↗•]/g, ' ')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/₹\s*([0-9,]+)/g, '$1 rupees')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);

    // Language code mapping
    const bcp47 = lang === 'hi' ? 'hi-IN' : lang === 'ta' ? 'ta-IN' : 'en-IN';
    utterance.lang = bcp47;

    // Pitch & Rate tuning for distinct Male vs Female presence
    if (gender === 'male') {
      utterance.pitch = 0.85;
      utterance.rate = 0.95;
    } else {
      utterance.pitch = 1.15;
      utterance.rate = 1.0;
    }

    // Select matching system voice if available
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      const match = voices.find((v) => {
        const name = v.name.toLowerCase();
        const vLang = v.lang.toLowerCase();
        if (gender === 'male') {
          return (
            vLang.includes(lang) &&
            (name.includes('male') || name.includes('david') || name.includes('hemant') || name.includes('valluvar') || name.includes('prabhat') || name.includes('madhur'))
          );
        } else {
          return (
            vLang.includes(lang) &&
            (name.includes('female') || name.includes('zira') || name.includes('swara') || name.includes('pallavi') || name.includes('neerja') || name.includes('kalpana'))
          );
        }
      }) || voices.find((v) => v.lang.toLowerCase().includes(lang));

      if (match) {
        utterance.voice = match;
      }
    }

    utterance.onstart = () => {
      if (onStart) onStart();
    };

    utterance.onend = () => {
      if (onEnded) onEnded();
    };

    utterance.onerror = (e) => {
      console.warn('[speechPlayer] Browser speech error:', e);
      if (onEnded) onEnded();
    };

    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.error('[speechPlayer] Failed to speak with browser synthesis:', err);
    if (onEnded) onEnded();
  }
}

