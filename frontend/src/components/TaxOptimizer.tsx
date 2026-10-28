import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { optimizeTax, fetchTaxCurve, assessTax, ApiError } from '@/lib/api';
import { formatINR, type RegimeMatrix, type TaxCurve } from '@/lib/mockData';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine, Legend,
} from 'recharts';
import { Scale, Sparkles, Loader2, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

const fmtLakh = (v: number) => (v >= 100000 ? `${(v / 100000).toFixed(v % 100000 ? 1 : 0)}L` : String(v));

function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

const TaxOptimizer: React.FC = () => {
  const [income, setIncome] = useState(1500000);
  const [c80C, setC80C] = useState(150000);
  const [c80D, setC80D] = useState(50000);
  const [senior, setSenior] = useState(false);

  const debIncome = useDebounced(income);
  const deb80C = useDebounced(c80C);
  const deb80D = useDebounced(c80D);
  const debSenior = useDebounced(senior);
  const deductions = useMemo(() => ({ '80C': deb80C, '80D': deb80D }), [deb80C, deb80D]);

  const { data: matrix } = useQuery<RegimeMatrix>({
    queryKey: ['optimize', debIncome, deb80C, deb80D, debSenior],
    queryFn: () => optimizeTax(debIncome, deductions, debSenior),
  });

  const { data: curve } = useQuery<TaxCurve>({
    queryKey: ['curve', deb80C, deb80D, debSenior],
    queryFn: () => fetchTaxCurve({
      income_max: Math.max(5000000, debIncome * 1.5),
      '80C': deb80C, '80D': deb80D, senior: debSenior,
    }),
  });

  const assessMutation = useMutation({
    mutationFn: () => assessTax({
      gross_income: debIncome, tax_paid: 0, deductions,
      name: 'Portal Visitor',
    }),
    onSuccess: (res) => {
      toast.success(`Assessment filed - ${res.assessment.compliance_status} · recommended ${res.assessment.recommended_regime} regime`);
    },
    onError: (err: Error) => {
      toast.error(err instanceof ApiError && err.status === 401
        ? 'Sign in with Supabase Auth to file a persisted assessment.'
        : err.message);
    },
  });

  const swap = matrix?.marginal_swap_income ?? curve?.marginal_swap_income ?? null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Scale className="h-5 w-5 text-fiscal-600 mr-2" />
            <CardTitle className="text-lg font-semibold">Dual-Regime Tax Optimizer</CardTitle>
          </div>
          <Badge variant="secondary" className="text-xs">{matrix?.assessment_year ?? 'FY 2024-25'}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Live comparison of the New vs Old regime with statutory cess, surcharge
          tiers and Section 87A rebates. PII is only persisted when you file an assessment.
        </p>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="space-y-5">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <Label>Gross Income</Label>
              <span className="font-semibold">{formatINR(income)}</span>
            </div>
            <Slider min={0} max={5000000} step={50000} value={[income]} onValueChange={([v]) => setIncome(v)} />
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <Label>80C investments <span className="text-muted-foreground">(cap ₹1.5L, old regime)</span></Label>
              <span className="font-semibold">{formatINR(c80C)}</span>
            </div>
            <Slider min={0} max={200000} step={5000} value={[c80C]} onValueChange={([v]) => setC80C(v)} />
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <Label>80D health premium <span className="text-muted-foreground">(cap ₹25k / ₹50k senior)</span></Label>
              <span className="font-semibold">{formatINR(c80D)}</span>
            </div>
            <Slider min={0} max={60000} step={2500} value={[c80D]} onValueChange={([v]) => setC80D(v)} />
          </div>
          <div className="flex items-center gap-2">
            <Switch id="senior" checked={senior} onCheckedChange={setSenior} />
            <Label htmlFor="senior" className="text-sm">Senior citizen (60y+)</Label>
          </div>
        </div>

        {matrix && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">New Regime</p>
              <p className="text-lg font-bold">{formatINR(matrix.new_regime.total_tax)}</p>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">Old Regime</p>
              <p className="text-lg font-bold">{formatINR(matrix.old_regime.total_tax)}</p>
            </div>
            <div className="rounded-md border p-3 bg-green-50 border-green-200">
              <p className="text-xs text-green-700 flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Recommendation
              </p>
              <p className="text-lg font-bold text-green-800">
                {matrix.recommended_regime}
                {matrix.savings > 0 && (
                  <span className="text-xs font-medium text-green-700 ml-2">saves {formatINR(matrix.savings)}</span>
                )}
              </p>
            </div>
          </div>
        )}

        {curve && (
          <div>
            <p className="text-sm font-medium mb-2">
              Regime crossover curve
              {swap
                ? <> — advantage flips at <span className="font-semibold">{formatINR(swap)}</span></>
                : <> — one regime dominates across the whole range for this deduction profile</>}
            </p>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={curve.points} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis dataKey="income" tickFormatter={fmtLakh} tick={{ fontSize: 11 }} axisLine={false} />
                  <YAxis tickFormatter={fmtLakh} tick={{ fontSize: 11 }} axisLine={false} width={50} />
                  <Tooltip
                    formatter={(v: number, n: string) => [formatINR(v), n === 'new_tax' ? 'New Regime' : 'Old Regime']}
                    labelFormatter={(l: number) => `Income: ${formatINR(l)}`}
                  />
                  <Legend formatter={(v) => (v === 'new_tax' ? 'New Regime tax' : 'Old Regime tax')} />
                  <Area type="monotone" dataKey="new_tax" stroke="#0284c7" fill="#0284c722" strokeWidth={2} />
                  <Area type="monotone" dataKey="old_tax" stroke="#f59e0b" fill="#f59e0b22" strokeWidth={2} />
                  {swap && (
                    <ReferenceLine x={swap} stroke="#16a34a" strokeDasharray="6 3"
                      label={{ value: 'swap', position: 'top', fill: '#16a34a', fontSize: 11 }} />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <Button
          className="w-full bg-fiscal-600 hover:bg-fiscal-700 gap-2"
          onClick={() => assessMutation.mutate()}
          disabled={assessMutation.isPending}
        >
          {assessMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
          File Secure Assessment (encrypts PII + audit-logs)
        </Button>

        {assessMutation.data && (
          <div className="rounded-md border bg-slate-50 p-4 space-y-2 text-sm">
            <p className="font-semibold">Assessment #{assessMutation.data.taxpayer_id}</p>
            <p>Compliance: <Badge>{assessMutation.data.assessment.compliance_status}</Badge></p>
            <p>Risk index: <span className="font-mono">{assessMutation.data.assessment.risk_index.toFixed(1)}</span> / 100</p>
            {assessMutation.data.assessment.risk_reasons?.length > 0 && (
              <ul className="list-disc pl-5 text-muted-foreground">
                {assessMutation.data.assessment.risk_reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TaxOptimizer;
