
export type TaxStat = {
  id: string;
  title: string;
  value: string;
  change: {
    value: string;
    trend: 'up' | 'down' | 'neutral';
  };
  icon: string;
};

export type AiInsight = {
  id: string;
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  date: string;
};

export type RegulationUpdate = {
  id: string;
  title: string;
  description: string;
  date: string;
  source: string;
  category: 'income' | 'corporate' | 'property' | 'other';
};

export type TaxBracket = {
  id: number;
  min: number;
  max: number | null;
  rate: number;
  name: string;
};

// Dashboard stats
export const taxStats: TaxStat[] = [
  {
    id: '1',
    title: 'Average Tax Rate',
    value: '22.4%',
    change: { value: '1.2%', trend: 'up' },
    icon: 'percent'
  },
  {
    id: '2',
    title: 'Tax Compliance',
    value: '91.7%',
    change: { value: '2.5%', trend: 'up' },
    icon: 'check-circle'
  },
  {
    id: '3',
    title: 'Audit Rate',
    value: '0.6%',
    change: { value: '0.2%', trend: 'down' },
    icon: 'search'
  },
  {
    id: '4',
    title: 'Digital Filing',
    value: '87.3%',
    change: { value: '5.8%', trend: 'up' },
    icon: 'file-text'
  },
];

// AI insights
export const aiInsights: AiInsight[] = [
  {
    id: '1',
    title: 'New Deduction Rules Analysis',
    description: 'AI analysis shows the new deduction rules will benefit middle-income households by an average of $420 annually.',
    impact: 'medium',
    date: '2025-04-26'
  },
  {
    id: '2',
    title: 'Remote Work Tax Implications',
    description: 'Cross-state remote work arrangements may create tax obligations in multiple jurisdictions for approximately 28% of the workforce.',
    impact: 'high',
    date: '2025-04-25'
  },
  {
    id: '3',
    title: 'Crypto Tax Reporting Gap',
    description: 'Detected a significant reporting gap in cryptocurrency gains, estimating $8.2B in unreported income.',
    impact: 'high',
    date: '2025-04-23'
  },
  {
    id: '4',
    title: 'Charitable Deduction Pattern',
    description: 'Pattern analysis reveals charitable deductions increase by 24% in December compared to monthly averages.',
    impact: 'low',
    date: '2025-04-20'
  },
];

// Regulation updates
export const regulationUpdates: RegulationUpdate[] = [
  {
    id: '1',
    title: 'Form 1040 Filing Deadline Extension',
    description: 'The IRS has extended the filing deadline for Form 1040 by 30 days for residents of disaster-affected areas.',
    date: '2025-04-28',
    source: 'Internal Revenue Service',
    category: 'income'
  },
  {
    id: '2',
    title: 'New Home Office Deduction Rules',
    description: 'Updated guidelines for claiming home office deductions now include simplified options for gig economy workers.',
    date: '2025-04-25',
    source: 'Department of Treasury',
    category: 'income'
  },
  {
    id: '3',
    title: 'Corporate Tax Credit for Green Energy',
    description: 'New tax credits available for corporations investing in renewable energy infrastructure and sustainability practices.',
    date: '2025-04-21',
    source: 'Environmental Protection Agency',
    category: 'corporate'
  },
  {
    id: '4',
    title: 'Property Tax Assessment Updates',
    description: 'New methods for property tax assessments will be implemented nationwide starting next fiscal year.',
    date: '2025-04-18',
    source: 'Department of Housing',
    category: 'property'
  },
];

// Tax brackets for 2025 (simulated)
export const taxBrackets: TaxBracket[] = [
  {
    id: 1,
    min: 0,
    max: 11000,
    rate: 10,
    name: 'Lowest Bracket'
  },
  {
    id: 2,
    min: 11001,
    max: 44725,
    rate: 12,
    name: 'Low Bracket'
  },
  {
    id: 3,
    min: 44726,
    max: 95375,
    rate: 22,
    name: 'Lower Middle Bracket'
  },
  {
    id: 4,
    min: 95376,
    max: 182100,
    rate: 24,
    name: 'Middle Bracket'
  },
  {
    id: 5,
    min: 182101,
    max: 231250,
    rate: 32,
    name: 'Upper Middle Bracket'
  },
  {
    id: 6,
    min: 231251,
    max: 578125,
    rate: 35,
    name: 'High Bracket'
  },
  {
    id: 7,
    min: 578126,
    max: null,
    rate: 37,
    name: 'Highest Bracket'
  }
];

// Monthly tax collection data (simulated)
export const monthlyTaxData = [
  { month: 'Jan', income: 325, corporate: 145, property: 85, other: 30 },
  { month: 'Feb', income: 310, corporate: 130, property: 90, other: 35 },
  { month: 'Mar', income: 345, corporate: 150, property: 88, other: 32 },
  { month: 'Apr', income: 420, corporate: 170, property: 85, other: 38 },
  { month: 'May', income: 380, corporate: 155, property: 92, other: 34 },
  { month: 'Jun', income: 365, corporate: 160, property: 90, other: 37 },
  { month: 'Jul', income: 370, corporate: 165, property: 88, other: 35 },
  { month: 'Aug', income: 360, corporate: 157, property: 91, other: 33 },
  { month: 'Sep', income: 380, corporate: 162, property: 89, other: 36 },
  { month: 'Oct', income: 395, corporate: 168, property: 87, other: 38 },
  { month: 'Nov', income: 410, corporate: 172, property: 92, other: 40 },
  { month: 'Dec', income: 430, corporate: 180, property: 95, other: 42 },
];
