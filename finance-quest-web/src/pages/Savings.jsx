import React, { useEffect, useState } from "react";
import { Savings } from "../services/mongodbClient";

export default function SavingsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ goal_id: "", amount_per_interval: "", interval: "monthly" });

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const res = await Savings.list();
      setItems(Array.isArray(res.items) ? res.items : []);
    } catch (e) {
      setError("Failed to load savings plans");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        goal_id: form.goal_id,
        amount_per_interval: Number(form.amount_per_interval),
        interval: form.interval || "monthly",
      };
      await Savings.create(payload);
      setForm({ goal_id: "", amount_per_interval: "", interval: "monthly" });
      await refresh();
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to create plan");
    }
  }

  async function runNow(id) {
    try {
      await Savings.runNow(id);
      await refresh();
    } catch (e) {
      setError("Run-now failed");
    }
  }

  async function runDue() {
    try {
      await Savings.runDue();
      await refresh();
    } catch (e) {
      setError("Run-due failed");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">Savings Plans</h2>
          <button onClick={runDue} className="px-3 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-700">Run Due</button>
        </div>
        {loading ? (
          <p className="text-slate-500 mt-2">Loading...</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-600">
                  <th className="py-2 pr-4">Goal ID</th>
                  <th className="py-2 pr-4">Amount / Interval</th>
                  <th className="py-2 pr-4">Interval</th>
                  <th className="py-2 pr-4">Next Run</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((s)=> (
                  <tr key={s.id} className="border-t">
                    <td className="py-2 pr-4">{s.goal_id}</td>
                    <td className="py-2 pr-4">{s.amount_per_interval}</td>
                    <td className="py-2 pr-4">{s.interval}</td>
                    <td className="py-2 pr-4">{s.next_run}</td>
                    <td className="py-2 pr-4 text-right">
                      <button onClick={()=>runNow(s.id)} className="px-3 py-1.5 text-xs rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100">Run now</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <p className="text-slate-500 mt-3">No savings plans yet.</p>}
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800">Create Plan</h3>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        <form onSubmit={onCreate} className="mt-4 grid sm:grid-cols-5 gap-3">
          <input className="border rounded-lg px-3 py-2" placeholder="Goal ID" value={form.goal_id} onChange={(e)=>setForm({...form, goal_id:e.target.value})} required />
          <input className="border rounded-lg px-3 py-2" placeholder="Amount per interval" type="number" step="0.01" value={form.amount_per_interval} onChange={(e)=>setForm({...form, amount_per_interval:e.target.value})} required />
          <select className="border rounded-lg px-3 py-2" value={form.interval} onChange={(e)=>setForm({...form, interval:e.target.value})}>
            <option value="monthly">monthly</option>
            <option value="weekly">weekly</option>
            <option value="daily">daily</option>
          </select>
          <div className="sm:col-span-5">
            <button className="mt-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Create</button>
          </div>
        </form>
      </div>
    </div>
  );
}
