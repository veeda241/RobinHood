
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { monthlyTaxData } from '@/lib/mockData';

const TaxTrends: React.FC = () => {
  const formatYAxis = (tickItem: number) => {
    return `$${tickItem}B`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-md">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={`item-${index}`} style={{ color: entry.color }} className="text-sm">
              {entry.name}: ${entry.value}B
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
        <CardTitle className="text-lg font-semibold">Tax Revenue Trends (2025)</CardTitle>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={monthlyTaxData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} />
              <YAxis tickFormatter={formatYAxis} tick={{ fontSize: 12 }} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: "10px" }} />
              <Bar dataKey="income" name="Income Tax" stackId="a" fill="#0284c7" radius={[4, 4, 0, 0]} />
              <Bar dataKey="corporate" name="Corporate Tax" stackId="a" fill="#38bdf8" radius={[0, 0, 0, 0]} />
              <Bar dataKey="property" name="Property Tax" stackId="a" fill="#7dd3fc" radius={[0, 0, 0, 0]} />
              <Bar dataKey="other" name="Other Taxes" stackId="a" fill="#bae6fd" radius={[0, 0, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default TaxTrends;
