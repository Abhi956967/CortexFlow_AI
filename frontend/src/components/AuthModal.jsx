import { useState } from "react";
import { useDispatch } from "react-redux";
import { 
  Mail, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Sparkles, 
  KeyRound, 
  CheckCircle2, 
  AlertCircle,
  Copy,
  Check,
  X
} from "lucide-react";
import { FaGoogle, FaGithub } from "react-icons/fa";
import api from "../utils/axios";
import { setUserData } from "../redux/user.slice";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider, githubProvider } from "../../firebase";

export default function AuthModal({ isOpen, onClose, initialView = "login" }) {
  const [view, setView] = useState(initialView); // 'login' | 'register' | 'forgot' | 'reset'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const dispatch = useDispatch();

  if (!isOpen) return null;

  // Password strength calculation
  const getPasswordStrength = (pwd) => {
    if (!pwd) return { score: 0, label: "", color: "bg-transparent" };
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 10) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    if (score <= 2) return { score: 1, label: "Weak", color: "bg-rose-500" };
    if (score <= 4) return { score: 2, label: "Medium", color: "bg-amber-500" };
    return { score: 3, label: "Strong", color: "bg-emerald-500" };
  };

  const strength = getPasswordStrength(password);

  const resetMessages = () => {
    setError("");
    setSuccessMsg("");
  };

  // 1. Handle Login
  const handleLogin = async (e) => {
    e?.preventDefault();
    resetMessages();
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/login", {
        email: email.trim(),
        password,
        remember_me: rememberMe
      });
      if (data?.user) {
        dispatch(setUserData(data.user));
        onClose();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Handle Register
  const handleRegister = async (e) => {
    e?.preventDefault();
    resetMessages();
    if (!name.trim() || !email.trim() || !password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/register", {
        name: name.trim(),
        email: email.trim(),
        password
      });
      if (data?.user) {
        dispatch(setUserData(data.user));
        onClose();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Email might already be taken.");
    } finally {
      setLoading(false);
    }
  };

  // 3. Handle Forgot Password
  const handleForgotPassword = async (e) => {
    e?.preventDefault();
    resetMessages();
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/forgot-password", { email: email.trim() });
      setSuccessMsg(data.message);
      if (data.reset_token) {
        setResetToken(data.reset_token);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to process request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Handle Reset Password
  const handleResetPassword = async (e) => {
    e?.preventDefault();
    resetMessages();
    if (!resetToken.trim() || !newPassword) {
      setError("Please enter both the reset token and your new password.");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/reset-password", {
        token: resetToken.trim(),
        new_password: newPassword
      });
      setSuccessMsg(data.message);
      setTimeout(() => {
        setView("login");
        setSuccessMsg("Password reset successfully! Please log in.");
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired reset token.");
    } finally {
      setLoading(false);
    }
  };

  // 5. Handle OAuth (Google / GitHub)
  const handleOAuth = async (providerName) => {
    resetMessages();
    setLoading(true);
    try {
      if (auth) {
        const provider = providerName === "github" ? githubProvider : googleProvider;
        const result = await signInWithPopup(auth, provider);
        const token = await result.user.getIdToken();
        
        const { data } = await api.post("/api/auth/oauth", {
          idToken: token,
          email: result.user.email,
          name: result.user.displayName || "OAuth User",
          avatar: result.user.photoURL
        });
        if (data?.user) {
          dispatch(setUserData(data.user));
          onClose();
        }
      } else {
        // Safe Guest Fallback
        handleGuestLogin();
      }
    } catch (err) {
      console.warn("OAuth popup error, using guest fallback:", err);
      handleGuestLogin();
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = () => {
    dispatch(
      setUserData({
        id: "cortex_user_1",
        name: "Cortex Guest",
        email: "guest@cortexflow.ai",
        credits: 100,
        plan: "free",
        is_verified: true
      })
    );
    onClose();
  };

  const copyResetToken = () => {
    if (resetToken) {
      navigator.clipboard.writeText(resetToken);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-[420px] bg-[#11131a] border border-white/[0.09] rounded-2xl p-6 sm:p-8 shadow-2xl shadow-indigo-950/40 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Glow ambient background */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-violet-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-500 hover:text-slate-200 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors"
        >
          <X size={18} />
        </button>

        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-700 flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-3">
            <Sparkles className="text-white w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">
            {view === "login" && "Welcome back"}
            {view === "register" && "Create your account"}
            {view === "forgot" && "Reset your password"}
            {view === "reset" && "Set new password"}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {view === "login" && "Enter your credentials to access CortexFlow AI"}
            {view === "register" && "Get started with 100 free AI computation credits"}
            {view === "forgot" && "Enter your email to receive recovery instructions"}
            {view === "reset" && "Create a secure password for your account"}
          </p>
        </div>

        {/* Tab Selector for Login / Register */}
        {(view === "login" || view === "register") && (
          <div className="grid grid-cols-2 p-1 bg-white/[0.03] border border-white/[0.06] rounded-xl mb-5">
            <button
              onClick={() => { setView("login"); resetMessages(); }}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                view === "login" 
                  ? "bg-indigo-600/90 text-white shadow-md shadow-indigo-600/30" 
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setView("register"); resetMessages(); }}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                view === "register" 
                  ? "bg-indigo-600/90 text-white shadow-md shadow-indigo-600/30" 
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign Up
            </button>
          </div>
        )}

        {/* Alert Notifications */}
        {error && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs mb-4">
            <AlertCircle size={15} className="shrink-0 mt-0.5 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs mb-4">
            <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* ── VIEW 1: LOGIN FORM ── */}
        {view === "login" && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => { setView("forgot"); resetMessages(); }}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400 hover:text-slate-300">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-white/20 bg-white/5 text-indigo-600 focus:ring-0"
                />
                Remember for 30 days
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 active:scale-[0.99] shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Signing In..." : "Sign In"}
              <ArrowRight size={15} />
            </button>
          </form>
        )}

        {/* ── VIEW 2: REGISTER FORM ── */}
        {view === "register" && (
          <form onSubmit={handleRegister} className="space-y-3.5">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>

              {/* Password strength bar */}
              {password && (
                <div className="mt-1.5 flex items-center gap-2">
                  <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden flex gap-1">
                    <div className={`h-full ${strength.score >= 1 ? strength.color : "bg-transparent"} flex-1 rounded-full transition-all`} />
                    <div className={`h-full ${strength.score >= 2 ? strength.color : "bg-transparent"} flex-1 rounded-full transition-all`} />
                    <div className={`h-full ${strength.score >= 3 ? strength.color : "bg-transparent"} flex-1 rounded-full transition-all`} />
                  </div>
                  <span className="text-[10px] font-medium text-slate-400">{strength.label}</span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 mt-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 active:scale-[0.99] shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Creating Account..." : "Create Account"}
              <ArrowRight size={15} />
            </button>
          </form>
        )}

        {/* ── VIEW 3: FORGOT PASSWORD ── */}
        {view === "forgot" && (
          <form onSubmit={handleForgotPassword} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Registered Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            {resetToken && (
              <div className="p-3.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl space-y-2">
                <p className="text-xs text-indigo-300 font-medium">Reset Token Generated:</p>
                <div className="flex items-center gap-2 bg-black/40 px-3 py-2 rounded-lg font-mono text-xs text-slate-200">
                  <span className="truncate flex-1">{resetToken}</span>
                  <button
                    type="button"
                    onClick={copyResetToken}
                    className="text-slate-400 hover:text-white p-1"
                  >
                    {copiedToken ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => { setView("reset"); resetMessages(); }}
                  className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 mt-1"
                >
                  Proceed to Reset Password &rarr;
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 active:scale-[0.99] shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Generating..." : "Generate Reset Instructions"}
              <KeyRound size={15} />
            </button>

            <button
              type="button"
              onClick={() => { setView("login"); resetMessages(); }}
              className="w-full text-center text-xs text-slate-400 hover:text-slate-200 mt-2"
            >
              &larr; Back to Sign In
            </button>
          </form>
        )}

        {/* ── VIEW 4: RESET PASSWORD ── */}
        {view === "reset" && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Reset Token
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="text"
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Paste reset token"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none font-mono transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-white/[0.03] border border-white/[0.08] focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 active:scale-[0.99] shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Updating..." : "Update Password"}
              <CheckCircle2 size={15} />
            </button>

            <button
              type="button"
              onClick={() => { setView("login"); resetMessages(); }}
              className="w-full text-center text-xs text-slate-400 hover:text-slate-200 mt-2"
            >
              &larr; Back to Sign In
            </button>
          </form>
        )}

        {/* ── Social Login Dividers & OAuth Buttons ── */}
        {(view === "login" || view === "register") && (
          <div className="mt-5 space-y-4">
            <div className="relative flex items-center justify-center">
              <div className="w-full border-t border-white/[0.08]" />
              <span className="absolute bg-[#11131a] px-3 text-[11px] uppercase font-semibold text-slate-500 tracking-wider">
                Or continue with
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleOAuth("google")}
                disabled={loading}
                className="flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-xs font-medium text-slate-200 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition cursor-pointer disabled:opacity-50"
              >
                <FaGoogle className="text-white" size={13} />
                Google
              </button>

              <button
                type="button"
                onClick={() => handleOAuth("github")}
                disabled={loading}
                className="flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-xs font-medium text-slate-200 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition cursor-pointer disabled:opacity-50"
              >
                <FaGithub className="text-white" size={14} />
                GitHub
              </button>
            </div>

            {/* Instant Guest Demo Access */}
            <button
              type="button"
              onClick={handleGuestLogin}
              className="w-full py-1.5 text-center text-[11.5px] text-slate-400 hover:text-indigo-300 font-medium transition cursor-pointer"
            >
              ⚡ Continue as Guest (Instant Access)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
