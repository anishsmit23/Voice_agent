'use client';

export function Waveform({ isActive }: { isActive: boolean }) {
  const bars = Array.from({ length: 20 }, (_, i) => i);

  return (
    <div className="flex items-center justify-center gap-1 h-20 mb-6">
      {bars.map((i) => (
        <div
          key={i}
          className={`w-1 rounded-full transition-all duration-100 ${
            isActive
              ? 'animate-pulse bg-gradient-to-t from-blue-400 to-cyan-400'
              : 'bg-slate-600'
          }`}
          style={{
            height: `${30 + Math.random() * 40}%`,
            animationDelay: isActive ? `${i * 0.05}s` : '0s',
          }}
        />
      ))}
    </div>
  );
}
