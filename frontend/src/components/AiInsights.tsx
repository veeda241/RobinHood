
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BrainCircuit } from 'lucide-react';
import { aiInsights } from '@/lib/mockData';

const AiInsights: React.FC = () => {
  const getBadgeColor = (impact: 'high' | 'medium' | 'low') => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800 hover:bg-red-100';
      case 'medium':
        return 'bg-amber-100 text-amber-800 hover:bg-amber-100';
      case 'low':
        return 'bg-green-100 text-green-800 hover:bg-green-100';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center">
          <BrainCircuit className="h-6 w-6 text-fiscal-600 mr-2" />
          <CardTitle className="text-lg font-semibold">AI-Powered Insights</CardTitle>
        </div>
        <div className="animate-pulse-slow">
          <div className="h-2 w-2 rounded-full bg-green-500 inline-block mr-1"></div>
          <span className="text-xs text-muted-foreground">Processing live data</span>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        <div className="space-y-4">
          {aiInsights.map((insight) => (
            <div key={insight.id} className="border-b border-border pb-3 last:border-0 last:pb-0 pt-1">
              <div className="flex justify-between items-start mb-1">
                <h3 className="font-medium text-base">{insight.title}</h3>
                <Badge variant="outline" className={getBadgeColor(insight.impact)}>
                  {insight.impact.charAt(0).toUpperCase() + insight.impact.slice(1)} Impact
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mb-1">{insight.description}</p>
              <p className="text-xs text-gray-500">Generated on {insight.date}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AiInsights;
