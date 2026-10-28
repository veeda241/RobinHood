import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Scroll } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchRegulations } from '@/lib/api';
import type { RegulationItem } from '@/lib/mockData';

/**
 * Statute-derived regulatory feed (/api/regulations): real FY 2024-25
 * provisions generated from the same constants the tax engine computes with.
 */
const RegulationFeed: React.FC = () => {
  const { data: updates, isLoading } = useQuery<RegulationItem[]>({
    queryKey: ['regulations'],
    queryFn: fetchRegulations,
    staleTime: 300_000,
  });

  const getCategoryColor = (category: string): string => {
    switch (category) {
      case 'income':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      case 'corporate':
        return 'bg-purple-100 text-purple-800 hover:bg-purple-100';
      case 'property':
        return 'bg-emerald-100 text-emerald-800 hover:bg-emerald-100';
      default:
        return 'bg-slate-100 text-slate-800 hover:bg-slate-100';
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center">
          <Scroll className="h-5 w-5 text-fiscal-600 mr-2" />
          <CardTitle className="text-lg font-semibold">Statutory Reference (FY 2024-25)</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-2 max-h-[400px] overflow-y-auto">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-slate-100 animate-pulse rounded" />)}
          </div>
        ) : (
          <div className="space-y-4">
            {(updates ?? []).map((update) => (
              <div key={update.id} className="border-b border-border pb-3 last:border-0 last:pb-0 pt-1">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-medium text-base">{update.title}</h3>
                  <Badge variant="outline" className={getCategoryColor(update.category)}>
                    {update.category.charAt(0).toUpperCase() + update.category.slice(1)}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-1">{update.description}</p>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-fiscal-800 font-medium">{update.source}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RegulationFeed;
