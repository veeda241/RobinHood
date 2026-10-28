import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { fetchTrends } from '@/lib/api';
import { formatINR, type TrendBand } from '@/lib/mockData';

/** DB-backed collection vs statutory expectation, per income band. */
const TaxTrends: React.FC = () => {
  const { data: bands, isLoading } = useQuery<TrendBand[]>({
    queryKey: ['trends'],
    queryFn: fetchTrends,
  });

  const formatYAxis = (tickItem: number) =>
    tickItem >= 100000 ? `${(tickItem / 100000).toFixed(0)}L` : String(tickItem);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-md">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={`item-${index}`} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {formatINR(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-semibold">Collection vs Demand by Income Band (FY 2024-25)</CardTitle>
        <p className="text-sm text-muted-foreground">Computed live from the taxpayer registry - no simulated series.</p>
      </CardHeader>
      <CardContent className="pt-2">
        {isLoading ? (
          <div className="h-[350px] bg-slate-100 animate-pulse rounded" />
        ) : (
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={bands ?? []}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="band" tick={{ fontSize: 12 }} axisLine={false} />
                <YAxis tickFormatter={formatYAxis} tick={{ fontSize: 12 }} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ paddingTop: "10px" }} />
                <Bar dataKey="expected" name="Expected Tax" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="collected" name="Collected" fill="#16a34a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TaxTrends;
