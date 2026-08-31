import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "./client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends GET requests without a CSRF header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch<{ ok: boolean }>("/api/auth/session");

    expect(result).toEqual({ ok: true });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["X-CSRF-Token"]).toBeUndefined();
    expect(init.credentials).toBe("same-origin");
  });

  it("throws without hitting the network when a state-changing request has no CSRF token", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/api/auth/logout", { method: "POST" })).rejects.toThrow(ApiError);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends the CSRF header for state-changing requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch("/api/auth/logout", { method: "POST", csrfToken: "token-123" });

    expect(result).toBeUndefined();
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["X-CSRF-Token"]).toBe("token-123");
  });

  it("raises an ApiError with the server-provided detail on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "invalid credentials" }), { status: 401 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/api/auth/login", { method: "POST", csrfToken: "t" })).rejects.toMatchObject({
      status: 401,
      message: "invalid credentials",
    });
  });
});
