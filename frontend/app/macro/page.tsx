import { apiFetch } from "@/components/api";

interface MacroData {
  us_2y_yield: { latest: number | null; latest_date: string | null };
  us_10y_yield: { latest: number | null; latest_date: string | null };
  uk_10y_gilt: { latest: number | null; latest_date: string | null };
  commodity_index: { latest: number | null; latest_date: string | null };
  yield_spread: number | null;
  yield_curve_inverted: boolean | null;
}

function fmt(n: number | null, decimals = 3): string {
  return n != null ? `${n.toFixed(decimals)}%` : "—";
}

export default async function MacroPage() {
  const macro = await apiFetch<MacroData>("/macro").catch(() => null);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">Macro</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Yield Curve */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">US Yield Curve</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">2-Year Yield</span>
              <span className="font-mono text-white">{fmt(macro?.us_2y_yield.latest)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">10-Year Yield</span>
              <span className="font-mono text-white">{fmt(macro?.us_10y_yield.latest)}</span>
            </div>
            <div className="flex justify-between border-t border-gray-800 pt-3">
              <span className="text-gray-400 text-sm">Spread (10Y – 2Y)</span>
              <span className={`font-mono font-semibold ${
                macro?.yield_spread != null && macro.yield_spread < 0 ? "text-red-400" : "text-green-400"
              }`}>
                {macro?.yield_spread != null ? `${macro.yield_spread > 0 ? "+" : ""}${macro.yield_spread.toFixed(3)}%` : "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Inverted?</span>
              <span className={macro?.yield_curve_inverted ? "text-red-400 font-semibold" : "text-green-400"}>
                {macro?.yield_curve_inverted == null ? "—" : macro.yield_curve_inverted ? "Yes ⚠" : "No"}
              </span>
            </div>
          </div>
        </div>

        {/* UK Gilts */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">UK 10Y Gilt Yield</h2>
          <p className="text-4xl font-bold tabular-nums text-white">
            {fmt(macro?.uk_10y_gilt.latest)}
          </p>
          {macro?.uk_10y_gilt.latest_date && (
            <p className="text-xs text-gray-500 mt-2">
              As of {new Date(macro.uk_10y_gilt.latest_date).toLocaleDateString()}
            </p>
          )}
        </div>

        {/* Commodity Index */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 md:col-span-2">
          <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">
            Commodity Index (PPI All Commodities)
          </h2>
          <p className="text-4xl font-bold tabular-nums text-white">
            {macro?.commodity_index.latest != null ? macro.commodity_index.latest.toFixed(2) : "—"}
          </p>
          {macro?.commodity_index.latest_date && (
            <p className="text-xs text-gray-500 mt-2">
              As of {new Date(macro.commodity_index.latest_date).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
