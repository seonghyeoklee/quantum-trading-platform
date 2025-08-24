/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Strict Mode 비활성화로 중복 useEffect 방지
  async rewrites() {
    return [
      {
        source: '/api/kiwoom/:path*',
        destination: 'http://localhost:8100/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;