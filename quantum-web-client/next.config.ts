import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false, // React Strict Mode 비활성화 (차트 중복 생성 방지)
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://api.quantum-trading.com:8080/api/v1/:path*',
      },
      {
        source: '/api/kis/:path*',
        destination: 'http://adapter.quantum-trading.com:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
