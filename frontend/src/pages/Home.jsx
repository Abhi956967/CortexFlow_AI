import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { FaGoogle, FaUserCircle } from "react-icons/fa";
import ArtifactPanel from "../components/ArtifactPanel";
import ChatArea from "../components/ChatArea";
import Sidebar from "../components/Sidebar";
import api from "../utils/axios";
import { setUserData } from "../redux/user.slice";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebase";

function Home() {
  const { userData } = useSelector((state) => state.user);
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);

  const loginWithToken = async (token) => {
    try {
      const { data } = await api.post(`/api/auth/login`, { token });
      if (data?.user) {
        dispatch(setUserData(data.user));
      }
    } catch (error) {
      console.warn("Backend auth login warning, using local session:", error);
      dispatch(
        setUserData({
          id: "guest_user",
          name: "Cortex User",
          email: "user@cortexflow.ai",
          credits: 100,
          plan: "free"
        })
      );
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      if (auth) {
        const result = await signInWithPopup(auth, googleProvider);
        const token = await result.user.getIdToken();
        await loginWithToken(token);
      } else {
        handleGuestLogin();
      }
    } catch (err) {
      console.warn("Google popup login failed, continuing as guest user:", err);
      handleGuestLogin();
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = () => {
    dispatch(
      setUserData({
        id: "cortex_user_1",
        name: "Cortex User",
        email: "user@cortexflow.ai",
        credits: 100,
        plan: "free"
      })
    );
  };

  return (
    <div className="h-screen flex bg-[#0d0f14] text-white overflow-hidden">
      <Sidebar />
      <ChatArea />
      <ArtifactPanel />

      {!userData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-[360px] bg-[#13151c] border border-white/[0.08] rounded-2xl p-7 flex flex-col gap-5 shadow-2xl">
            <div className="flex flex-col gap-1">
              <h2 className="text-[18px] font-semibold text-slate-100 tracking-tight flex items-center gap-2">
                🧠 Welcome to CortexFlow AI
              </h2>
              <p className="text-[13px] text-slate-400">
                Next-Gen Multi-Agent AI Platform
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 py-[11px] rounded-xl text-sm font-medium text-white bg-gradient-to-br from-indigo-500 to-violet-700 hover:from-indigo-400 hover:to-violet-600 active:from-indigo-600 active:to-violet-800 border border-indigo-500/30 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-150 cursor-pointer disabled:opacity-50"
              >
                <FaGoogle size={15} className="text-white" />
                {loading ? "Signing in..." : "Continue with Google"}
              </button>

              <button
                onClick={handleGuestLogin}
                className="w-full flex items-center justify-center gap-2 py-[10px] rounded-xl text-xs font-medium text-slate-300 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition-all cursor-pointer"
              >
                <FaUserCircle size={14} />
                Continue as Guest (Instant Access)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;