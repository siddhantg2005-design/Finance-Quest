import React, { useEffect, useState } from "react";
import { getProfile } from "../services/mongodbClient";

export default function Profile() {
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

  if (loading) return <div className="bg-white rounded-2xl shadow p-6">Loading...</div>;
  if (!profile) return <div className="bg-white rounded-2xl shadow p-6">No profile found.</div>;

  return (
    <div className="grid gap-4">
      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-xl font-semibold text-slate-800">Profile</h2>
        <div className="mt-4 grid gap-2 text-slate-700">
          <div><span className="font-medium">User ID:</span> {profile.id}</div>
          <div><span className="font-medium">Email:</span> {profile.email}</div>
          <div><span className="font-medium">XP:</span> {profile.xp}</div>
          <div><span className="font-medium">Level:</span> {profile.level}</div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800">Badges</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {(profile.badges || []).length === 0 && <span className="text-slate-500">No badges yet.</span>}
          {(profile.badges || []).map((b, idx) => (
            <span key={idx} className="px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-800 border border-amber-200">
              {b.code}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
