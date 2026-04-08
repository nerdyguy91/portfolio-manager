import { apiFetch } from "@/components/api";
import RiskScoreGauge from "@/components/RiskScoreGauge";
import RegimeBadge from "@/components/RegimeBadge";
import SeverityBadge from "@/components/SeverityBadge";
import Link from "next/link";

async function getData() {
  const [scoreData, regimeData, alertsData] = await Promise.all([
    apiFetch<{ risk_score: number }>("/risk-score").catch(() => ({ risk_score: 0 })),
    apiFetch<{ regime: string }>("/regime").catch(() => ({ regime: "Unknown" })),
    apiFetch<any[]>("/alerts?limit=5").catch(() => []),
  ]);
  return { scoreData, regimeData, alertsData };
}

export default async function OverviewPage() {
  const { scoreData, regimeData, alertsData } = await getData();

  const criticalCount = alertsData.filter((a) => a.severity === "Critical").length;
  const highCount = alertsData.filter((a) => a.severity === "High").length;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Score */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">Portfolio Risk Score</h2>
          <RiskScoreGauge score={scoreData.risk_score} />
        </div>

        {/* Regime */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">Market Regime</h2>
          <div className="flex items-center justify-center h-16">
            <RegimeBadge regime={regimeData.regime} />
          </div>
        </div>

        {/* Alert Summary */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">Active Alerts</h2>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-red-400">Critical</span>
              <span className="font-bold text-white">{criticalCount}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-orange-400">High</span>
              <span className="font-bold text-white">{highCount}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Total (shown)</span>
              <span className="font-bold text-white">{alertsData.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide">Recent Alerts</h2>
          <Link href="/alerts" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
        </div>
        {alertsData.length === 0 ? (
          <p className="text-gray-500 text-sm">No active alerts.</p>
        ) : (
          <div className="space-y-2">
            {alertsData.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                <SeverityBadge severity={alert.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 truncate">{alert.message}</p>
                </div>
                <span className="text-xs text-gray-600 whitespace-nowrap">
                  {new Date(alert.timestamp).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
