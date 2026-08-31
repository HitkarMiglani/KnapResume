import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProfilePage } from "./ProfilePage";
import { AuthProvider } from "../auth/AuthContext";
import * as client from "../api/client";

function renderProfilePage() {
  render(
    <AuthProvider>
      <ProfilePage />
    </AuthProvider>,
  );
}

describe("ProfilePage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("lists existing bullets after loading", async () => {
    vi.spyOn(client, "apiFetch")
      .mockResolvedValueOnce([
        {
          id: "b1",
          section: "skill",
          raw_text: "Python",
          normalized_text: "Python",
          created_at: "2026-01-01T00:00:00Z",
        },
      ])
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });

    renderProfilePage();

    expect(await screen.findByText("[skill] Python")).toBeInTheDocument();
  });

  it("submits a new fact with the CSRF token and refreshes the list", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockResolvedValueOnce({
        id: "b2",
        section: "skill",
        raw_text: "Go",
        normalized_text: "Go",
        created_at: "2026-01-01T00:00:00Z",
      })
      .mockResolvedValueOnce([
        {
          id: "b2",
          section: "skill",
          raw_text: "Go",
          normalized_text: "Go",
          created_at: "2026-01-01T00:00:00Z",
        },
      ]);

    renderProfilePage();
    await screen.findByText("Profile facts");
    await waitFor(() => expect(apiFetchSpy).toHaveBeenCalledTimes(2));

    await user.type(screen.getByLabelText("Fact"), "Go");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(apiFetchSpy).toHaveBeenCalledWith("/api/bullets", {
      method: "POST",
      body: { section: "experience", raw_text: "Go" },
      csrfToken: "csrf-1",
    });
    expect(await screen.findByText("[skill] Go")).toBeInTheDocument();
  });

  it("shows an error message when adding a fact fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockRejectedValueOnce(new client.ApiError(422, "invalid fact"));

    renderProfilePage();
    await screen.findByText("Profile facts");

    await user.type(screen.getByLabelText("Fact"), "x");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("invalid fact");
  });
});
