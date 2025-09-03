import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/kis/:path*',
        destination: 'http://adapter.quantum-trading.com:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
