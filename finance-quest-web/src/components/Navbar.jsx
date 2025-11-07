import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthProvider";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium ${isActive ? "bg-emerald-100 text-emerald-700" : "text-slate-600 hover:bg-slate-100"}`;

  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800">Finance Quest</span>
        </div>
        <nav className="flex items-center gap-2">
          <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/analytics" className={linkClass}>Analytics</NavLink>
          <NavLink to="/transactions" className={linkClass}>Transactions</NavLink>
          <NavLink to="/recurring" className={linkClass}>Recurring</NavLink>
          <NavLink to="/savings" className={linkClass}>Savings</NavLink>
          <NavLink to="/goals" className={linkClass}>Goals</NavLink>
          <NavLink to="/profile" className={linkClass}>Profile</NavLink>
          <NavLink to="/xp" className={linkClass}>Award XP</NavLink>
        </nav>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600 hidden sm:block">{user?.email}</span>
          <button
            onClick={() => { signOut(); navigate("/login"); }}
            className="px-3 py-2 rounded-lg bg-slate-800 text-white text-sm hover:bg-slate-700"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}
