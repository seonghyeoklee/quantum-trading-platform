import KiwoomDirectExample from '@/components/examples/KiwoomDirectExample';

export default function KiwoomDirectPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">
          키움 어댑터 직접 호출 테스트
        </h1>
        
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h2 className="font-semibold text-blue-800 mb-2">직접 호출 방식 장점:</h2>
          <ul className="text-blue-700 text-sm space-y-1 list-disc list-inside">
            <li>프록시 없이 키움 어댑터에 바로 연결 (http://localhost:10201)</li>
            <li>간단한 구조로 디버깅이 쉬움</li>
            <li>응답 속도가 빠름 (중간 레이어 제거)</li>
            <li>CORS는 키움 어댑터에서 해결됨</li>
          </ul>
        </div>

        <KiwoomDirectExample />

        <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h2 className="font-semibold text-gray-800 mb-2">사용 예제 코드:</h2>
          <pre className="text-xs bg-white p-3 border rounded overflow-x-auto">
{`import { getStockList, getProgramTradeTop50, getKiwoomToken } from '@/lib/api/kiwoom-direct';

// 코스피 종목 리스트 조회
const stockList = await getStockList({ mrkt_tp: '0' });

// 프로그램 거래 상위 50 조회  
const programTrade = await getProgramTradeTop50({
  trde_upper_tp: '2', // 순매수상위
  amt_qty_tp: '1',    // 금액
  mrkt_tp: 'P00101',  // 코스피
  stex_tp: '1'        // KRX
});

// 키움 토큰 발급
const token = await getKiwoomToken();`}
          </pre>
        </div>
      </div>
    </div>
  );
}