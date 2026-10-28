import test from 'node:test';
import assert from 'node:assert/strict';
import { AudioRecorder } from './audioRecorder.js';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

test('audio worklet captures stereo input as mono without output feedback', () => {
  let Processor;
  let captured;
  const context = vm.createContext({
    AudioWorkletProcessor: class { constructor() { this.port = { postMessage: (data) => { captured = data; } }; } },
    registerProcessor: (_, processor) => { Processor = processor; },
    Float32Array,
  });
  vm.runInContext(readFileSync(new URL('./capture-worklet.js', import.meta.url), 'utf8'), context);
  const processor = new Processor();
  assert.equal(processor.process([[new Float32Array([0.4, -0.4]), new Float32Array([0.2, -0.2])]]), true);
  assert.ok(Math.abs(captured[0] - 0.3) < 0.00001);
  assert.ok(Math.abs(captured[1] + 0.3) < 0.00001);
});

test('48k microphone samples become one second of mono PCM16 at 16k', () => {
  const recorder = new AudioRecorder();
  const samples = Float32Array.from({ length: 48000 }, (_, i) => 0.5 * Math.sin(2 * Math.PI * 440 * i / 48000));
  const resampled = recorder._resample(samples, 48000, 16000);
  const wav = new DataView(recorder._encodeWav(resampled, 16000));
  assert.equal(resampled.length, 16000);
  assert.equal(wav.getUint16(22, true), 1);
  assert.equal(wav.getUint32(24, true), 16000);
  assert.equal(wav.getUint16(34, true), 16);
  assert.equal(wav.getUint32(40, true), 32000);
  assert.ok(Math.abs(wav.getInt16(44 + 18, true)) > 10000);
});

test('silent capture is rejected and microphone is released', async () => {
  const recorder = new AudioRecorder();
  let stopped = false;
  recorder.isRecording = true;
  recorder.audioChunks = [new Float32Array(16000)];
  recorder.audioContext = { sampleRate: 16000, state: 'running', close: async () => {} };
  recorder.mediaStream = { getTracks: () => [{ stop: () => { stopped = true; } }] };
  await assert.rejects(recorder.stop(), /no usable sound/);
  assert.equal(stopped, true);
});
