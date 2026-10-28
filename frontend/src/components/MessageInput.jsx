/**
 * src/components/MessageInput.jsx - Message Composer with Audio Recording
 */

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Square, Loader2 } from 'lucide-react';
import { transcribeAudio } from '../api/client';
import { AudioRecorder } from '../utils/audioRecorder';

export default function MessageInput({ onSendMessage, onSendVoice, isLoading }) {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [audioError, setAudioError] = useState('');
  const [level, setLevel] = useState(0);
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);
  useEffect(() => {
    const refresh = async () => {
      try {
        const all = await navigator.mediaDevices?.enumerateDevices();
        setDevices((all || []).filter((d) => d.kind === 'audioinput'));
      } catch { /* Permission guidance is shown when recording starts. */ }
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

    try {
      const wavBlob = await recorderRef.current.stop();
      setPreviewUrl(URL.createObjectURL(wavBlob));
      if (wavBlob && wavBlob.size > 0) {
        const result = await transcribeAudio(wavBlob, 'auto');
        if (!result.transcript?.trim()) throw new Error('No reliable speech recognized. Play the recording and check the microphone, then try again.');
        setInputText(result.transcript);
        setAudioError('Review the transcript below, correct it if needed, then press Send.');
      }
    } catch (err) {
      console.error('Error stopping recording:', err);
      setAudioError(err.message);
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
      <label style={{ padding: '6px 16px', fontSize: '0.85rem' }}>
        Microphone: <select aria-label="Select microphone" value={deviceId}
          disabled={isRecording || isStarting || isProcessingAudio}
          onChange={(e) => setDeviceId(e.target.value)}>
          <option value="">System default</option>
          {devices.filter((d) => d.deviceId && d.deviceId !== 'default').map((d, i) =>
            <option key={d.deviceId} value={d.deviceId}>{d.label || `Microphone ${i + 1}`}</option>)}
        </select>
      </label>
      {previewUrl && <audio aria-label="Play last microphone recording" controls src={previewUrl} style={{ height: 32, margin: '4px 16px' }} />}
      {audioError && <div role="alert" className="recording-badge-bar">{audioError}</div>}
      {isStarting && <div role="status" className="recording-badge-bar">Waiting for microphone permission...</div>}
      {/* Recording status banner */}
      {isRecording && (
        <div className="recording-badge-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#DC2626' }} />
            <span>Listening... ({formatTimer(recordingSeconds)})</span>
            <meter min="0" max="0.15" value={level} aria-label="Microphone input level" />
            <span>{level < 0.001 ? 'No sound — check your microphone' : 'Receiving audio'}</span>
          </div>
          <span style={{ fontSize: '0.8rem', opacity: 0.85 }}>Click mic to stop and review</span>
        </div>
      )}

      {/* Processing audio banner */}
      {isProcessingAudio && (
        <div className="recording-badge-bar" style={{ backgroundColor: '#EFF6FF', color: '#1D4ED8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Loader2 size={16} className="animate-spin" />
            <span>Transcribing with native ASR (Whisper / IndicConformer)...</span>
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
          title={isRecording ? 'Stop recording' : 'Speak with microphone'}
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
                ? 'Recording in progress...'
                : 'Type your message here or use the microphone...'
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
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
