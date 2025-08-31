/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Strict Mode 비활성화로 중복 useEffect 방지
  
  // API 프록시 설정 - 백엔드로 리디렉션
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://100.68.90.21:10101/api/v1/:path*',
      },
    ];
  },
  
  // TypedRoutes 설정 (최신 Next.js 버전)
  typedRoutes: false,
  webpack: (config) => {
    // Path mapping alias 추가 설정
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').resolve(__dirname, './src'),
    };
    return config;
  },
};

module.exports = nextConfig;