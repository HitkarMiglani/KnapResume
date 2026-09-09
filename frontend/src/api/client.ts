export type Bullet = {
  id: string;
  section: string;
  raw_text: string;
  normalized_text: string;
  created_at: string;
};

export type ResumeImport = {
  id: string;
  user_id: string;
  filename: string;
  file_type: string;
  status: string;
  created_at: string;
};

export type ResumeImportDetail = {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  created_at: string;
  bullets: Bullet[];
};

export type JobDescription = {
  id: string;
  raw_text: string;
  skills: string[];
  keywords: string[];
  seniority: string | null;
  created_at: string;
};

export type CompletenessScore = {
  experience: number;
  project: number;
  education: number;
  skill: number;
  overall: number;
};

export const SECTIONS = ["experience", "project", "education", "skill"] as const;
export type Section = (typeof SECTIONS)[number];

export type SessionInfo = {
  user_id: string;
  email: string;
  csrf_token: string;
};

const STATE_CHANGING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  options: { method?: string; body?: unknown; csrfToken?: string } = {},
): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = {};

  const isFormData = options.body instanceof FormData;
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (STATE_CHANGING_METHODS.has(method)) {
    if (!options.csrfToken) {
      throw new ApiError(0, "missing CSRF token for state-changing request");
    }
    headers["X-CSRF-Token"] = options.csrfToken;
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body !== undefined
      ? (isFormData ? (options.body as FormData) : JSON.stringify(options.body))
      : undefined,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, detail.detail ?? response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
