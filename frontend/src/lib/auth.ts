import { api } from "@/lib/api";

export type AuthUser = {
  id: string;
  arabic_name: string;
  phone_number: string;
  grade_level?: string | null;
  role?: string;
};

const USER_INFO_KEY = "user_info";

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
  if (!user) {
    localStorage.removeItem(USER_INFO_KEY);
    return;
  }
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
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
