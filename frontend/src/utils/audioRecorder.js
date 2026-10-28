/**
 * src/utils/audioRecorder.js - High-Fidelity 16kHz Mono PCM WAV Audio Recorder
 * Uses Web Audio API directly (no lossy MediaRecorder/WebM container issues)
 * Captures clean PCM samples straight from the microphone.
 */

export class AudioRecorder {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.source = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.peakVolume = 0;
    this.level = 0;
  }

  async start(deviceId = "") {
    if (this.isRecording || this.mediaStream) throw new Error('Recorder is already active');
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('Microphone recording requires localhost or HTTPS and a supported browser.');
    }
    try {
      this.audioChunks = [];
      this.peakVolume = 0;
      this.level = 0;

      // 1. Request microphone stream
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
          echoCancellation: true,
          noiseSuppression: false,
          autoGainControl: true,
        },
      });

      // 2. Initialize AudioContext
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioContextClass();

      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
      await this.audioContext.audioWorklet.addModule(new URL('./capture-worklet.js', import.meta.url));
      this.processor = new AudioWorkletNode(this.audioContext, 'pcm-capture');
      this.processor.port.onmessage = ({ data: samples }) => {
        if (!this.isRecording) return;
        let energy = 0;
        for (const sample of samples) {
          energy += sample * sample;
          this.peakVolume = Math.max(this.peakVolume, Math.abs(sample));
        }
        this.level = Math.sqrt(energy / samples.length);
        this.audioChunks.push(samples);
      };

      this.source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
      this.isRecording = true;
    } catch (error) {
      await this.dispose();
      throw error;
    }
  }

  async dispose() {
    this.isRecording = false;
    if (this.processor) {
      this.processor.onaudioprocess = null;
      this.processor.disconnect();
      this.processor = null;
    }
    this.source?.disconnect();
    this.source = null;
    this.mediaStream?.getTracks().forEach((track) => track.stop());
    this.mediaStream = null;
    const context = this.audioContext;
    this.audioContext = null;
    if (context && context.state !== 'closed') await context.close();
  }

  async stop() {
    if (!this.isRecording) {
      throw new Error('Recorder is not active');
    }

    this.isRecording = false;

    // Disconnect audio nodes
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }

    const recordedSampleRate = this.audioContext ? this.audioContext.sampleRate : 44100;

    if (this.audioContext && this.audioContext.state !== 'closed') {
      await this.audioContext.close();
      this.audioContext = null;
    }

    // Merge Float32Array chunks
    let totalSamples = 0;
    for (const chunk of this.audioChunks) {
      totalSamples += chunk.length;
    }

    if (totalSamples === 0) {
      throw new Error('No audio captured. Please speak into the microphone.');
    }
    if (totalSamples / recordedSampleRate < 0.3) {
      throw new Error('Recording is too short. Speak a complete sentence before stopping.');
    }
    if (this.peakVolume < 0.00003) {
      throw new Error('The microphone captured no usable sound. Check your selected input device and microphone volume.');
    }

    const merged = new Float32Array(totalSamples);
    let offset = 0;
    for (const chunk of this.audioChunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }
    this.audioChunks = [];

    console.log(
      `[AudioRecorder] Captured ${totalSamples} samples at ${recordedSampleRate} Hz. Peak volume: ${this.peakVolume.toFixed(4)}`
    );

    // Resample down to 16,000 Hz if recorded at 44.1k or 48k
    const targetSampleRate = 16000;
    const resampled = this._resample(merged, recordedSampleRate, targetSampleRate);

    // Encode to 16-bit Mono PCM WAV
    const wavBuffer = this._encodeWav(resampled, targetSampleRate);
    return new Blob([wavBuffer], { type: 'audio/wav' });
  }

  _resample(samples, fromRate, toRate) {
    if (fromRate === toRate) return samples;
    const ratio = fromRate / toRate;
    const newLength = Math.round(samples.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const originIndex = i * ratio;
      const index = Math.floor(originIndex);
      const decimal = originIndex - index;
      const nextIndex = Math.min(index + 1, samples.length - 1);
      result[i] = samples[index] * (1 - decimal) + samples[nextIndex] * decimal;
    }

    return result;
  }

  _encodeWav(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    // RIFF chunk descriptor
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');

    // "fmt " sub-chunk
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
    view.setUint16(22, 1, true); // NumChannels (1 = Mono)
    view.setUint32(24, sampleRate, true); // SampleRate (16000)
    view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
    view.setUint16(32, 2, true); // BlockAlign (NumChannels * BitsPerSample/8)
    view.setUint16(34, 16, true); // BitsPerSample (16 bits)

    // "data" sub-chunk
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Write PCM 16-bit samples with normalization/clamping
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return buffer;
  }
}
