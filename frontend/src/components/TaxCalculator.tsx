
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calculator, ArrowRight, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { calculateTax as apiCalculateTax } from '@/lib/api';

const TaxCalculator: React.FC = () => {
  const [income, setIncome] = useState<string>('600000');
  const [taxAmount, setTaxAmount] = useState<number | null>(null);
  const [breakdown, setBreakdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    const incomeValue = parseFloat(income);

    if (isNaN(incomeValue) || incomeValue < 0) {
      return;
    }

    setLoading(true);
    try {
      const data = await apiCalculateTax(incomeValue);
      setTaxAmount(data.tax);
      setBreakdown(data.breakdown);
    } catch (error) {
      console.error("Calculation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center">
          <Calculator className="h-5 w-5 text-fiscal-600 mr-2" />
          <CardTitle className="text-lg font-semibold">Quick Tax Estimator</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="income">Annual Income (INR)</Label>
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-2.5 text-muted-foreground">₹</span>
                <Input
                  id="income"
                  type="number"
                  value={income}
                  onChange={(e) => setIncome(e.target.value)}
                  className="pl-7"
                />
              </div>
              <Button
                onClick={handleCalculate}
                disabled={loading}
                className="bg-fiscal-600 hover:bg-fiscal-700"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4 mr-1" />}
                Calculate
              </Button>
            </div>
          </div>

          {taxAmount !== null && (
            <div className="bg-fiscal-50 p-4 rounded-md space-y-3">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground">Estimated Tax:</h4>
                <p className="text-xl font-bold text-fiscal-900">₹{taxAmount.toLocaleString()}</p>
              </div>

              {breakdown && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Tax Breakdown:</h4>
                  <div className="text-xs bg-white p-2 rounded border border-fiscal-100 whitespace-pre-line font-mono text-fiscal-800">
                    {breakdown}
                  </div>
                </div>
              )}

              <p className="text-[10px] text-muted-foreground italic">
                Calculated based on the latest Indian Income Tax Slabs (2024-25).
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TaxCalculator;
