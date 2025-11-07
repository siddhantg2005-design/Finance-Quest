import React, { useEffect, useState } from "react";
import { Recurring } from "../services/mongodbClient";

export default function RecurringPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", type: "expense", amount: "", currency: "USD", category: "", description: "", cadence: "monthly" });

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const res = await Recurring.list();
      setItems(Array.isArray(res.items) ? res.items : []);
    } catch (e) {
      setError("Failed to load rules");
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
        name: form.name || "Recurring",
        type: form.type || "expense",
        amount: Number(form.amount),
        currency: form.currency || "USD",
        category: form.category || null,
        description: form.description || null,
        cadence: form.cadence || "monthly",
      };
      await Recurring.create(payload);
      setForm({ name: "", type: "expense", amount: "", currency: "USD", category: "", description: "", cadence: "monthly" });
      await refresh();
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to create rule");
    }
  }

  async function runNow(id) {
    try {
      await Recurring.runNow(id);
      await refresh();
    } catch (e) {
      setError("Run-now failed");
    }
  }

  async function runDue() {
    try {
      await Recurring.runDue();
      await refresh();
    } catch (e) {
      setError("Run-due failed");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">Recurring Rules</h2>
          <button onClick={runDue} className="px-3 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-700">Run Due</button>
        </div>
        {loading ? (
          <p className="text-slate-500 mt-2">Loading...</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-600">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Amount</th>
                  <th className="py-2 pr-4">Currency</th>
                  <th className="py-2 pr-4">Category</th>
                  <th className="py-2 pr-4">Cadence</th>
                  <th className="py-2 pr-4">Next Run</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((r)=> (
                  <tr key={r.id} className="border-t">
                    <td className="py-2 pr-4">{r.name}</td>
                    <td className="py-2 pr-4">{r.type}</td>
                    <td className="py-2 pr-4">{r.amount}</td>
                    <td className="py-2 pr-4">{r.currency}</td>
                    <td className="py-2 pr-4">{r.category || '-'}</td>
                    <td className="py-2 pr-4">{r.cadence}</td>
                    <td className="py-2 pr-4">{r.next_run}</td>
                    <td className="py-2 pr-4 text-right">
                      <button onClick={()=>runNow(r.id)} className="px-3 py-1.5 text-xs rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100">Run now</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <p className="text-slate-500 mt-3">No rules yet.</p>}
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800">Create Rule</h3>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        <form onSubmit={onCreate} className="mt-4 grid sm:grid-cols-6 gap-3">
          <input className="border rounded-lg px-3 py-2" placeholder="Name" value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} />
          <select className="border rounded-lg px-3 py-2" value={form.type} onChange={(e)=>setForm({...form, type:e.target.value})}>
            <option value="expense">expense</option>
            <option value="income">income</option>
          </select>
          <input className="border rounded-lg px-3 py-2" placeholder="Amount" type="number" step="0.01" value={form.amount} onChange={(e)=>setForm({...form, amount:e.target.value})} required />
          <input className="border rounded-lg px-3 py-2" placeholder="Currency" value={form.currency} onChange={(e)=>setForm({...form, currency:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" placeholder="Category" value={form.category} onChange={(e)=>setForm({...form, category:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" placeholder="Description" value={form.description} onChange={(e)=>setForm({...form, description:e.target.value})} />
          <select className="border rounded-lg px-3 py-2" value={form.cadence} onChange={(e)=>setForm({...form, cadence:e.target.value})}>
            <option value="monthly">monthly</option>
            <option value="weekly">weekly</option>
            <option value="daily">daily</option>
          </select>
          <div className="sm:col-span-6">
            <button className="mt-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Create</button>
          </div>
        </form>
      </div>
    </div>
  );
}
