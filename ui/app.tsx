'use client';

import { useState, useRef, useEffect } from 'react';
import { Waveform } from './components/waveform';
import { AudioUploader } from './components/audio-uploader';
import { ResultCard } from './components/result-card';
import { ProcessingIndicator } from './components/processing-indicator';

export default function VoiceAgent() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [result, setResult] = useState<any>(null);
  const [confirmFileOps, setConfirmFileOps] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async () => {
    if (!audioBlob) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');

    try {
      const response = await fetch('/api/process-audio', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error processing audio:', error);
      setResult({
        transcription: '',
        intent: '',
        action: 'error',
        result: 'Failed to process audio',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    const blob = new Blob([file], { type: file.type });
    setAudioBlob(blob);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 text-white overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a1 1 0 011 1v2.101a7.002 7.002 0 015.707 11.414l1.414-1.414a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 111.414-1.414l1.414 1.414a5.002 5.002 0 01-8.242-6.828l-1.414 1.414a1 1 0 01-1.414-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414l-1.414-1.414a3 3 0 015.586 2.828V3a1 1 0 011-1z" />
              </svg>
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400">
            Voice Agent
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Speak. Understand. Execute. Turn your voice into intelligent actions with AI.
          </p>
        </div>

        {/* Main interaction area */}
        <div className="w-full max-w-2xl">
          {/* Recording area */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8 mb-8 backdrop-blur-xl">
            {isRecording && <Waveform isActive={isRecording} />}

            <div className="flex gap-4 mb-6">
              {!audioBlob ? (
                <>
                  <button
                    onClick={startRecording}
                    disabled={isRecording}
                    className="flex-1 py-4 px-6 rounded-full font-semibold transition-all bg-gradient-to-r from-blue-500 to-cyan-500 hover:shadow-lg hover:shadow-blue-500/50 disabled:opacity-75 text-white"
                  >
                    {isRecording ? 'Recording...' : '🎤 Start Recording'}
                  </button>
                  {isRecording && (
                    <button
                      onClick={stopRecording}
                      className="flex-1 py-4 px-6 rounded-full font-semibold transition-all bg-red-600 hover:bg-red-700 text-white"
                    >
                      Stop Recording
                    </button>
                  )}
                </>
              ) : (
                <>
                  <button
                    onClick={() => setAudioBlob(null)}
                    className="flex-1 py-4 px-6 rounded-full font-semibold transition-all bg-slate-700 hover:bg-slate-600 text-white"
                  >
                    Clear
                  </button>
                  <button
                    onClick={processAudio}
                    disabled={isProcessing}
                    className="flex-1 py-4 px-6 rounded-full font-semibold transition-all bg-gradient-to-r from-blue-500 to-cyan-500 hover:shadow-lg hover:shadow-blue-500/50 disabled:opacity-75 text-white"
                  >
                    {isProcessing ? 'Processing...' : 'Process Audio'}
                  </button>
                </>
              )}
            </div>

            <AudioUploader onFileSelect={handleFileUpload} />
          </div>

          {/* Confirmation checkbox */}
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 mb-6 flex items-center gap-3 backdrop-blur-xl">
            <input
              type="checkbox"
              id="confirm"
              checked={confirmFileOps}
              onChange={(e) => setConfirmFileOps(e.target.checked)}
              className="w-5 h-5 rounded border-slate-500"
            />
            <label htmlFor="confirm" className="text-sm text-gray-300">
              Approve file operations (create/write/save)
            </label>
          </div>

          {/* Processing indicator */}
          {isProcessing && <ProcessingIndicator />}

          {/* Results */}
          {result && !isProcessing && (
            <div className="space-y-4">
              <ResultCard
                label="Transcription"
                value={result.transcription}
                icon="🎤"
              />
              <ResultCard
                label="Intent"
                value={result.intent}
                icon="🧠"
              />
              <ResultCard
                label="Action"
                value={result.action}
                icon="⚡"
              />
              <ResultCard
                label="Result"
                value={result.result}
                icon="✨"
                isLarge
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
