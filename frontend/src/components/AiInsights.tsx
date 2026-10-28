import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BrainCircuit } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchRiskFeed } from '@/lib/api';
import { formatINR, type RiskInsight } from '@/lib/mockData';

/**
 * Real AI insights: every card is a live IsolationForest risk assessment
 * with concrete reason strings from /api/risk - no mock content.
 */
const AiInsights: React.FC = () => {
  const { data: feed, isLoading } = useQuery<RiskInsight[]>({
    queryKey: ['risk'],
    queryFn: fetchRiskFeed,
  });

  const impactOf = (score: number): 'high' | 'medium' | 'low' =>
    score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low';

  const badgeColor = (impact: string) =>
    impact === 'high'
      ? 'bg-red-100 text-red-800 hover:bg-red-100'
      : impact === 'medium'
        ? 'bg-amber-100 text-amber-800 hover:bg-amber-100'
        : 'bg-green-100 text-green-800 hover:bg-green-100';

  const top = (feed ?? []).slice(0, 4);

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center">
          <BrainCircuit className="h-6 w-6 text-fiscal-600 mr-2" />
          <CardTitle className="text-lg font-semibold">ML Risk Insights</CardTitle>
        </div>
        <div className="animate-pulse-slow">
          <div className="h-2 w-2 rounded-full bg-green-500 inline-block mr-1"></div>
          <span className="text-xs text-muted-foreground">Live anomaly screening</span>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-16 bg-slate-100 animate-pulse rounded" />)}
          </div>
        ) : top.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            No taxpayer records scored yet. Risk insights appear once assessments are filed.
          </p>
        ) : (
          <div className="space-y-4">
            {top.map((insight) => {
              const impact = impactOf(insight.risk_score);
              return (
                <div key={insight.user_id} className="border-b border-border pb-3 last:border-0 last:pb-0 pt-1">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-medium text-base">
                      {insight.name ?? insight.user_id}
                      <span className="text-sm text-muted-foreground font-normal ml-2">
                        {formatINR(insight.gross_income)} · paid {Math.round(insight.paid_ratio * 100)}%
                      </span>
                    </h3>
                    <Badge variant="outline" className={badgeColor(impact)}>
                      Risk {insight.risk_score}
                    </Badge>
                  </div>
                  <ul className="text-sm text-muted-foreground mb-1 space-y-0.5 list-disc pl-4">
                    {insight.reasons.length > 0
                      ? insight.reasons.map((r, i) => <li key={i}>{r}</li>)
                      : <li>No anomalies detected for this profile.</li>}
                  </ul>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AiInsights;
