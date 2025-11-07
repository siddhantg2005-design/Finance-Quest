import React, { useEffect, useState } from "react";
import { Goals, getProfile } from "../services/mongodbClient";

export default function GoalsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", target_amount: "", current_amount: "", deadline: "", status: "active" });

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const data = await Goals.list();
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError("Failed to load goals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);
  const [profile, setProfile] = useState(null);
  useEffect(() => { (async () => { try { const p = await getProfile(); setProfile(p); } catch {} })(); }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        user_id: profile?.id,
        name: form.name,
        target_amount: Number(form.target_amount),
        current_amount: form.current_amount ? Number(form.current_amount) : 0,
        deadline: form.deadline || null,
        status: form.status || "active",
      };
      await Goals.create(payload);
      setForm({ name: "", target_amount: "", current_amount: "", deadline: "", status: "active" });
      await refresh();
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to create goal");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-xl font-semibold text-slate-800">Create Goal</h2>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        <form onSubmit={onSubmit} className="mt-4 grid sm:grid-cols-5 gap-3">
          <input className="border rounded-lg px-3 py-2" placeholder="Name" value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} required />
          <input className="border rounded-lg px-3 py-2" placeholder="Target Amount" type="number" step="0.01" value={form.target_amount} onChange={(e)=>setForm({...form, target_amount:e.target.value})} required />
          <input className="border rounded-lg px-3 py-2" placeholder="Current Amount" type="number" step="0.01" value={form.current_amount} onChange={(e)=>setForm({...form, current_amount:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" type="date" value={form.deadline} onChange={(e)=>setForm({...form, deadline:e.target.value})} />
          <select className="border rounded-lg px-3 py-2" value={form.status} onChange={(e)=>setForm({...form, status:e.target.value})}>
            <option value="active">active</option>
            <option value="paused">paused</option>
            <option value="completed">completed</option>
            <option value="archived">archived</option>
          </select>
          <div className="sm:col-span-5">
            <button className="mt-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Create</button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">Goals</h2>
          <button onClick={refresh} className="px-3 py-2 text-sm rounded-lg bg-slate-100 hover:bg-slate-200">Refresh</button>
        </div>
        {loading ? (
          <p className="text-slate-500 mt-2">Loading...</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-600">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Target</th>
                  <th className="py-2 pr-4">Current</th>
                  <th className="py-2 pr-4">Deadline</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((g)=> (
                  <tr key={g.id} className="border-t">
                    <td className="py-2 pr-4">{g.name}</td>
                    <td className="py-2 pr-4">{g.target_amount}</td>
                    <td className="py-2 pr-4">{g.current_amount}</td>
                    <td className="py-2 pr-4">{g.deadline || '-'}</td>
                    <td className="py-2 pr-4">{g.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <p className="text-slate-500 mt-3">No goals yet.</p>}
          </div>
        )}
      </div>
    </div>
  );
}
