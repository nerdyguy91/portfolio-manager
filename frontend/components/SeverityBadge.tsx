const STYLES: Record<string, string> = {
  Critical: "bg-red-900 text-red-300 border border-red-700",
  High:     "bg-orange-900 text-orange-300 border border-orange-700",
  Medium:   "bg-yellow-900 text-yellow-300 border border-yellow-700",
  Low:      "bg-blue-900 text-blue-300 border border-blue-700",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  const style = STYLES[severity] ?? "bg-gray-800 text-gray-300";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${style}`}>
      {severity}
    </span>
  );
}
