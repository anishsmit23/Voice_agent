'use client';

export function ResultCard({
  label,
  value,
  icon,
  isLarge = false,
}: {
  label: string;
  value: string;
  icon: string;
  isLarge?: boolean;
}) {
  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-xl p-6 backdrop-blur-xl hover:border-slate-600 transition-all">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <h3 className="font-semibold text-gray-200">{label}</h3>
      </div>
      <div
        className={`text-gray-300 font-mono text-sm bg-slate-950 rounded-lg p-4 break-words ${
          isLarge ? 'max-h-64 overflow-y-auto' : ''
        }`}
      >
        {value || <span className="text-gray-500">No data</span>}
      </div>
    </div>
  );
}
