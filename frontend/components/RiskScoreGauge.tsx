function scoreColor(score: number): string {
  if (score >= 75) return "text-red-400";
  if (score >= 50) return "text-orange-400";
  if (score >= 25) return "text-yellow-400";
  return "text-green-400";
}

function scoreLabel(score: number): string {
  if (score >= 75) return "Critical";
  if (score >= 50) return "High";
  if (score >= 25) return "Elevated";
  return "Low";
}

export default function RiskScoreGauge({ score }: { score: number }) {
  const color = scoreColor(score);
  const pct = score;
  return (
    <div className="flex flex-col items-center gap-2">
      <span className={`text-5xl font-bold tabular-nums ${color}`}>{score}</span>
      <span className={`text-sm font-semibold uppercase tracking-wide ${color}`}>
        {scoreLabel(score)} Risk
      </span>
      <div className="w-full bg-gray-800 rounded-full h-3 mt-1">
        <div
          className={`h-3 rounded-full transition-all ${
            score >= 75 ? "bg-red-500" :
            score >= 50 ? "bg-orange-500" :
            score >= 25 ? "bg-yellow-500" : "bg-green-500"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500">Score out of 100</span>
    </div>
  );
}
