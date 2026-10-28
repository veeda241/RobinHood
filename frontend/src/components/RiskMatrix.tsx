import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { fetchRiskFeed } from '@/lib/api';
import { formatINR, type RiskInsight } from '@/lib/mockData';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, ReferenceLine,
} from 'recharts';
import { Grid3X3 } from 'lucide-react';

/**
 * Anomaly screening matrix: income (x) vs paid-to-expected ratio (y).
 * Point size encodes the ML risk index; colour buckets mirror the
 * 0-100 risk bands used by the IsolationForest engine.
 */
const RiskMatrix: React.FC = () => {
  const { data: feed, isLoading } = useQuery<RiskInsight[]>({
    queryKey: ['risk'],
    queryFn: fetchRiskFeed,
  });

  const withColor = (feed ?? []).map((r) => ({
    ...r,
    incomeLakh: r.gross_income / 100000,
    paidPct: Math.min(r.paid_ratio, 1.5) * 100,
    riskBucket: r.risk_score >= 70 ? 'High' : r.risk_score >= 40 ? 'Medium' : 'Low',
  }));

  const buckets = [
    { key: 'High', color: '#dc2626' },
    { key: 'Medium', color: '#f59e0b' },
    { key: 'Low', color: '#16a34a' },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload?.length) {
      const d = payload[0].payload as RiskInsight & { incomeLakh: number };
      return (
        <div className="bg-white p-3 border rounded shadow-md max-w-xs">
          <p className="font-medium text-sm">{d.name ?? d.user_id}</p>
          <p className="text-xs text-muted-foreground">
            {formatINR(d.gross_income)} · risk {d.risk_score}
          </p>
          {d.reasons?.slice(0, 3).map((reason, i) => (
            <p key={i} className="text-xs mt-1">• {reason}</p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2">
        <div className="flex items-center">
          <Grid3X3 className="h-5 w-5 text-fiscal-600 mr-2" />
          <CardTitle className="text-lg font-semibold">ML Risk Matrix</CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          Anomaly screening (IsolationForest) - income vs tax-paid ratio, sized by risk index.
        </p>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[320px] bg-slate-100 animate-pulse rounded" />
        ) : (
          <div className="h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="incomeLakh" name="Income" unit="L" tick={{ fontSize: 11 }}
                  axisLine={false} label={{ value: 'Gross income (₹ lakh)', position: 'insideBottom', offset: -2, fontSize: 11 }} />
                <YAxis dataKey="paidPct" name="Paid %" unit="%" tick={{ fontSize: 11 }} axisLine={false}
                  domain={[0, 150]} label={{ value: 'Paid / expected', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                <ZAxis dataKey="risk_score" range={[60, 400]} name="Risk" />
                <ReferenceLine y={100} stroke="#94a3b8" strokeDasharray="4 4"
                  label={{ value: 'fully paid', position: 'right', fontSize: 10, fill: '#64748b' }} />
                <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                <Legend />
                {buckets.map((b) => (
                  <Scatter key={b.key} name={`${b.key} risk`}
                    data={withColor.filter((r) => r.riskBucket === b.key)}
                    fill={b.color} />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RiskMatrix;
