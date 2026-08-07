import axios from "axios";

// Clean API Base URL configuration for Production VPS & Netlify
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://a12tqtb1zoht2490gpbgg0ea.72.62.148.31.sslip.io/api/v1";


export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
