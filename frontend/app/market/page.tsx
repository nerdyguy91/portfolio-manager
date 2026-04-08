import { apiFetch } from "@/components/api";
import RegimeBadge from "@/components/RegimeBadge";

interface MarketData {
  ftse: {
    current: number | null;
    drawdown: { drawdown: number; current: number; high: number } | null;
    history: { timestamp: string; price: number }[];
  };
  vix: number | null;
}

interface RegimeData {
  regime: string;
  drawdown: number;
  yield_inverted: boolean;
  commodity_spike: boolean;
  bond_shock: boolean;
}

function drawdownColor(d: number): string {
  if (d >= 0.20) return "text-red-400";
  if (d >= 0.15) return "text-orange-400";
  if (d >= 0.10) return "text-yellow-400";
  if (d >= 0.05) return "text-blue-400";
  return "text-green-400";
}

export default async function MarketPage() {
  const [market, regime] = await Promise.all([
    apiFetch<MarketData>("/market").catch(() => null),
    apiFetch<RegimeData>("/regime").catch(() => null),
  ]);

  const dd = market?.ftse.drawdown;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">Market</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* FTSE Drawdown */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-3">FTSE 100 Drawdown</h2>
          {dd ? (
            <>
              <p className={`text-3xl font-bold tabular-nums ${drawdownColor(dd.drawdown)}`}>
                {(dd.drawdown * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Current: {dd.current.toFixed(0)} / 90-day high: {dd.high.toFixed(0)}
              </p>
            </>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>

        {/* VIX */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-3">VIX</h2>
          {market?.vix != null ? (
            <>
              <p className={`text-3xl font-bold tabular-nums ${market.vix > 30 ? "text-red-400" : "text-green-400"}`}>
                {market.vix.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {market.vix > 30 ? "⚠ Above stress threshold (30)" : "Below stress threshold (30)"}
              </p>
            </>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>

        {/* Regime */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-3">Regime</h2>
          {regime ? (
            <div className="space-y-3">
              <RegimeBadge regime={regime.regime} />
              <div className="text-xs text-gray-500 space-y-1 mt-2">
                <p>Yield inverted: <span className={regime.yield_inverted ? "text-red-400" : "text-green-400"}>{regime.yield_inverted ? "Yes" : "No"}</span></p>
                <p>Commodity spike: <span className={regime.commodity_spike ? "text-red-400" : "text-green-400"}>{regime.commodity_spike ? "Yes" : "No"}</span></p>
                <p>Bond shock: <span className={regime.bond_shock ? "text-red-400" : "text-green-400"}>{regime.bond_shock ? "Yes" : "No"}</span></p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>
      </div>

      {/* FTSE Price History */}
      {market?.ftse.history && market.ftse.history.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">FTSE 100 — 90-Day Price History</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-gray-400">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-1 px-2">Date</th>
                  <th className="text-right py-1 px-2">Price</th>
                </tr>
              </thead>
              <tbody>
                {market.ftse.history.slice(-10).reverse().map((row) => (
                  <tr key={row.timestamp} className="border-b border-gray-800/50">
                    <td className="py-1 px-2">{new Date(row.timestamp).toLocaleDateString()}</td>
                    <td className="py-1 px-2 text-right font-mono">{row.price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
