import { useEffect, useState } from "react";
import { apiFetch, type Workspace } from "../api/client";
import { JobDescriptionPage } from "./JobDescriptionPage";
import { ProfilePage } from "./ProfilePage";

export function WorkspacePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  async function refresh() {
    setWorkspaces(await apiFetch<Workspace[]>("/api/workspaces"));
  }

  useEffect(() => { void refresh(); }, []);

  if (activeId) {
    return <section><button type="button" onClick={() => setActiveId(null)}>Back to sessions</button><JobDescriptionPage workspaceId={activeId} /><ProfilePage workspaceId={activeId} /></section>;
  }

  return <section><h2>Your resume sessions</h2><p>Each session has its own job description and resume, using your shared profile data.</p><JobDescriptionPage onCreated={refresh} /><ul>{workspaces.map((workspace) => <li key={workspace.id}><button type="button" onClick={() => setActiveId(workspace.id)}>{workspace.name}</button></li>)}</ul></section>;
}
