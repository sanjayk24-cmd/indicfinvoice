/**
 * src/components/MessageInput.jsx - Message Composer with Real-Time Audio Recording
 */

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Square, Loader2, CheckCircle2, Volume2, Globe } from 'lucide-react';
import { transcribeAudio } from '../api/client';
import { AudioRecorder } from '../utils/audioRecorder';

export default function MessageInput({
  onSendMessage,
  onSendVoice,
  currentLang = 'auto',
  isLoading,
}) {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [audioError, setAudioError] = useState('');
  const [transcriptionSuccess, setTranscriptionSuccess] = useState('');
  const [level, setLevel] = useState(0);
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    const refresh = async () => {
      try {
        const all = await navigator.mediaDevices?.enumerateDevices();
        setDevices((all || []).filter((d) => d.kind === 'audioinput'));
      } catch {
        /* Device enumeration fallback */
      }
    };
    refresh();
    navigator.mediaDevices?.addEventListener('devicechange', refresh);
    return () => navigator.mediaDevices?.removeEventListener('devicechange', refresh);
  }, []);

  const startingRef = useRef(false);
  const mountedRef = useRef(true);
  const recorderRef = useRef(null);
  const timerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
      recorderRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (!isRecording) return;
    const meter = setInterval(() => setLevel(recorderRef.current?.level || 0), 60);
    return () => clearInterval(meter);
  }, [isRecording]);

  const handleSend = () => {
    const trimmed = inputText.trim();
    if (!trimmed || isLoading || isRecording || isStarting || isProcessingAudio) return;
    onSendMessage(trimmed);
    setInputText('');
    setTranscriptionSuccess('');
    setAudioError('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRecording = async () => {
    if (startingRef.current || isLoading || isProcessingAudio) return;
    startingRef.current = true;
    setIsStarting(true);
    setAudioError('');
    setTranscriptionSuccess('');

    try {
      if (!recorderRef.current) {
        recorderRef.current = new AudioRecorder();
      }
      await recorderRef.current.start(deviceId);
      const all = await navigator.mediaDevices.enumerateDevices();
      setDevices(all.filter((d) => d.kind === 'audioinput'));
      if (!mountedRef.current) {
        await recorderRef.current.dispose();
        return;
      }
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Failed to start recording:', err);
      setAudioError('Microphone unavailable: ' + err.message);
    } finally {
      startingRef.current = false;
      if (mountedRef.current) setIsStarting(false);
    }
  };

  const stopRecording = async () => {
    if (!recorderRef.current || !isRecording) return;
    if (timerRef.current) clearInterval(timerRef.current);

    setIsRecording(false);
    setIsProcessingAudio(true);
    setAudioError('');
    setTranscriptionSuccess('');

    try {
      const wavBlob = await recorderRef.current.stop();
      setPreviewUrl(URL.createObjectURL(wavBlob));

      if (wavBlob && wavBlob.size > 0) {
        // Send audio with active speech language to ASR
        const result = await transcribeAudio(wavBlob, currentLang || 'auto');
        const text = result?.transcript?.trim();

        if (!text) {
          throw new Error('No clear speech recognized. Speak closer to the microphone and try again.');
        }

        setInputText(text);
        setTranscriptionSuccess(text);
        setAudioError('');

        // Focus the input composer for immediate review / Send
        setTimeout(() => inputRef.current?.focus(), 80);
      }
    } catch (err) {
      console.error('Error in voice transcription:', err);
      setAudioError(err.message || 'Voice transcription failed.');
    } finally {
      setIsProcessingAudio(false);
      setRecordingSeconds(0);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="composer-outer-box">
      {/* Mini Controls Toolbar */}
      <div className="composer-toolbar">
        <div className="mic-device-selector">
          <Volume2 size={13} style={{ color: '#64748B' }} />
          <select
            aria-label="Select input microphone"
            value={deviceId}
            disabled={isRecording || isStarting || isProcessingAudio}
            onChange={(e) => setDeviceId(e.target.value)}
            className="mic-device-select"
          >
            <option value="">System Default Mic</option>
            {devices
              .filter((d) => d.deviceId && d.deviceId !== 'default')
              .map((d, i) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `Microphone ${i + 1}`}
                </option>
              ))}
          </select>
        </div>

        <div className="composer-lang-badge">
          <Globe size={13} style={{ color: '#2563EB' }} />
          <span>Language:</span>
          <span className="composer-lang-tag">{currentLang.toUpperCase()}</span>
        </div>
      </div>

      {/* Audio Playback Preview (if audio was recorded) */}
      {previewUrl && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 24px', background: '#F8FAFC', borderBottom: '1px solid #F1F5F9' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>Audio Preview:</span>
          <audio aria-label="Play last microphone recording" controls src={previewUrl} style={{ height: 26, flex: 1, maxWidth: '280px' }} />
        </div>
      )}

      {/* Error Alert Bar */}
      {audioError && (
        <div role="alert" className="recording-badge-bar error">
          <span>⚠️ {audioError}</span>
        </div>
      )}

      {/* Success Notification Bar */}
      {transcriptionSuccess && !audioError && (
        <div role="status" className="recording-badge-bar success">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={15} />
            <span>
              Transcribed: <strong>"{transcriptionSuccess}"</strong> — press <strong>Send ↗</strong> or Enter.
            </span>
          </div>
        </div>
      )}

      {/* Waiting for Permission Bar */}
      {isStarting && (
        <div role="status" className="recording-badge-bar processing">
          <span>Requesting microphone access...</span>
        </div>
      )}

      {/* Active Recording Waveform Bar */}
      {isRecording && (
        <div className="recording-badge-bar active-recording">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#DC2626', animation: 'pulse-dot 1s infinite' }} />
            <span>Listening ({formatTimer(recordingSeconds)})</span>

            {/* Dynamic Sound Wave Bars */}
            <div className="sound-wave-visualizer">
              {[0.4, 0.8, 1.2, 0.6, 1.0, 1.4, 0.7, 1.1, 0.5, 0.9, 1.3, 0.6].map((multiplier, i) => {
                const dynamicHeight = Math.max(4, Math.min(22, level * 200 * multiplier + 4));
                return (
                  <span
                    key={i}
                    className="sound-wave-bar"
                    style={{ height: `${dynamicHeight}px` }}
                  />
                );
              })}
            </div>

            <span style={{ fontSize: '0.775rem', opacity: 0.85 }}>
              {level < 0.001 ? 'Speak into microphone...' : 'Receiving clear speech'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', opacity: 0.9, fontWeight: 700 }}>
            Click (■) to finish
          </span>
        </div>
      )}

      {/* Processing Audio Bar */}
      {isProcessingAudio && (
        <div className="recording-badge-bar processing">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
            <span>Transcribing speech with AI model ({currentLang.toUpperCase()})...</span>
          </div>
        </div>
      )}

      {/* Main Composer Bar */}
      <div className="chat-composer-container">
        {/* Tactile Microphone Button */}
        <button
          type="button"
          className={`composer-mic-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
          disabled={isLoading || isProcessingAudio || isStarting}
          title={isRecording ? 'Stop recording (click to transcribe)' : 'Click to speak via microphone'}
          aria-label="Microphone"
        >
          {isRecording ? <Square size={18} /> : <Mic size={20} />}
        </button>

        {/* Text Input Composer */}
        <div className="composer-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="composer-input"
            placeholder={
              isRecording
                ? 'Recording in progress... speak now'
                : 'Type a message or click the mic to speak in English, हिंदी, or தமிழ்...'
            }
            value={inputText}
            onChange={(e) => {
              setInputText(e.target.value);
              if (transcriptionSuccess) setTranscriptionSuccess('');
            }}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isRecording || isProcessingAudio || isStarting}
          />
        </div>

        {/* Send Button */}
        <button
          type="button"
          className="composer-send-btn"
          onClick={handleSend}
          disabled={!inputText.trim() || isLoading || isRecording || isProcessingAudio || isStarting}
          aria-label="Send message"
          title="Send message"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
