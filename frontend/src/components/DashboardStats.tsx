
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Percent, CheckCircle, Search, FileText, AlertCircle, DollarSign, Users } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchStats } from '@/lib/api';

const DashboardStats: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 5000,
  });

  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6 h-24 bg-slate-100 rounded-md" />
          </Card>
        ))}
      </div>
    );
  }

  const statItems = [
    {
      id: 'total',
      title: 'Total Taxpayers',
      value: stats.total.toString(),
      icon: <Users className="h-5 w-5" />,
      color: 'border-l-blue-500'
    },
    {
      id: 'compliant',
      title: 'Compliant',
      value: stats.compliant.toString(),
      icon: <CheckCircle className="h-5 w-5" />,
      color: 'border-l-green-500'
    },
    {
      id: 'underpaid',
      title: 'Underpaid',
      value: stats.underpaid.toString(),
      icon: <AlertCircle className="h-5 w-5" />,
      color: 'border-l-orange-500'
    },
    {
      id: 'flagged',
      title: 'Flagged (Audit)',
      value: stats.flagged.toString(),
      icon: <Search className="h-5 w-5" />,
      color: 'border-l-red-500'
    },
  ];

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statItems.map((stat) => (
          <Card key={stat.id} className={`border-l-4 ${stat.color}`}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                  <h2 className="text-2xl font-bold mt-1">{stat.value}</h2>
                </div>
                <div className="bg-fiscal-100 p-2 rounded-full">
                  {stat.icon}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <Card className="border-l-4 border-l-emerald-600 bg-emerald-50/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-emerald-700">Total Tax Collected</p>
              <h2 className="text-3xl font-bold text-emerald-900">₹{stats.total_paid.toLocaleString()}</h2>
            </div>
            <DollarSign className="h-10 w-10 text-emerald-600 opacity-20" />
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-600 bg-amber-50/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-amber-700">Total Tax Due</p>
              <h2 className="text-3xl font-bold text-amber-900">₹{stats.total_due.toLocaleString()}</h2>
            </div>
            <AlertCircle className="h-10 w-10 text-amber-600 opacity-20" />
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default DashboardStats;
