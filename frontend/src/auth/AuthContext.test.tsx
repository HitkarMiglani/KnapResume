import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";
import * as client from "../api/client";

function Consumer() {
  const { session, login, register, logout } = useAuth();
  return (
    <div>
      <p data-testid="session">{session ? session.email : "anonymous"}</p>
      <button onClick={() => void login("a@example.com", "password123")}>login</button>
      <button onClick={() => void register("a@example.com", "password123")}>register</button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("throws when useAuth is used outside an AuthProvider", () => {
    function BareConsumer() {
      useAuth();
      return null;
    }
    expect(() => render(<BareConsumer />)).toThrow("useAuth must be used within an AuthProvider");
  });

  it("stores the session returned by login", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockResolvedValueOnce({
        user_id: "u1",
        email: "a@example.com",
        csrf_token: "csrf-1",
      });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await user.click(screen.getByText("login"));

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("a@example.com"));
  });

  it("stores the session returned by register", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockResolvedValueOnce({
        user_id: "u2",
        email: "a@example.com",
        csrf_token: "csrf-2",
      });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await user.click(screen.getByText("register"));

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("a@example.com"));
  });

  it("clears the session on logout and sends the CSRF token", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" })
      .mockResolvedValueOnce(undefined);

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await user.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("a@example.com"));

    await user.click(screen.getByText("logout"));

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("anonymous"));
    expect(apiFetchSpy).toHaveBeenLastCalledWith("/api/auth/logout", {
      method: "POST",
      csrfToken: "csrf-1",
    });
  });

  it("does not call the logout endpoint when there is no active session", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"));

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("anonymous"));
    apiFetchSpy.mockClear();

    await user.click(screen.getByText("logout"));

    expect(apiFetchSpy).not.toHaveBeenCalled();
  });

  it("restores an existing session on mount", async () => {
    vi.spyOn(client, "apiFetch").mockResolvedValueOnce({
      user_id: "u3",
      email: "restored@example.com",
      csrf_token: "csrf-3",
    });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("session")).toHaveTextContent("restored@example.com"),
    );
  });
});
