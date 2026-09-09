import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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

  it("lists existing bullets and imports after loading", async () => {
    vi.spyOn(client, "apiFetch").mockImplementation((path) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/bullets") {
        return Promise.resolve([
          {
            id: "b1",
            section: "skill",
            raw_text: "Python",
            normalized_text: "Python",
            created_at: "2026-01-01T00:00:00Z",
          },
        ]);
      }
      if (path === "/api/profile/imports") {
        return Promise.resolve([
          {
            id: "imp-1",
            user_id: "u1",
            filename: "resume.pdf",
            file_type: "pdf",
            status: "completed",
            created_at: "2026-01-01T12:00:00Z",
          },
        ]);
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();

    expect(await screen.findByText("[skill] Python")).toBeInTheDocument();
    expect(await screen.findByText("resume.pdf")).toBeInTheDocument();
    expect(screen.getByText("pdf")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("submits a new fact with the CSRF token and refreshes the list", async () => {
    const user = userEvent.setup();
    let bullets = [] as any[];

    const apiFetchSpy = vi.spyOn(client, "apiFetch").mockImplementation((path, options) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/profile/imports") {
        return Promise.resolve([]);
      }
      if (path === "/api/bullets") {
        if (options?.method === "POST") {
          const body = options.body as any;
          const b = {
            id: "b2",
            section: body.section,
            raw_text: body.raw_text,
            normalized_text: body.raw_text,
            created_at: "2026-01-01T00:00:00Z",
          };
          bullets.push(b);
          return Promise.resolve(b);
        }
        return Promise.resolve(bullets);
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();
    await screen.findByText("Profile facts");

    await user.type(screen.getByLabelText("Fact"), "Go");
    await user.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/bullets", {
        method: "POST",
        body: { section: "experience", raw_text: "Go" },
        csrfToken: "csrf-1",
      });
    });
    expect(await screen.findByText("[experience] Go")).toBeInTheDocument();
  });

  it("shows an error message when adding a fact fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch").mockImplementation((path, options) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/bullets") {
        if (options?.method === "POST") {
          return Promise.reject(new client.ApiError(422, "invalid fact"));
        }
        return Promise.resolve([]);
      }
      if (path === "/api/profile/imports") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();
    await screen.findByText("Profile facts");

    await user.type(screen.getByLabelText("Fact"), "x");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("invalid fact");
  });

  it("shows validation error on file exceeding 5MB or invalid extension", async () => {
    vi.spyOn(client, "apiFetch").mockImplementation((path) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/bullets") {
        return Promise.resolve([]);
      }
      if (path === "/api/profile/imports") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();

    const fileInput = screen.getByLabelText("Select PDF or DOCX file");

    // Invalid extension
    const invalidFile = new File(["dummy content"], "resume.txt", { type: "text/plain" });
    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid file type");

    // Clear and try too large
    const hugeFile = new File([new ArrayBuffer(6 * 1024 * 1024)], "huge.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [hugeFile] } });

    expect(await screen.findByRole("alert")).toHaveTextContent("File size exceeds 5MB limit");
  });

  it("uploads a valid file and refreshes bullets and imports", async () => {
    const user = userEvent.setup();
    let bulletsCount = 0;
    let importsCount = 0;

    const apiFetchSpy = vi.spyOn(client, "apiFetch").mockImplementation((path, _options) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/bullets") {
        if (bulletsCount > 0) {
          return Promise.resolve([
            { id: "b2", section: "skill", raw_text: "Python", normalized_text: "Python", created_at: "" },
          ]);
        }
        return Promise.resolve([]);
      }
      if (path === "/api/profile/imports") {
        if (importsCount > 0) {
          return Promise.resolve([
            { id: "imp-1", user_id: "u1", filename: "resume.pdf", file_type: "pdf", status: "completed", created_at: "" },
          ]);
        }
        return Promise.resolve([]);
      }
      if (path === "/api/profile/import") {
        bulletsCount++;
        importsCount++;
        return Promise.resolve({
          id: "imp-1",
          filename: "resume.pdf",
          file_type: "pdf",
          status: "completed",
          created_at: "",
          bullets: [],
        });
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();
    await screen.findByText("Profile facts");

    const fileInput = screen.getByLabelText("Select PDF or DOCX file");
    const validFile = new File(["dummy content"], "resume.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [validFile] } });

    const uploadButton = screen.getByRole("button", { name: "Upload Resume" });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/profile/import", {
        method: "POST",
        body: expect.any(FormData),
        csrfToken: "csrf-1",
      });
    });

    expect(await screen.findByText("[skill] Python")).toBeInTheDocument();
    expect(await screen.findByText("resume.pdf")).toBeInTheDocument();
  });

  it("deletes a resume import and refreshes both lists", async () => {
    const user = userEvent.setup();
    let isDeleted = false;

    const apiFetchSpy = vi.spyOn(client, "apiFetch").mockImplementation((path, options) => {
      if (path === "/api/auth/session") {
        return Promise.resolve({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
      }
      if (path === "/api/bullets") {
        return Promise.resolve([]);
      }
      if (path === "/api/profile/imports") {
        if (isDeleted) {
          return Promise.resolve([]);
        }
        return Promise.resolve([
          {
            id: "imp-123",
            user_id: "u1",
            filename: "resume.pdf",
            file_type: "pdf",
            status: "completed",
            created_at: "2026-09-09",
          },
        ]);
      }
      if (path === "/api/profile/imports/imp-123" && options?.method === "DELETE") {
        isDeleted = true;
        return Promise.resolve(undefined);
      }
      return Promise.reject(new Error(`Unhandled path: ${path}`));
    });

    renderProfilePage();

    expect(await screen.findByText("resume.pdf")).toBeInTheDocument();

    const deleteBtn = screen.getByRole("button", { name: "Delete" });
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(apiFetchSpy).toHaveBeenCalledWith("/api/profile/imports/imp-123", {
        method: "DELETE",
        csrfToken: "csrf-1",
      });
    });

    await waitFor(() => {
      expect(screen.queryByText("resume.pdf")).not.toBeInTheDocument();
    });
  });
});
