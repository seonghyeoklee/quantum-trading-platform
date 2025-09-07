import { Metadata } from 'next';
import DomesticNewsClient from '@/components/news/DomesticNewsClient';

export const metadata: Metadata = {
  title: '국내 뉴스 | Quantum Trading',
  description: '실시간 국내 금융 뉴스 - 주식, 증시, 경제 관련 최신 소식',
};

export default function DomesticNewsPage() {
  return (
    <DomesticNewsClient />
  );
}