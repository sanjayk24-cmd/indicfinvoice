/**
 * src/components/MessageInput.jsx - Message Composer with Audio Recording
 */

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Square, Loader2, CheckCircle2 } from 'lucide-react';
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
        /* Permission guidance is shown when recording starts. */
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
    const meter = setInterval(() => setLevel(recorderRef.current?.level || 0), 100);
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

        // Focus the input box for immediate Enter/Send
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
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <label style={{ padding: '6px 16px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        Microphone:
        <select
          aria-label="Select microphone"
          value={deviceId}
          disabled={isRecording || isStarting || isProcessingAudio}
          onChange={(e) => setDeviceId(e.target.value)}
          style={{ padding: '2px 8px', borderRadius: '4px', border: '1px solid #CBD5E1' }}
        >
          <option value="">System default</option>
          {devices
            .filter((d) => d.deviceId && d.deviceId !== 'default')
            .map((d, i) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Microphone ${i + 1}`}
              </option>
            ))}
        </select>
        <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#64748B' }}>
          Language: <strong>{currentLang.toUpperCase()}</strong>
        </span>
      </label>

      {previewUrl && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '2px 16px' }}>
          <audio aria-label="Play last microphone recording" controls src={previewUrl} style={{ height: 28, flex: 1 }} />
        </div>
      )}

      {/* Error alert bar */}
      {audioError && (
        <div
          role="alert"
          className="recording-badge-bar"
          style={{ backgroundColor: '#FEF2F2', color: '#B91C1C', borderColor: '#FECACA' }}
        >
          ⚠️ {audioError}
        </div>
      )}

      {/* Success transcript notification */}
      {transcriptionSuccess && !audioError && (
        <div
          role="status"
          className="recording-badge-bar"
          style={{ backgroundColor: '#F0FDF4', color: '#15803D', borderColor: '#BBF7D0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <CheckCircle2 size={16} />
          <span>
            Transcribed: <strong>"{transcriptionSuccess}"</strong> — press <strong>Send ↗</strong> or Enter to submit.
          </span>
        </div>
      )}

      {isStarting && (
        <div role="status" className="recording-badge-bar">
          Waiting for microphone permission...
        </div>
      )}

      {/* Recording status banner */}
      {isRecording && (
        <div className="recording-badge-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#DC2626', animation: 'pulse 1s infinite' }} />
            <span>Listening... ({formatTimer(recordingSeconds)})</span>
            <meter min="0" max="0.15" value={level} aria-label="Microphone input level" style={{ width: '80px' }} />
            <span>{level < 0.001 ? 'Speak into your microphone...' : 'Receiving audio'}</span>
          </div>
          <span style={{ fontSize: '0.8rem', opacity: 0.85 }}>Click mic icon (■) to stop</span>
        </div>
      )}

      {/* Processing audio banner */}
      {isProcessingAudio && (
        <div className="recording-badge-bar" style={{ backgroundColor: '#EFF6FF', color: '#1D4ED8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Loader2 size={16} className="animate-spin" />
            <span>Transcribing speech ({currentLang.toUpperCase()})...</span>
          </div>
        </div>
      )}

      {/* Main composer bar */}
      <div className="chat-composer-container">
        {/* Microphone Button */}
        <button
          type="button"
          className={`composer-mic-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
          disabled={isLoading || isProcessingAudio || isStarting}
          title={isRecording ? 'Stop recording (click to transcribe)' : 'Click to speak with microphone'}
          aria-label="Microphone"
        >
          {isRecording ? <Square size={18} /> : <Mic size={20} />}
        </button>

        {/* Text Input */}
        <div className="composer-input-wrapper">
          <input
            ref={inputRef}
            type="text"
            className="composer-input"
            placeholder={
              isRecording
                ? 'Recording in progress... speak now'
                : 'Type your message or click the mic to speak...'
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
