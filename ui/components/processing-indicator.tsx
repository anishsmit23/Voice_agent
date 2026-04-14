'use client';

export function ProcessingIndicator() {
  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8 backdrop-blur-xl mb-6">
      <div className="flex flex-col items-center justify-center">
        <div className="relative w-16 h-16 mb-6">
          {/* Outer rotating ring */}
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-400 border-r-blue-400 animate-spin"></div>
          {/* Inner pulsing dot */}
          <div className="absolute inset-2 rounded-full bg-gradient-to-br from-blue-400 to-cyan-400 animate-pulse"></div>
        </div>
        <h3 className="text-xl font-semibold mb-2">Processing your audio</h3>
        <p className="text-gray-400 text-center">
          Transcribing, analyzing intent, and executing actions...
        </p>
      </div>
    </div>
  );
}
