'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

// DINO 분석 데이터 타입 정의
interface DinoFinanceItem {
  항목: string;
  기준연도?: string;
  값: string | number;
  판단: string;
  점수: number;
}

interface DinoTechnicalItem {
  항목: string;
  기간?: string;
  값: string | number;
  판단: string;
  점수: number;
}

interface DinoPriceData {
  최고가: number;
  최저가: number;
  현재가: number;
  판단: string;
  점수: number;
}

interface DinoMaterialItem {
  평가항목: string;
  기준?: string;
  해당여부: 'Y' | 'N';
  값?: string | number;
  점수: number;
}

interface DinoAnalysisData {
  평가점수: {
    총점: number;
    재무: number;
    기술: number;
    가격: number;
    재료: number;
  };
  재무: DinoFinanceItem[];
  기술: DinoTechnicalItem[];
  가격: DinoPriceData;
  재료: DinoMaterialItem[];
}

interface DinoAnalysisVisualizationProps {
  data: DinoAnalysisData;
}

// 점수에 따른 색상 및 아이콘 반환
const getScoreColor = (score: number, maxScore: number = 5) => {
  const percentage = (score / maxScore) * 100;
  if (percentage >= 70) return { color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle };
  if (percentage >= 40) return { color: 'text-orange-600', bgColor: 'bg-orange-100', icon: AlertCircle };
  return { color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircle };
};

// 재무 분석 테이블 컴포넌트
const FinanceAnalysisTable = ({ items }: { items: DinoFinanceItem[] }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <DollarSign className="w-5 h-5" />
        재무 분석
      </CardTitle>
    </CardHeader>
    <CardContent>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>항목</TableHead>
            <TableHead>기준연도</TableHead>
            <TableHead>값</TableHead>
            <TableHead>판단</TableHead>
            <TableHead className="text-center">점수</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item, index) => {
            const scoreInfo = getScoreColor(item.점수, 1);
            const Icon = scoreInfo.icon;
            return (
              <TableRow key={index}>
                <TableCell className="font-medium">{item.항목}</TableCell>
                <TableCell>{item.기준연도 || '-'}</TableCell>
                <TableCell className="font-mono">
                  {typeof item.값 === 'number' ? item.값.toLocaleString() : item.값}
                </TableCell>
                <TableCell>{item.판단}</TableCell>
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <Icon className={`w-4 h-4 ${scoreInfo.color}`} />
                    <Badge variant="outline" className={scoreInfo.bgColor}>
                      {item.점수}
                    </Badge>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </CardContent>
  </Card>
);

// 기술 분석 컴포넌트
const TechnicalAnalysisCard = ({ items }: { items: DinoTechnicalItem[] }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <BarChart3 className="w-5 h-5" />
        기술 분석
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      {items.map((item, index) => {
        const scoreInfo = getScoreColor(item.점수, 1);
        const Icon = scoreInfo.icon;
        return (
          <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium">{item.항목}</span>
                {item.기간 && <Badge variant="secondary">{item.기간}</Badge>}
              </div>
              <div className="text-sm text-gray-600">
                값: <span className="font-mono">{item.값}</span> | {item.판단}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Icon className={`w-5 h-5 ${scoreInfo.color}`} />
              <Badge className={scoreInfo.bgColor}>{item.점수}점</Badge>
            </div>
          </div>
        );
      })}
    </CardContent>
  </Card>
);

// 가격 분석 컴포넌트
const PriceAnalysisCard = ({ data }: { data: DinoPriceData }) => {
  const scoreInfo = getScoreColor(data.점수, 2);
  const Icon = scoreInfo.icon;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          가격 분석
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center p-3 border rounded-lg">
            <div className="text-sm text-gray-600">최고가</div>
            <div className="text-lg font-bold text-red-600">
              {data.최고가.toLocaleString()}원
            </div>
          </div>
          <div className="text-center p-3 border rounded-lg bg-blue-50">
            <div className="text-sm text-gray-600">현재가</div>
            <div className="text-lg font-bold text-blue-600">
              {data.현재가.toLocaleString()}원
            </div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-sm text-gray-600">최저가</div>
            <div className="text-lg font-bold text-green-600">
              {data.최저가.toLocaleString()}원
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div>
            <div className="font-medium">가격 분석 결과</div>
            <div className="text-sm text-gray-600">{data.판단}</div>
          </div>
          <div className="flex items-center gap-2">
            <Icon className={`w-5 h-5 ${scoreInfo.color}`} />
            <Badge className={scoreInfo.bgColor}>{data.점수}점</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// 재료 분석 체크리스트 컴포넌트
const MaterialAnalysisCard = ({ items }: { items: DinoMaterialItem[] }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <CheckCircle className="w-5 h-5" />
        재료 분석
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        {items.map((item, index) => {
          const isPositive = item.해당여부 === 'Y';
          const scoreInfo = getScoreColor(item.점수, 1);
          const Icon = scoreInfo.icon;
          
          return (
            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">{item.평가항목}</span>
                  {item.기준 && <Badge variant="outline">{item.기준}</Badge>}
                </div>
                {item.값 && (
                  <div className="text-sm text-gray-600">
                    값: <span className="font-mono">{item.값}</span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                {isPositive ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-gray-400" />
                )}
                <Badge 
                  variant={isPositive ? "default" : "secondary"}
                  className={isPositive ? "bg-green-100 text-green-800" : ""}
                >
                  {item.해당여부}
                </Badge>
                <Icon className={`w-4 h-4 ${scoreInfo.color}`} />
                <Badge className={scoreInfo.bgColor}>{item.점수}점</Badge>
              </div>
            </div>
          );
        })}
      </div>
    </CardContent>
  </Card>
);

// 종합 점수 요약 컴포넌트
const ScoreSummaryCard = ({ scores }: { scores: DinoAnalysisData['평가점수'] }) => {
  const totalScoreInfo = getScoreColor(scores.총점, 20); // 총점 20점 기준
  const financeScoreInfo = getScoreColor(scores.재무, 5);
  const technicalScoreInfo = getScoreColor(scores.기술, 5);
  const priceScoreInfo = getScoreColor(scores.가격, 5);
  const materialScoreInfo = getScoreColor(scores.재료, 5);

  return (
    <Card className="mb-6 border-2">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-6 h-6" />
          종합 DINO 평가 점수
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* 총점 강조 표시 */}
        <div className="text-center mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className={`text-4xl font-bold ${totalScoreInfo.color}`}>
              {scores.총점}
            </div>
            <div className="text-lg text-gray-600">/ 20점</div>
          </div>
          <div className="text-sm text-gray-600 mb-2">종합 점수</div>
          <Progress 
            value={(scores.총점 / 20) * 100} 
            className="h-3"
          />
          <div className="text-xs text-gray-500 mt-1">
            {((scores.총점 / 20) * 100).toFixed(1)}%
          </div>
        </div>

        {/* 영역별 점수 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-3 border rounded-lg">
            <div className={`text-2xl font-bold ${financeScoreInfo.color} mb-1`}>
              {scores.재무}
            </div>
            <div className="text-sm text-gray-600 mb-2">재무 분석</div>
            <Progress 
              value={(scores.재무 / 5) * 100} 
              className="h-2"
            />
            <div className="text-xs text-gray-500 mt-1">
              {scores.재무}/5 ({((scores.재무 / 5) * 100).toFixed(0)}%)
            </div>
          </div>
          
          <div className="text-center p-3 border rounded-lg">
            <div className={`text-2xl font-bold ${technicalScoreInfo.color} mb-1`}>
              {scores.기술}
            </div>
            <div className="text-sm text-gray-600 mb-2">기술 분석</div>
            <Progress 
              value={(scores.기술 / 5) * 100} 
              className="h-2"
            />
            <div className="text-xs text-gray-500 mt-1">
              {scores.기술}/5 ({((scores.기술 / 5) * 100).toFixed(0)}%)
            </div>
          </div>
          
          <div className="text-center p-3 border rounded-lg">
            <div className={`text-2xl font-bold ${priceScoreInfo.color} mb-1`}>
              {scores.가격}
            </div>
            <div className="text-sm text-gray-600 mb-2">가격 분석</div>
            <Progress 
              value={(scores.가격 / 5) * 100} 
              className="h-2"
            />
            <div className="text-xs text-gray-500 mt-1">
              {scores.가격}/5 ({((scores.가격 / 5) * 100).toFixed(0)}%)
            </div>
          </div>
          
          <div className="text-center p-3 border rounded-lg">
            <div className={`text-2xl font-bold ${materialScoreInfo.color} mb-1`}>
              {scores.재료}
            </div>
            <div className="text-sm text-gray-600 mb-2">재료 분석</div>
            <Progress 
              value={(scores.재료 / 5) * 100} 
              className="h-2"
            />
            <div className="text-xs text-gray-500 mt-1">
              {scores.재료}/5 ({((scores.재료 / 5) * 100).toFixed(0)}%)
            </div>
          </div>
        </div>

        {/* 등급 표시 */}
        <div className="mt-4 text-center">
          <Badge 
            variant="outline" 
            className={`text-lg px-4 py-2 ${totalScoreInfo.bgColor} ${totalScoreInfo.color} font-medium`}
          >
            {scores.총점 >= 16 ? 'A급 (투자 추천)' :
             scores.총점 >= 12 ? 'B급 (투자 고려)' :
             scores.총점 >= 8 ? 'C급 (신중 검토)' : 'D급 (투자 주의)'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

// 개별 영역 시각화 컴포넌트 (종합 점수 없이)
export function DinoSectionVisualization({ data }: DinoAnalysisVisualizationProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FinanceAnalysisTable items={data.재무} />
        <TechnicalAnalysisCard items={data.기술} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PriceAnalysisCard data={data.가격} />
        <MaterialAnalysisCard items={data.재료} />
      </div>
    </div>
  );
}

// 메인 컴포넌트 (종합 점수 포함)
export default function DinoAnalysisVisualization({ data }: DinoAnalysisVisualizationProps) {
  return (
    <div className="space-y-6">
      <ScoreSummaryCard scores={data.평가점수} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FinanceAnalysisTable items={data.재무} />
        <TechnicalAnalysisCard items={data.기술} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PriceAnalysisCard data={data.가격} />
        <MaterialAnalysisCard items={data.재료} />
      </div>
    </div>
  );
}