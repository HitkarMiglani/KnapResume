import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RegisterPage } from "./RegisterPage";
import { AuthProvider } from "../auth/AuthContext";
import * as client from "../api/client";

function renderRegisterPage(onSwitchToLogin = vi.fn()) {
  render(
    <AuthProvider>
      <RegisterPage onSwitchToLogin={onSwitchToLogin} />
    </AuthProvider>,
  );
}

describe("RegisterPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits the entered credentials", async () => {
    const user = userEvent.setup();
    const apiFetchSpy = vi
      .spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockResolvedValueOnce({ user_id: "u1", email: "a@example.com", csrf_token: "csrf-1" });
    renderRegisterPage();

    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(apiFetchSpy).toHaveBeenCalledWith("/api/auth/register", {
      method: "POST",
      body: { email: "a@example.com", password: "password123" },
    });
  });

  it("shows an error message when registration fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch")
      .mockRejectedValueOnce(new client.ApiError(401, "not authenticated"))
      .mockRejectedValueOnce(new client.ApiError(409, "email already registered"));
    renderRegisterPage();

    await user.type(screen.getByLabelText("Email"), "dup@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("email already registered");
  });

  it("calls onSwitchToLogin when the toggle button is clicked", async () => {
    const user = userEvent.setup();
    vi.spyOn(client, "apiFetch").mockRejectedValueOnce(new client.ApiError(401, "not authenticated"));
    const onSwitchToLogin = vi.fn();
    renderRegisterPage(onSwitchToLogin);

    await user.click(screen.getByText("Already have an account? Log in"));

    expect(onSwitchToLogin).toHaveBeenCalledOnce();
  });
});
