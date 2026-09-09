import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { JobDescriptionPage } from "./JobDescriptionPage";
import { AuthProvider } from "../auth/AuthContext";
import * as client from "../api/client";

function renderJobDescriptionPage() {
  render(
    <AuthProvider>
      <JobDescriptionPage />
    </AuthProvider>,
  );
}

const completeness = {
  experience: 0.5,
  project: 0.2,
  education: 1.0,
  skill: 0.4,
  overall: 0.525,
};

describe("JobDescriptionPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("lists existing job descriptions with skills/keywords/seniority after loading", async () => {
    vi.spyOn(client, "apiFetch")
      .mockResolvedValueOnce([
        {
          id: "jd1",
          raw_text: "Senior Python engineer",
          skills: ["python"],
          keywords: ["engineer"],
          seniority: "senior",
          created_at: "2026-01-01T00:00:00Z",
        },
      ])
      .mockResolvedValueOnce(completeness)
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });

    renderJobDescriptionPage();

    expect(await screen.findByText("Senior Python engineer")).toBeInTheDocument();
    expect(screen.getByText("Skills: python")).toBeInTheDocument();
    expect(screen.getByText("Keywords: engineer")).toBeInTheDocument();
    expect(screen.getByText("Seniority: senior")).toBeInTheDocument();
  });

  it("submits a new job description paste with CSRF token and refreshes the list", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(completeness)
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockResolvedValueOnce({
        id: "jd2",
        raw_text: "Go backend engineer",
        skills: ["go"],
        keywords: ["backend"],
        seniority: null,
        created_at: "2026-01-01T00:00:00Z",
      })
      .mockResolvedValueOnce([
        {
          id: "jd2",
          raw_text: "Go backend engineer",
          skills: ["go"],
          keywords: ["backend"],
          seniority: null,
          created_at: "2026-01-01T00:00:00Z",
        },
      ])
      .mockResolvedValueOnce(completeness);

    renderJobDescriptionPage();
    await screen.findByText("Job descriptions");
    await waitFor(() => expect(apiFetchSpy).toHaveBeenCalledTimes(3));

    await user.type(screen.getByLabelText("Job description"), "Go backend engineer");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(apiFetchSpy).toHaveBeenCalledWith("/api/job-descriptions", {
      method: "POST",
      body: { raw_text: "Go backend engineer" },
      csrfToken: "csrf-1",
    });
    expect(await screen.findByText("Go backend engineer")).toBeInTheDocument();
  });

  it("shows an error message on submit failure", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(completeness)
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockRejectedValueOnce(new client.ApiError(422, "raw_text too long"));

    renderJobDescriptionPage();
    await screen.findByText("Job descriptions");

    await user.type(screen.getByLabelText("Job description"), "x");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("raw_text too long");
  });

  it("delete removes an item and refreshes", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockResolvedValueOnce([
        {
          id: "jd1",
          raw_text: "Senior Python engineer",
          skills: ["python"],
          keywords: ["engineer"],
          seniority: "senior",
          created_at: "2026-01-01T00:00:00Z",
        },
      ])
      .mockResolvedValueOnce(completeness)
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(completeness);

    renderJobDescriptionPage();
    await screen.findByText("Senior Python engineer");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(apiFetchSpy).toHaveBeenCalledWith("/api/job-descriptions/jd1", {
      method: "DELETE",
      csrfToken: "csrf-1",
    });
    await waitFor(() =>
      expect(screen.queryByText("Senior Python engineer")).not.toBeInTheDocument(),
    );
  });

  it("renders completeness scores", async () => {
    vi.spyOn(client, "apiFetch")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(completeness)
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });

    renderJobDescriptionPage();

    expect(await screen.findByText("Profile completeness")).toBeInTheDocument();
    expect(screen.getByText("Experience: 0.50")).toBeInTheDocument();
    expect(screen.getByText("Project: 0.20")).toBeInTheDocument();
    expect(screen.getByText("Education: 1.00")).toBeInTheDocument();
    expect(screen.getByText("Skill: 0.40")).toBeInTheDocument();
    expect(screen.getByText("Overall: 0.53")).toBeInTheDocument();
  });
});
