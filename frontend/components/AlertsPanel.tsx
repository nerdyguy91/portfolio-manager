import SeverityBadge from "./SeverityBadge";

interface Action {
  action_type: string;
  description: string;
  direction: string | null;
}

interface Alert {
  id: number;
  type: string;
  severity: string;
  asset: string | null;
  message: string;
  explanation: { trigger: string; why_it_matters: string; suggested_actions: string[] } | null;
  needs_review: boolean;
  timestamp: string;
  actions: Action[];
}

export default function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) {
    return <p className="text-gray-500 text-sm">No active alerts.</p>;
  }

  return (
    <div className="space-y-4">
      {alerts.map((alert) => (
        <div key={alert.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="flex items-center gap-2 flex-wrap">
              <SeverityBadge severity={alert.severity} />
              <span className="text-sm font-medium text-gray-200">
                {alert.type.replace(/_/g, " ")}
              </span>
              {alert.asset && (
                <span className="text-xs text-gray-500 font-mono">{alert.asset}</span>
              )}
              {alert.needs_review && (
                <span className="text-xs bg-purple-900 text-purple-300 border border-purple-700 px-2 py-0.5 rounded">
                  Review needed
                </span>
              )}
            </div>
            <span className="text-xs text-gray-600 whitespace-nowrap">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>

          <p className="text-sm text-gray-300 mb-3">{alert.message}</p>

          {alert.explanation && (
            <div className="bg-gray-800 rounded p-3 mb-3 text-sm space-y-1">
              <p><span className="text-gray-500">Trigger:</span> {alert.explanation.trigger}</p>
              <p><span className="text-gray-500">Why it matters:</span> {alert.explanation.why_it_matters}</p>
            </div>
          )}

          {alert.actions.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Actions</p>
              <ul className="space-y-1">
                {alert.actions.map((a, i) => (
                  <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                    <span className="text-gray-600 mt-0.5">›</span>
                    {a.description}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
