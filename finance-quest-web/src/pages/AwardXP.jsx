import React, { useEffect, useState } from "react";
import { getProfile, awardXP } from "../services/mongodbClient";

export default function AwardXPPage() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ reason: "manual_award", xp_amount: "10" });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const p = await getProfile();
        setProfile(p);
      } catch {
        setProfile(null);
      }
    })();
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    try {
      const res = await awardXP(profile?.id, form.reason, Number(form.xp_amount || 0));
      setResult(res);
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to award XP");
    }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-xl font-semibold text-slate-800">Award XP</h2>
        {!profile && <p className="text-slate-500 mt-2">Loading profile...</p>}
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        <form onSubmit={onSubmit} className="mt-4 grid sm:grid-cols-3 gap-3">
          <input
            className="border rounded-lg px-3 py-2"
            placeholder="Reason"
            value={form.reason}
            onChange={(e)=>setForm({...form, reason:e.target.value})}
          />
          <input
            className="border rounded-lg px-3 py-2"
            type="number"
            step="1"
            min="1"
            placeholder="XP Amount"
            value={form.xp_amount}
            onChange={(e)=>setForm({...form, xp_amount:e.target.value})}
          />
          <div>
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Award</button>
          </div>
        </form>
        {result && (
          <div className="mt-4 rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-emerald-800 text-sm">
            <div>XP Awarded: <b>{result.xp_awarded}</b></div>
            <div>New Level: <b>{result.new_level}</b></div>
            <div>New Badges: {(result.new_badges || []).map(b=>b.code).join(", ") || "None"}</div>
          </div>
        )}
      </div>
    </div>
  );
}
