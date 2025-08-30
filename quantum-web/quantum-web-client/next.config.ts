import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    dirs: [],
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  transpilePackages: [],
  swcMinify: true,
  reactStrictMode: false,
  productionBrowserSourceMaps: false,
};

export default nextConfig;
