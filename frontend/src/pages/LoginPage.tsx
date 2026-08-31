import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

export function LoginPage({ onSwitchToRegister }: { onSwitchToRegister: () => void }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "login failed");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Log in</h1>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <label htmlFor="password">Password</label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit">Log in</button>
      {error && <p role="alert">{error}</p>}
      <button type="button" onClick={onSwitchToRegister}>
        Need an account? Register
      </button>
    </form>
  );
}
