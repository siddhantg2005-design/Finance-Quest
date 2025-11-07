import React, { useEffect, useMemo, useState } from "react";
import { Analytics } from "../services/mongodbClient";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip as ReTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

const COLORS = ["#10b981", "#6366f1", "#f59e0b", "#ef4444", "#14b8a6", "#8b5cf6", "#f97316", "#22c55e"]; 

export default function AnalyticsPage() {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0,7));
  const [range, setRange] = useState({ from: "", to: "" });
  const [spendData, setSpendData] = useState([]);
  const [ivx, setIvx] = useState({ income: 0, expense: 0, net: 0 });
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [{ data: sbc } = { data: {} }, ivxRes, gp] = await Promise.all([
        Analytics.spendByCategory(month).then((d)=>({ data: d })),
        Analytics.incomeVsExpense({ from: range.from || undefined, to: range.to || undefined }),
        Analytics.goalProgress(),
      ]);
      setSpendData((sbc?.data) || []);
      setIvx({ income: ivxRes.income || 0, expense: ivxRes.expense || 0, net: ivxRes.net || 0 });
      setGoals(Array.isArray(gp.goals) ? gp.goals : []);
    } catch (e) {
      setError("Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const ivxChartData = useMemo(() => (
    [
      { name: "Income", value: ivx.income },
      { name: "Expense", value: ivx.expense },
      { name: "Net", value: ivx.net },
    ]
  ), [ivx]);

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-800">Analytics</h2>
          <div className="flex gap-3 items-center">
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-600">Month</label>
              <input type="month" className="border rounded-lg px-3 py-1.5" value={month} onChange={(e)=>setMonth(e.target.value)} />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-600">From</label>
              <input type="date" className="border rounded-lg px-3 py-1.5" value={range.from} onChange={(e)=>setRange({...range, from:e.target.value})} />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-600">To</label>
              <input type="date" className="border rounded-lg px-3 py-1.5" value={range.to} onChange={(e)=>setRange({...range, to:e.target.value})} />
            </div>
            <button onClick={load} className="px-3 py-2 rounded-lg bg-slate-800 text-white text-sm hover:bg-slate-700">Apply</button>
          </div>
        </div>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-semibold text-slate-800">Spend by Category ({month})</h3>
          <div className="h-64 mt-4">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={spendData} dataKey="total" nameKey="category" outerRadius={100} label>
                  {spendData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <ReTooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-semibold text-slate-800">Income vs Expense</h3>
          <div className="h-64 mt-4">
            <ResponsiveContainer>
              <BarChart data={ivxChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <ReTooltip />
                <Legend />
                <Bar dataKey="value" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="font-semibold text-slate-800">Goal Progress & Forecast</h3>
        <div className="mt-4 space-y-3">
          {goals.length === 0 && <div className="text-slate-500 text-sm">No goals yet.</div>}
          {goals.map((g) => (
            <div key={g.id} className="p-3 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between">
                <div className="font-medium text-slate-800">{g.name}</div>
                <div className="text-sm text-slate-600">{g.status}</div>
              </div>
              <div className="text-sm text-slate-600 mt-1">
                {g.current_amount} / {g.target_amount} ({g.progress_pct}%)
              </div>
              <div className="w-full h-2 bg-slate-100 rounded mt-2">
                <div className="h-2 bg-emerald-500 rounded" style={{ width: `${Math.min(100, g.progress_pct)}%` }} />
              </div>
              <div className="text-xs text-slate-500 mt-1">Forecast: {g.forecast_date || "—"}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
