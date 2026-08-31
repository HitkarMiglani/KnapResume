import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiError, apiFetch, SECTIONS, type Bullet, type Section } from "../api/client";

export function ProfilePage() {
  const { session } = useAuth();
  const [bullets, setBullets] = useState<Bullet[]>([]);
  const [section, setSection] = useState<Section>(SECTIONS[0]);
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const result = await apiFetch<Bullet[]>("/api/bullets");
    setBullets(result);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await apiFetch<Bullet>("/api/bullets", {
        method: "POST",
        body: { section, raw_text: rawText },
        csrfToken: session?.csrf_token,
      });
      setRawText("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "could not add fact");
    }
  }

  async function handleDelete(id: string) {
    await apiFetch(`/api/bullets/${id}`, { method: "DELETE", csrfToken: session?.csrf_token });
    await refresh();
  }

  return (
    <div>
      <h2>Profile facts</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="section">Section</label>
        <select
          id="section"
          value={section}
          onChange={(e) => setSection(e.target.value as Section)}
        >
          {SECTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <label htmlFor="raw_text">Fact</label>
        <input id="raw_text" value={rawText} onChange={(e) => setRawText(e.target.value)} required />
        <button type="submit">Add</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <ul>
        {bullets.map((bullet) => (
          <li key={bullet.id}>
            <span>
              [{bullet.section}] {bullet.normalized_text}
            </span>
            <button type="button" onClick={() => void handleDelete(bullet.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
