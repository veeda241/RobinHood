import React from 'react';
import { Navigate } from 'react-router-dom';
import Header from '@/components/Header';
import DashboardStats from '@/components/DashboardStats';
import UserRegistry from '@/components/UserRegistry';
import RiskMatrix from '@/components/RiskMatrix';
import AuditLedger from '@/components/AuditLedger';
import TaxTrends from '@/components/TaxTrends';
import AiInsights from '@/components/AiInsights';
import Footer from '@/components/Footer';
import { useMe } from '@/lib/auth';
import { Loader2 } from 'lucide-react';

/** Admin Command Center - session-gated (Flask cookie or Supabase admin JWT). */
const Admin = () => {
  const { data: me, isLoading } = useMe();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-green-600" />
      </div>
    );
  }
  if (me?.role !== 'admin') return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-2">
            Admin Command Center
          </h1>
          <p className="text-lg text-slate-600">
            Encrypted taxpayer registry, ML risk matrix and the tamper-evident ledger.
          </p>
        </div>

        <DashboardStats />
        <RiskMatrix />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2 space-y-8">
            <UserRegistry />
            <AuditLedger />
          </div>
          <div className="space-y-8">
            <AiInsights />
            <TaxTrends />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Admin;
