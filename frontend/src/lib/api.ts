
export const fetchStats = async () => {
    const response = await fetch('/api/stats');
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
};

export const fetchUsers = async () => {
    const response = await fetch('/api/users');
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
};

export const calculateTax = async (income: number) => {
    const response = await fetch('/api/tax/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ income }),
    });
    if (!response.ok) throw new Error('Failed to calculate tax');
    return response.json();
};

export const addUser = async (userData: any) => {
    const response = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
    });
    if (!response.ok) throw new Error('Failed to add user');
    return response.json();
};

export const flagUser = async (userId: string) => {
    const response = await fetch(`/api/users/flag/${userId}`, {
        method: 'PUT',
    });
    if (!response.ok) throw new Error('Failed to toggle flag');
    return response.json();
};

export const processPayment = async (data: { user_id: string; amount: number }) => {
    const response = await fetch('/api/payments/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to process payment');
    return response.json();
};

export const sendNotice = async (userId: string, type: string) => {
    const response = await fetch(`/api/notices/send/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type }),
    });
    if (!response.ok) throw new Error('Failed to send notice');
    return response.json();
};
