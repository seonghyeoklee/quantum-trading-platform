/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Strict Mode 비활성화로 중복 useEffect 방지
  // 프록시 설정 제거 - 직접 API 호출 사용
  experimental: {
    // Path mapping을 위한 설정
    typedRoutes: false,
  },
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