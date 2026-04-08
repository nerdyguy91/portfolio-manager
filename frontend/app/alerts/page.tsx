import { apiFetch } from "@/components/api";
import AlertsPanel from "@/components/AlertsPanel";

export default async function AlertsPage() {
  const alerts = await apiFetch<any[]>("/alerts?limit=100").catch(() => []);

  const bySeverity: Record<string, any[]> = {
    Critical: alerts.filter((a) => a.severity === "Critical"),
    High: alerts.filter((a) => a.severity === "High"),
    Medium: alerts.filter((a) => a.severity === "Medium"),
    Low: alerts.filter((a) => a.severity === "Low"),
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <span className="text-sm text-gray-500">{alerts.length} active</span>
      </div>

      {alerts.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-green-400 font-semibold">No active alerts</p>
          <p className="text-gray-500 text-sm mt-1">All monitoring checks are passing.</p>
        </div>
      )}

      {(["Critical", "High", "Medium", "Low"] as const).map((severity) =>
        bySeverity[severity].length > 0 ? (
          <div key={severity}>
            <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-3">{severity}</h2>
            <AlertsPanel alerts={bySeverity[severity]} />
          </div>
        ) : null
      )}
    </div>
  );
}
