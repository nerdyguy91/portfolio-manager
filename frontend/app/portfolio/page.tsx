"use client";

import { useState, useEffect } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Holding {
  ticker: string;
  shares: number;
  cost_basis: number | null;
  sector: string | null;
  sector_avg_yield: number | null;
  current_price: number | null;
  market_cap: number | null;
  eps: number | null;
  dividend_per_share: number | null;
  dividend_cover: number | null;
  current_yield: number | null;
}

function coverColor(cover: number | null): string {
  if (cover === null) return "text-gray-500";
  if (cover < 1.3) return "text-red-400";
  if (cover < 1.7) return "text-yellow-400";
  return "text-green-400";
}

function fmt(n: number | null, decimals = 2): string {
  if (n === null || n === undefined) return "—";
  return n.toFixed(decimals);
}

function fmtM(n: number | null): string {
  if (n === null) return "—";
  if (n >= 1e9) return `£${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `£${(n / 1e6).toFixed(0)}M`;
  return `£${n.toFixed(0)}`;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [form, setForm] = useState({ ticker: "", shares: "", cost_basis: "", sector: "", sector_avg_yield: "" });
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const res = await fetch(`${BASE}/portfolio`, { cache: "no-store" });
    setHoldings(await res.json());
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch(`${BASE}/portfolio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker: form.ticker.toUpperCase(),
        shares: parseFloat(form.shares),
        cost_basis: form.cost_basis ? parseFloat(form.cost_basis) : null,
        sector: form.sector || null,
        sector_avg_yield: form.sector_avg_yield ? parseFloat(form.sector_avg_yield) : null,
      }),
    });
    setForm({ ticker: "", shares: "", cost_basis: "", sector: "", sector_avg_yield: "" });
    load();
  };

  const remove = async (ticker: string) => {
    await fetch(`${BASE}/portfolio/${ticker}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">Portfolio</h1>

      {/* Holdings table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wide">
              {["Ticker", "Shares", "Price", "Mkt Cap", "EPS", "DPS", "Cover", "Yield", "Sector", ""].map((h) => (
                <th key={h} className="text-left px-4 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={10} className="px-4 py-6 text-gray-500 text-center">Loading…</td></tr>
            ) : holdings.length === 0 ? (
              <tr><td colSpan={10} className="px-4 py-6 text-gray-500 text-center">No holdings. Add one below.</td></tr>
            ) : (
              holdings.map((h) => (
                <tr key={h.ticker} className="border-b border-gray-800 hover:bg-gray-800/40">
                  <td className="px-4 py-3 font-mono font-semibold text-white">{h.ticker}</td>
                  <td className="px-4 py-3 text-gray-300">{h.shares}</td>
                  <td className="px-4 py-3 text-gray-300">{h.current_price ? `${fmt(h.current_price)}` : "—"}</td>
                  <td className="px-4 py-3 text-gray-300">{fmtM(h.market_cap)}</td>
                  <td className="px-4 py-3 text-gray-300">{fmt(h.eps)}</td>
                  <td className="px-4 py-3 text-gray-300">{fmt(h.dividend_per_share, 4)}</td>
                  <td className={`px-4 py-3 font-semibold ${coverColor(h.dividend_cover)}`}>
                    {fmt(h.dividend_cover)}x
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {h.current_yield ? `${(h.current_yield * 100).toFixed(2)}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{h.sector ?? "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => remove(h.ticker)}
                      className="text-xs text-red-500 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add holding form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm text-gray-500 uppercase tracking-wide mb-4">Add Holding</h2>
        <form onSubmit={submit} className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { key: "ticker", label: "Ticker *", placeholder: "e.g. ULVR.L" },
            { key: "shares", label: "Shares *", placeholder: "100" },
            { key: "cost_basis", label: "Cost Basis", placeholder: "Optional" },
            { key: "sector", label: "Sector", placeholder: "e.g. Consumer Staples" },
            { key: "sector_avg_yield", label: "Sector Avg Yield", placeholder: "e.g. 0.035" },
          ].map(({ key, label, placeholder }) => (
            <div key={key}>
              <label className="block text-xs text-gray-500 mb-1">{label}</label>
              <input
                type="text"
                placeholder={placeholder}
                value={(form as any)[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
              />
            </div>
          ))}
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold px-4 py-2 rounded transition-colors"
            >
              Add
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
