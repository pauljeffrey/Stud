/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // Allow any site to embed this app in an iframe.
          // X-Frame-Options is intentionally omitted — its only standard "allow-all"
          // behaviour is the absence of the header. CSP frame-ancestors is the
          // modern replacement and takes precedence in all current browsers.
          {
            key: "Content-Security-Policy",
            value: "frame-ancestors https://www.aletheia.com.ng",
          },
        ],
      },
    ];
  },
}

export default nextConfig