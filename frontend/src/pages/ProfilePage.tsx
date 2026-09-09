import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiError, apiFetch, SECTIONS, type Bullet, type Section, type ResumeImport, type ResumeImportDetail } from "../api/client";

export function ProfilePage() {
  const { session } = useAuth();
  const [bullets, setBullets] = useState<Bullet[]>([]);
  const [section, setSection] = useState<Section>(SECTIONS[0]);
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Resume Ingestion States
  const [imports, setImports] = useState<ResumeImport[]>([]);
  const [uploadError, setUploadError] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);

  async function refresh() {
    const result = await apiFetch<Bullet[]>("/api/bullets");
    setBullets(result);
  }

  async function refreshImports() {
    const result = await apiFetch<ResumeImport[]>("/api/profile/imports");
    setImports(result);
  }

  useEffect(() => {
    void refresh();
    void refreshImports();
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError("");
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) {
      setFile(null);
      return;
    }

    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setUploadError("Invalid file type. Only .pdf and .docx are supported.");
      setFile(null);
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setUploadError("File size exceeds 5MB limit.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  async function handleUploadSubmit(event: React.FormEvent) {
    event.preventDefault();
    setUploadError("");

    if (!file) {
      setUploadError("Please select a file to upload.");
      return;
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setUploadError("Invalid file type. Only .pdf and .docx are supported.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setUploadError("File size exceeds 5MB limit.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      await apiFetch<ResumeImportDetail>("/api/profile/import", {
        method: "POST",
        body: formData,
        csrfToken: session?.csrf_token,
      });

      setFile(null);
      const fileInput = document.getElementById("resume-file-input") as HTMLInputElement;
      if (fileInput) {
        fileInput.value = "";
      }

      await refresh();
      await refreshImports();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "could not upload file");
    }
  }

  async function handleDeleteImport(id: string) {
    try {
      await apiFetch(`/api/profile/imports/${id}`, {
        method: "DELETE",
        csrfToken: session?.csrf_token,
      });
      await refresh();
      await refreshImports();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "could not delete import");
    }
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

      <div style={{ marginTop: "2rem" }}>
        <h3>Import resume</h3>
        <form onSubmit={handleUploadSubmit}>
          <label htmlFor="resume-file-input">Select PDF or DOCX file</label>
          <input
            id="resume-file-input"
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
          />
          <button type="submit">Upload Resume</button>
          {uploadError && <p id="upload-error" role="alert" style={{ color: "red" }}>{uploadError}</p>}
        </form>
      </div>

      <div style={{ marginTop: "2rem" }}>
        <h3>Resume imports</h3>
        {imports.length === 0 ? (
          <p>No active resume imports.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Created At</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {imports.map((imp) => (
                <tr key={imp.id}>
                  <td>{imp.filename}</td>
                  <td>{imp.file_type}</td>
                  <td>{imp.created_at}</td>
                  <td>{imp.status}</td>
                  <td>
                    <button
                      type="button"
                      onClick={() => void handleDeleteImport(imp.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
