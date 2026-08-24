import { useState } from "react";
import { useSelector } from "react-redux";
import ArtifactPanel from "../components/ArtifactPanel";
import ChatArea from "../components/ChatArea";
import Sidebar from "../components/Sidebar";
import AuthModal from "../components/AuthModal";

function Home() {
  const { userData } = useSelector((state) => state.user);
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <div className="h-screen flex bg-[#0d0f14] text-white overflow-hidden">
      <Sidebar />
      <ChatArea />
      <ArtifactPanel />

      {/* Show AuthModal if user is not logged in */}
      {!userData && (
        <AuthModal
          isOpen={!userData || showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialView="login"
        />
      )}
    </div>
  );
}

export default Home;