/** @type {import('next').NextConfig} */
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "";
const normalizedApiUrl = rawApiUrl.replace(/\/api\/v1\/?$/, "");
const backendOrigin = normalizedApiUrl || process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";
const isRelativeApi = rawApiUrl.startsWith("/");
const isDev = process.env.NODE_ENV === "development";

const connectSources = ["'self'"];
if (normalizedApiUrl && !isRelativeApi) {
  connectSources.push(normalizedApiUrl);
}
if (process.env.NEXT_PUBLIC_APP_URL) {
  connectSources.push(process.env.NEXT_PUBLIC_APP_URL.replace(/\/$/, ""));
}
if (isDev) {
  connectSources.push("ws://127.0.0.1:3000", "ws://localhost:3000");
}

const mediaSources = ["'self'", "blob:"];
if (process.env.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN) {
  mediaSources.push(`https://${process.env.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN}`);
}
if (process.env.BUNNY_STREAM_LIBRARY_ID) {
  mediaSources.push("https://iframe.mediadelivery.net", "https://video.bunnycdn.com");
}

const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""};
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob:;
  font-src 'self' data:;
  connect-src ${connectSources.join(" ")};
  media-src ${mediaSources.join(" ")};
  object-src 'none';
  base-uri 'self';
  frame-ancestors 'none';
  form-action 'self';
`.replace(/\s{2,}/g, " ").trim();

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    if (isRelativeApi) {
      return [];
    }
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendOrigin}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: cspHeader },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
