import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

export function RegisterPage({ onSwitchToLogin }: { onSwitchToLogin: () => void }) {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await register(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "registration failed");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Register</h1>
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
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit">Register</button>
      {error && <p role="alert">{error}</p>}
      <button type="button" onClick={onSwitchToLogin}>
        Already have an account? Log in
      </button>
    </form>
  );
}
