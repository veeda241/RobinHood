// Shared domain types for the Indian tax stack.
// The former US/IRS mock arrays are deliberately deleted - every screen now
// renders live data from the Flask gateway (/api/*) backed by Supabase.

export type Regime = 'NEW' | 'OLD' | 'EQUAL';

export type ComplianceStatus = 'COMPLIANT' | 'UNDERPAID' | 'FLAGGED_FOR_REVIEW';

/** Mirrors the decrypted shape of a `taxpayers` row (models.Taxpayer.to_dict). */
export interface TaxpayerProfile {
  user_id: string;
  name: string | null;
  pan_masked: string | null;
  declared_income: number;
  declared_deductions: number;
  expected_tax: number;
  tax_paid: number;
  due_amount: number;
  compliance_status: ComplianceStatus;
  recommended_regime: Regime;
  risk_score: number;
  flagged: boolean;
}

/** One insight row from /api/risk - real IsolationForest score + reasons. */
export interface RiskInsight {
  user_id: string;
  name: string | null;
  risk_score: number;
  gross_income: number;
  paid_ratio: number;
  reasons: string[];
}

/** One income band from /api/trends. */
export interface TrendBand {
  band: string;
  expected: number;
  collected: number;
  count: number;
}

/** Statute item from /api/regulations. */
export interface RegulationItem {
  id: string;
  title: string;
  description: string;
  source: string;
  category: 'income' | 'corporate' | 'property' | 'other';
}

/** Ledger row from /api/audit/trail. */
export interface AuditEvent {
  log_id: number;
  timestamp: string;
  action_type: string;
  actor_id: string;
  target_user_id: string | null;
  payload_json: string | null;
  prev_hash: string;
  payload_hash: string;
}

/** Result of /api/audit/verify. */
export interface ChainVerification {
  ok: boolean;
  length: number;
  broken_at: number | null;
  reason: string | null;
  head_hash: string | null;
}

/** Response of /api/tax/optimize. */
export interface RegimeMatrix {
  assessment_year: string;
  recommended_regime: Regime;
  savings: number;
  marginal_swap_income: number | null;
  new_regime: { total_tax: number; taxable_income: number };
  old_regime: { total_tax: number; taxable_income: number; allowed_deductions: Record<string, number> };
}

/** Response of /api/tax/curve. */
export interface TaxCurve {
  assessment_year: string;
  marginal_swap_income: number | null;
  points: { income: number; new_tax: number; old_tax: number; recommended: Regime }[];
}

export const formatINR = (value: number): string =>
  '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value);
