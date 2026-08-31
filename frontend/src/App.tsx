import { useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ProfilePage } from "./pages/ProfilePage";

function AuthenticatedApp() {
  const { session, loading, logout } = useAuth();
  const [view, setView] = useState<"login" | "register">("login");

  if (loading) {
    return <p>Loading…</p>;
  }

  if (!session) {
    return view === "login" ? (
      <LoginPage onSwitchToRegister={() => setView("register")} />
    ) : (
      <RegisterPage onSwitchToLogin={() => setView("login")} />
    );
  }

  return (
    <div>
      <p>Signed in as {session.email}</p>
      <button type="button" onClick={() => void logout()}>
        Log out
      </button>
      <ProfilePage />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}
