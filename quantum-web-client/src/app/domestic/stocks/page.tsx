export const metadata = {
  title: '국내 종목 | Quantum Trading',
  description: '국내 주식 종목 정보',
};

export default function DomesticStockPage() {
  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground mb-2">
          국내 종목
        </h1>
        <p className="text-muted-foreground">
          국내 주식 종목 정보 및 실시간 시세
        </p>
      </div>
      
      <div className="bg-card p-8 rounded-lg border border-border">
        <div className="text-center text-muted-foreground">
          <div className="text-4xl mb-4">🏢</div>
          <p>국내 종목 정보 기능을 준비 중입니다.</p>
        </div>
      </div>
    </div>
  );
}