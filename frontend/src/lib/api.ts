// Gateway API client. Every request:
//   * sends cookies (Flask admin session) via credentials: 'include'
//   * attaches a Supabase Bearer JWT when a citizen session exists
//   * surfaces HTTP errors as typed Error objects (status included) so the
//     UI can react to 401/403 (redirect to login) without parsing strings.
import { getAccessToken } from './supabase';

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

async function request(path: string, options: RequestInit = {}) {
    const headers = new Headers(options.headers || {});
    if (options.body) headers.set('Content-Type', 'application/json');
    const token = await getAccessToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);

    const response = await fetch(path, { ...options, headers, credentials: 'include' });
    if (!response.ok) {
        let detail = '';
        try {
            const body = await response.json();
            detail = typeof body?.error === 'string' ? body.error : '';
        } catch {
            /* non-JSON error body - use status only */
        }
        throw new ApiError(detail || `Request failed (${response.status})`, response.status);
    }
    return response.json();
}

const post = (path: string, body?: unknown) =>
    request(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });

// --- Session / auth ----------------------------------------------------------

export const fetchMe = () => request('/api/auth/me');
export const adminLogin = (email: string, password: string) =>
    post('/api/admin/login', { email, password });
export const adminLogout = () => post('/api/admin/logout');

// --- Tax intelligence (public) ------------------------------------------------

export const calculateTax = (income: number) => post('/api/tax/calculate', { income });

export const optimizeTax = (grossIncome: number, deductions: Record<string, number>, senior = false) =>
    post('/api/tax/optimize', { gross_income: grossIncome, deductions, senior });

export const fetchTaxCurve = (params: { income_max?: number; '80C'?: number; '80D'?: number; HRA?: number; senior?: boolean }) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && qs.set(k, String(v)));
    return request(`/api/tax/curve?${qs.toString()}`);
};

export const fetchRegulations = () => request('/api/regulations');

// --- Citizen assessment gateway (needs Supabase JWT or demo mode) -------------

export const assessTax = (payload: {
    gross_income: number; name?: string; tax_paid?: number;
    deductions?: Record<string, number>; pan?: string; assets_value?: number;
}) => post('/api/tax/assess', payload);

// --- Admin dashboard ----------------------------------------------------------

export const fetchStats = () => request('/api/stats');
export const fetchUsers = () => request('/api/users');
export const addUser = (userData: Record<string, unknown>) => post('/api/users', userData);
export const flagUser = (userId: string) =>
    request(`/api/users/flag/${encodeURIComponent(userId)}`, { method: 'PUT' });
export const processPayment = (data: { user_id: string; amount: number }) =>
    post('/api/payments/process', data);
export const sendNotice = (userId: string, type: string) =>
    post(`/api/notices/send/${encodeURIComponent(userId)}`, { type });
export const fetchNoticeHistory = (userId: string) =>
    request(`/api/notices/${encodeURIComponent(userId)}`);

// --- Intelligence / audit feeds ------------------------------------------------

export const fetchRiskFeed = () => request('/api/risk');
export const fetchTrends = () => request('/api/trends');
export const fetchAuditTrail = (limit = 50) => request(`/api/audit/trail?limit=${limit}`);
export const verifyAuditChain = () => request('/api/audit/verify');
