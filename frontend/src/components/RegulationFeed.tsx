
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Scroll } from 'lucide-react';
import { regulationUpdates } from '@/lib/mockData';

const RegulationFeed: React.FC = () => {
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
          <CardTitle className="text-lg font-semibold">Latest Regulation Updates</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-2 max-h-[400px] overflow-y-auto">
        <div className="space-y-4">
          {regulationUpdates.map((update) => (
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
                <span className="text-xs text-gray-500">Posted on {update.date}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default RegulationFeed;
