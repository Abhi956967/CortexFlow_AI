import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { 
  User, 
  Mail, 
  Lock, 
  ShieldCheck, 
  Coins, 
  Sparkles, 
  LogOut, 
  X, 
  Check, 
  AlertCircle,
  Save,
  KeyRound,
  Trash2,
  Activity,
  Laptop
} from "lucide-react";
import api from "../utils/axios";
import { setUserData } from "../redux/user.slice";

export default function ProfileModal({ isOpen, onClose }) {
  const { userData } = useSelector((state) => state.user);
  const dispatch = useDispatch();

  const [activeTab, setActiveTab] = useState("profile"); // 'profile' | 'security' | 'usage'
  const [name, setName] = useState(userData?.name || "");
  const [avatar, setAvatar] = useState(userData?.avatar || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [deleteConfirmPassword, setDeleteConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: "", text: "" });

  if (!isOpen || !userData) return null;

  const AVATAR_PRESETS = [
    "https://api.dicebear.com/7.x/bottts/svg?seed=Cortex",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Nova",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Quantum",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Apex",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Cipher",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Vortex",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Zenith",
    "https://api.dicebear.com/7.x/bottts/svg?seed=Echo"
  ];

  // 1. Update Profile
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg({ type: "", text: "" });
    try {
      const { data } = await api.put("/api/auth/profile", {
        name: name.trim(),
        avatar: avatar
      });
      dispatch(setUserData({ ...userData, ...data }));
      setStatusMsg({ type: "success", text: "Profile updated successfully!" });
    } catch (err) {
      setStatusMsg({
        type: "error",
        text: err.response?.data?.detail || "Failed to update profile."
      });
    } finally {
      setLoading(false);
    }
  };

  // 2. Change Password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setStatusMsg({ type: "", text: "" });
    if (!currentPassword || !newPassword) {
      setStatusMsg({ type: "error", text: "Please enter all password fields." });
      return;
    }
    if (newPassword.length < 6) {
      setStatusMsg({ type: "error", text: "New password must be at least 6 characters." });
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setStatusMsg({ type: "error", text: "New passwords do not match." });
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword
      });
      setStatusMsg({ type: "success", text: data.message });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err) {
      setStatusMsg({
        type: "error",
        text: err.response?.data?.detail || "Failed to change password."
      });
    } finally {
      setLoading(false);
    }
  };

  // 3. Logout
  const handleLogout = async () => {
    try {
      await api.post("/api/auth/logout");
    } catch (err) {
      console.log(err);
    } finally {
      dispatch(setUserData(null));
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-[480px] bg-[#11131a] border border-white/[0.09] rounded-2xl p-6 sm:p-7 shadow-2xl shadow-indigo-950/40 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Ambient Glow */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-500 hover:text-slate-200 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors cursor-pointer"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-5">
          <div className="relative">
            <img
              src={avatar || userData.avatar || "https://api.dicebear.com/7.x/bottts/svg?seed=Cortex"}
              alt={userData.name}
              className="w-13 h-13 rounded-2xl object-cover border-2 border-indigo-500/30 shadow-lg shadow-indigo-500/20 bg-[#171923]"
            />
            <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-[#11131a]" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              {userData.name}
              {userData.is_verified && (
                <ShieldCheck size={16} className="text-emerald-400" title="Verified Account" />
              )}
            </h2>
            <p className="text-xs text-slate-400">{userData.email}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="grid grid-cols-3 p-1 bg-white/[0.03] border border-white/[0.06] rounded-xl mb-4">
          {[
            { id: "profile", label: "Profile" },
            { id: "security", label: "Security" },
            { id: "usage", label: "Usage & Plan" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setStatusMsg({ type: "", text: "" }); }}
              className={`py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${
                activeTab === tab.id
                  ? "bg-indigo-600/90 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Status Message */}
        {statusMsg.text && (
          <div className={`flex items-start gap-2.5 p-3 rounded-xl text-xs mb-4 ${
            statusMsg.type === "success"
              ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-300"
              : "bg-rose-500/10 border border-rose-500/20 text-rose-300"
          }`}>
            {statusMsg.type === "success" ? (
              <Check size={15} className="shrink-0 mt-0.5 text-emerald-400" />
            ) : (
              <AlertCircle size={15} className="shrink-0 mt-0.5 text-rose-400" />
            )}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* ── TAB 1: PROFILE & AVATAR ── */}
        {activeTab === "profile" && (
          <form onSubmit={handleUpdateProfile} className="space-y-3.5">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Choose AI Avatar
              </label>
              <div className="grid grid-cols-8 gap-1.5">
                {AVATAR_PRESETS.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setAvatar(preset)}
                    className={`p-1 rounded-xl bg-white/[0.04] border transition cursor-pointer hover:bg-white/[0.08] ${
                      (avatar || userData.avatar) === preset
                        ? "border-indigo-500 ring-2 ring-indigo-500/40"
                        : "border-white/[0.08]"
                    }`}
                  >
                    <img src={preset} alt={`Avatar ${idx}`} className="w-full h-7 object-cover rounded-lg" />
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Display Name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 outline-none transition"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition cursor-pointer disabled:opacity-50"
              >
                <Save size={14} />
                {loading ? "Saving..." : "Save Profile"}
              </button>

              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition cursor-pointer"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          </form>
        )}

        {/* ── TAB 2: SECURITY & PASSWORD ── */}
        {activeTab === "security" && (
          <form onSubmit={handleChangePassword} className="space-y-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Current Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                New Password
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 outline-none transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 mt-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition cursor-pointer disabled:opacity-50"
            >
              <Save size={14} />
              {loading ? "Updating..." : "Update Password"}
            </button>
          </form>
        )}

        {/* ── TAB 3: USAGE & SESSIONS ── */}
        {activeTab === "usage" && (
          <div className="space-y-3.5">
            <div className="p-3.5 bg-white/[0.03] border border-white/[0.06] rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Credits Remaining</span>
                <span className="text-sm font-bold text-indigo-400">{userData.credits || 100} / 100</span>
              </div>
              <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 w-[95%] rounded-full" />
              </div>
              <p className="text-[11px] text-slate-500">Resets on the 1st of every month.</p>
            </div>

            <div className="p-3.5 bg-white/[0.03] border border-white/[0.06] rounded-xl space-y-2">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Laptop size={14} className="text-indigo-400" /> Active Session
              </span>
              <p className="text-xs text-slate-400">Current Web Session (Chrome on Windows)</p>
              <span className="inline-block text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                Active Now
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
