import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for Docker — produces a standalone server.js instead of requiring next start
  output: "standalone",
};

export default nextConfig;
