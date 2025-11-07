import React, { useEffect, useState } from "react";
import { getProfile } from "../services/mongodbClient";

export default function Dashboard() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const p = await getProfile();
        if (mounted) setProfile(p);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-xl font-semibold text-slate-800">Overview</h2>
        {loading ? (
          <p className="text-slate-500 mt-2">Loading...</p>
        ) : profile ? (
          <div className="mt-4 grid sm:grid-cols-3 gap-4">
            <div className="rounded-xl bg-emerald-50 p-4">
              <div className="text-sm text-slate-600">XP</div>
              <div className="text-2xl font-semibold text-slate-800">{profile.xp}</div>
            </div>
            <div className="rounded-xl bg-indigo-50 p-4">
              <div className="text-sm text-slate-600">Level</div>
              <div className="text-2xl font-semibold text-slate-800">{profile.level}</div>
            </div>
            <div className="rounded-xl bg-amber-50 p-4">
              <div className="text-sm text-slate-600">Badges</div>
              <div className="text-2xl font-semibold text-slate-800">{profile.badges?.length || 0}</div>
            </div>
          </div>
        ) : (
          <p className="text-slate-500 mt-2">No profile data.</p>
        )}
      </div>
      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800">Quick Links</h3>
        <ul className="mt-3 list-disc pl-5 text-slate-700 space-y-1">
          <li>Use the navbar to manage Transactions, Goals, Profile, or Award XP</li>
        </ul>
      </div>
    </div>
  );
}
