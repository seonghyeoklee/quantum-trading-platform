/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Strict Mode 비활성화로 중복 useEffect 방지
  // 프록시 설정 제거 - 직접 API 호출 사용
};

module.exports = nextConfig;