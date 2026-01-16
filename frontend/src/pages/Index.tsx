
import React from 'react';
import Header from '@/components/Header';
import DashboardStats from '@/components/DashboardStats';
import AiInsights from '@/components/AiInsights';
import TaxTrends from '@/components/TaxTrends';
import UserRegistry from '@/components/UserRegistry';
import TaxCalculator from '@/components/TaxCalculator';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-2">Robinhood AI Tax Monitor</h1>
          <p className="text-lg text-slate-600">
            Advanced AI-powered compliance analysis and taxpayer management system.
          </p>
        </div>

        <DashboardStats />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2 space-y-8">
            <UserRegistry />
            <TaxTrends />
          </div>

          <div className="space-y-8">
            <TaxCalculator />
            <AiInsights />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Index;
