import React from 'react';
import Header from '@/components/Header';
import TaxOptimizer from '@/components/TaxOptimizer';
import TaxCalculator from '@/components/TaxCalculator';
import RegulationFeed from '@/components/RegulationFeed';
import Footer from '@/components/Footer';
import { ShieldCheck, Lock, BrainCircuit } from 'lucide-react';

/** Citizen-facing portal: dual-regime optimization + quick estimator. */
const Index = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-2">
            Robinhood AI — Citizen Tax Intelligence
          </h1>
          <p className="text-lg text-slate-600">
            Privacy-preserving dual-regime optimization with ML compliance risk scoring.
          </p>
          <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-500">
            <span className="flex items-center gap-1.5">
              <Lock className="h-4 w-4 text-green-600" /> PII encrypted per-field (Fernet + blind index)
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-green-600" /> Tamper-evident audit ledger
            </span>
            <span className="flex items-center gap-1.5">
              <BrainCircuit className="h-4 w-4 text-green-600" /> IsolationForest anomaly screening
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2">
            <TaxOptimizer />
          </div>
          <div className="space-y-8">
            <TaxCalculator />
            <RegulationFeed />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Index;
