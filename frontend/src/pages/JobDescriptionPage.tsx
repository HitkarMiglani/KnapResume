import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiError, apiFetch, type CompletenessScore, type JobDescription } from "../api/client";

export function JobDescriptionPage({ workspaceId, onCreated }: { workspaceId?: string; onCreated?: () => void }) {
  const { session } = useAuth();
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [completeness, setCompleteness] = useState<CompletenessScore | null>(null);
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const [jds, score] = await Promise.all([
      workspaceId
        ? apiFetch<{ job_description: JobDescription | null }>(`/api/workspaces/${workspaceId}`).then(
            (workspace) => (workspace.job_description ? [workspace.job_description] : []),
          )
        : apiFetch<JobDescription[]>("/api/job-descriptions"),
      apiFetch<CompletenessScore>("/api/profile/completeness"),
    ]);
    setJobDescriptions(jds);
    setCompleteness(score);
  }

  useEffect(() => {
    void refresh();
  }, [workspaceId]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await apiFetch<JobDescription>("/api/job-descriptions", {
        method: "POST",
        body: { raw_text: rawText, ...(workspaceId ? { workspace_id: workspaceId } : {}) },
        csrfToken: session?.csrf_token,
      });
      setRawText("");
      await refresh();
      onCreated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "could not add job description");
    }
  }

  async function handleDelete(id: string) {
    try {
      await apiFetch(`/api/job-descriptions/${id}`, {
        method: "DELETE",
        csrfToken: session?.csrf_token,
      });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "could not delete job description");
    }
  }

  return (
    <div>
      <h2>{workspaceId ? "Target job" : "Job descriptions"}</h2>
      {!workspaceId && <p>Step 2: create a session from a job description, then attach its separate resume.</p>}
      <form onSubmit={handleSubmit}>
        <label htmlFor="jd_raw_text">Job description</label>
        <textarea
          id="jd_raw_text"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          required
        />
        <button type="submit">Add</button>
        {error && <p role="alert">{error}</p>}
      </form>
      {completeness && (
        <div>
          <h3>Profile completeness</h3>
          <ul>
            <li>Experience: {completeness.experience.toFixed(2)}</li>
            <li>Project: {completeness.project.toFixed(2)}</li>
            <li>Education: {completeness.education.toFixed(2)}</li>
            <li>Skill: {completeness.skill.toFixed(2)}</li>
            <li>Overall: {completeness.overall.toFixed(2)}</li>
          </ul>
        </div>
      )}
      <ul>
        {jobDescriptions.map((jd) => (
          <li key={jd.id}>
            <p>{jd.raw_text}</p>
            <p>Skills: {jd.skills.join(", ")}</p>
            <p>Keywords: {jd.keywords.join(", ")}</p>
            <p>Seniority: {jd.seniority ?? "unknown"}</p>
            <button type="button" onClick={() => void handleDelete(jd.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
