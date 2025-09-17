import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false, // React Strict Mode 비활성화 (차트 중복 생성 방지)
  async rewrites() {
    // 동적 호스트 기반 API 프록시 설정
    // Next.js 서버에서 실행되므로 어떤 클라이언트에서 접속해도 동일하게 작동
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://192.168.200.198:8080/api/v1/:path*',
      },
      {
        source: '/api/kis/:path*',
        destination: 'http://192.168.200.198:8000/:path*',
      },
      {
        source: '/api/external/:path*',
        destination: 'http://192.168.200.198:8001/:path*',
      },
    ];
  },
};

export default nextConfig;
