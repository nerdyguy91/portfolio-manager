const REGIME_STYLES: Record<string, string> = {
  "Normal":           "bg-green-900 text-green-300 border border-green-700",
  "Slowdown":         "bg-yellow-900 text-yellow-300 border border-yellow-700",
  "Recession Risk":   "bg-orange-900 text-orange-300 border border-orange-700",
  "Inflation Shock":  "bg-red-900 text-red-300 border border-red-700",
};

export default function RegimeBadge({ regime }: { regime: string }) {
  const style = REGIME_STYLES[regime] ?? "bg-gray-800 text-gray-300";
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${style}`}>
      {regime}
    </span>
  );
}
