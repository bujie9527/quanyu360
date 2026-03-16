import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  getToken,
  setToken,
  clearToken,
  getUser,
  setUser,
  isAuthenticated,
  getAuthHeaders,
} from "@/lib/auth";

/** In-memory localStorage mock (Node 22+ restricts real localStorage). */
function createStorage() {
  const store: Record<string, string> = {};
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => {
      store[k] = v;
    },
    removeItem: (k: string) => {
      delete store[k];
    },
    clear: () => {
      Object.keys(store).forEach((k) => delete store[k]);
    },
    get length() {
      return Object.keys(store).length;
    },
    key: () => null,
  };
}

describe("auth", () => {
  let storage: ReturnType<typeof createStorage>;

  beforeEach(() => {
    storage = createStorage();
    vi.stubGlobal("localStorage", storage);
    vi.stubGlobal("window", { localStorage: storage });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("isAuthenticated returns false when no token", () => {
    expect(isAuthenticated()).toBe(false);
  });

  it("isAuthenticated returns true when token exists", () => {
    setToken("abc123");
    expect(isAuthenticated()).toBe(true);
  });

  it("getAuthHeaders returns empty object when no token", () => {
    expect(getAuthHeaders()).toEqual({});
  });

  it("getAuthHeaders returns Bearer header when token exists", () => {
    setToken("jwt-xyz");
    expect(getAuthHeaders()).toEqual({ Authorization: "Bearer jwt-xyz" });
  });

  it("setToken and getToken roundtrip", () => {
    setToken("token123");
    expect(getToken()).toBe("token123");
  });

  it("clearToken removes token and user", () => {
    setToken("t");
    setUser({ id: "1", tenant_id: "t1", tenant_slug: "demo", email: "a@b.com" });
    clearToken();
    expect(getToken()).toBe(null);
    expect(getUser()).toBe(null);
  });

  it("getUser returns null when no user stored", () => {
    expect(getUser()).toBe(null);
  });

  it("getUser returns parsed user when valid JSON stored", () => {
    const user = { id: "1", tenant_id: "t1", tenant_slug: "demo", email: "a@b.com" };
    setUser(user);
    expect(getUser()).toEqual(user);
  });
});
