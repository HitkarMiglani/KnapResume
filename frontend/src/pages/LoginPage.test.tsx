import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LoginPage } from "./LoginPage";
import { AuthProvider } from "../auth/AuthContext";
import * as client from "../api/client";

function renderLoginPage(onSwitchToRegister = vi.fn()) {
  render(
    <AuthProvider>
      <LoginPage onSwitchToRegister={onSwitchToRegister} />
    </AuthProvider>,
  );
}

describe("LoginPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits the entered credentials", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(apiFetchSpy).toHaveBeenCalledWith("/api/auth/login", {
      method: "POST",
      body: { email: "a@example.com", password: "password123" },
    });
  });

  it("shows an error message when login fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockRejectedValueOnce(new client.ApiError(401, "invalid credentials"));
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("invalid credentials");
  });

  it("calls onSwitchToRegister when the toggle button is clicked", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch").mockRejectedValueOnce(new client.ApiError(401, "not authenticated"));
    const onSwitchToRegister = vi.fn();
    renderLoginPage(onSwitchToRegister);

    await user.click(screen.getByText("Need an account? Register"));

    expect(onSwitchToRegister).toHaveBeenCalledOnce();
  });
});
