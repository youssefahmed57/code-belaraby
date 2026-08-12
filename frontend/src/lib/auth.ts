import { api } from "@/lib/api";

export type AuthUser = {
  id: string;
  arabic_name: string;
  grade_level?: string | null;
  role?: string;
};

const USER_INFO_KEY = "user_info";

function sanitizeUserForStorage(user: AuthUser | null): AuthUser | null {
  if (!user) return null;
  return {
    id: user.id,
    arabic_name: user.arabic_name,
    grade_level: user.grade_level ?? null,
    role: user.role,
  };
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_INFO_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    localStorage.removeItem(USER_INFO_KEY);
    return null;
  }
}

export function setStoredUser(user: AuthUser | null): void {
  if (typeof window === "undefined") return;
  const sanitizedUser = sanitizeUserForStorage(user);
  if (!sanitizedUser) {
    localStorage.removeItem(USER_INFO_KEY);
    return;
  }
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(sanitizedUser));
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  try {
    const response = await api.get("/auth/me");
    const user = response.data as AuthUser;
    setStoredUser(user);
    return user;
  } catch {
    setStoredUser(null);
    return null;
  }
}

export async function logoutCurrentSession(allDevices = false): Promise<void> {
  const endpoint = allDevices ? "/auth/logout-all" : "/auth/logout";
  await api.post(endpoint);
  setStoredUser(null);
}
