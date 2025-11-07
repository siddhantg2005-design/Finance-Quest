import React, { useEffect, useState } from "react";
import { Transactions, getProfile } from "../services/mongodbClient";

export default function TransactionsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ amount: "", currency: "USD", category: "", description: "", occurred_at: "" });

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const data = await Transactions.list();
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError("Failed to load transactions");
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
        amount: Number(form.amount),
        currency: form.currency || "USD",
        category: form.category || null,
        description: form.description || null,
        occurred_at: form.occurred_at || new Date().toISOString(),
      };
      await Transactions.create(payload);
      setForm({ amount: "", currency: "USD", category: "", description: "", occurred_at: "" });
      await refresh();
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to create transaction");
    }
  }

  async function onDelete(id) {
    try {
      await Transactions.remove(id);
      await refresh();
    } catch {
      setError("Delete failed");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-xl font-semibold text-slate-800">Add Transaction</h2>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        <form onSubmit={onSubmit} className="mt-4 grid sm:grid-cols-5 gap-3">
          <input className="border rounded-lg px-3 py-2" placeholder="Amount" type="number" step="0.01" value={form.amount} onChange={(e)=>setForm({...form, amount:e.target.value})} required />
          <input className="border rounded-lg px-3 py-2" placeholder="Currency" value={form.currency} onChange={(e)=>setForm({...form, currency:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" placeholder="Category" value={form.category} onChange={(e)=>setForm({...form, category:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" placeholder="Description" value={form.description} onChange={(e)=>setForm({...form, description:e.target.value})} />
          <input className="border rounded-lg px-3 py-2" type="datetime-local" value={form.occurred_at} onChange={(e)=>setForm({...form, occurred_at:e.target.value})} />
          <div className="sm:col-span-5">
            <button className="mt-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Create</button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">Transactions</h2>
          <button onClick={refresh} className="px-3 py-2 text-sm rounded-lg bg-slate-100 hover:bg-slate-200">Refresh</button>
        </div>
        {loading ? (
          <p className="text-slate-500 mt-2">Loading...</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-600">
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Amount</th>
                  <th className="py-2 pr-4">Currency</th>
                  <th className="py-2 pr-4">Category</th>
                  <th className="py-2 pr-4">Description</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((t)=> (
                  <tr key={t.id} className="border-t">
                    <td className="py-2 pr-4">{new Date(t.occurred_at).toLocaleString()}</td>
                    <td className="py-2 pr-4">{t.amount}</td>
                    <td className="py-2 pr-4">{t.currency}</td>
                    <td className="py-2 pr-4">{t.category || '-'}</td>
                    <td className="py-2 pr-4">{t.description || '-'}</td>
                    <td className="py-2 pr-4 text-right">
                      <button onClick={()=>onDelete(t.id)} className="px-3 py-1.5 text-xs rounded bg-red-50 text-red-700 hover:bg-red-100">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {items.length === 0 && <p className="text-slate-500 mt-3">No transactions yet.</p>}
          </div>
        )}
      </div>
    </div>
  );
}
