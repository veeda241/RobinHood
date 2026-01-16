const apiUrl = '/api';
let allUsers = [];

// Tab Navigation
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.getElementById(tabId).style.display = 'block';
    document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
    if (tabId === 'notices') loadNotices();
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = message;
    toast.style.cssText = `position:fixed;bottom:30px;right:30px;padding:15px 25px;border-radius:10px;color:white;z-index:9999;animation:fadeIn 0.3s;background:${type === 'success' ? 'linear-gradient(135deg,#11998e,#38ef7d)' : type === 'error' ? 'linear-gradient(135deg,#eb3349,#f45c43)' : 'linear-gradient(135deg,#f2994a,#f2c94c)'}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Load users and update stats
async function getUsers() {
    try {
        const response = await fetch(`${apiUrl}/users`);
        allUsers = await response.json();
        renderUsersTable(allUsers);
        updateStats(allUsers);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function updateStats(users) {
    document.getElementById('total-users').textContent = users.length;
    document.getElementById('compliant-users').textContent = users.filter(u => u.compliance_status === 'Compliant').length;
    document.getElementById('underpaid-users').textContent = users.filter(u => u.compliance_status === 'Underpaid').length;
    document.getElementById('flagged-users').textContent = users.filter(u => u.flagged).length;
}

function renderUsersTable(users) {
    const tableBody = document.querySelector('#users-table tbody');
    tableBody.innerHTML = users.map(user => {
        const due = Math.max(0, user.expected_tax - user.tax_paid);
        const statusClass = user.compliance_status.toLowerCase();
        return `<tr>
            <td><strong>${user.user_id}</strong>${user.flagged ? ' 🚩' : ''}</td>
            <td>${formatCurrency(user.declared_income)}</td>
            <td>${formatCurrency(user.tax_paid)}</td>
            <td>${formatCurrency(user.expected_tax)}</td>
            <td style="color:${due > 0 ? '#f45c43' : '#38ef7d'}">${formatCurrency(due)}</td>
            <td><span class="status-badge ${statusClass}">${user.compliance_status}</span></td>
            <td class="action-btns">
                ${user.compliance_status === 'Underpaid' ? `<button class="btn btn-warning btn-sm" onclick="sendReminder('${user.user_id}')">📧</button>` : ''}
                <button class="btn ${user.flagged ? 'btn-success' : 'btn-danger'} btn-sm" onclick="toggleFlag('${user.user_id}', ${user.flagged})">${user.flagged ? '✓' : '🚩'}</button>
            </td>
        </tr>`;
    }).join('');
}

// Search functionality
document.getElementById('search-users')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allUsers.filter(u => u.user_id.toLowerCase().includes(query));
    renderUsersTable(filtered);
});

// Add new user
async function addUser() {
    const userId = document.getElementById('user_id').value;
    const declaredIncome = parseFloat(document.getElementById('declared_income').value);
    const taxPaid = parseFloat(document.getElementById('tax_paid')?.value || 0);
    
    if (!userId || !declaredIncome) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    try {
        await fetch(`${apiUrl}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, declared_income: declaredIncome, tax_paid: taxPaid })
        });
        showToast('Taxpayer registered successfully!');
        document.getElementById('user_id').value = '';
        document.getElementById('declared_income').value = '';
        if (document.getElementById('tax_paid')) document.getElementById('tax_paid').value = '';
        getUsers();
    } catch (error) {
        showToast('Error adding user', 'error');
    }
}

// Flag/Unflag user
async function toggleFlag(userId, isFlagged) {
    try {
        await fetch(`${apiUrl}/users/flag/${userId}`, { method: 'PUT' });
        showToast(isFlagged ? 'Flag removed' : 'User flagged as suspicious!', isFlagged ? 'success' : 'warning');
        getUsers();
    } catch (error) {
        showToast('Error updating flag', 'error');
    }
}

// Calculate tax with breakdown
async function calculateTax() {
    const income = parseFloat(document.getElementById('income').value);
    if (!income || income < 0) {
        showToast('Please enter valid income', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${apiUrl}/tax/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ income })
        });
        const data = await response.json();
        
        document.getElementById('tax-result').style.display = 'block';
        document.getElementById('tax-amount').textContent = formatCurrency(data.tax);
        
        // Show breakdown
        const breakdown = calculateBreakdown(income);
        document.getElementById('tax-breakdown').innerHTML = breakdown.map(item => 
            `<div class="breakdown-item"><span>${item.slab}</span><span>${formatCurrency(item.tax)}</span></div>`
        ).join('');
    } catch (error) {
        showToast('Error calculating tax', 'error');
    }
}

function calculateBreakdown(income) {
    const slabs = [];
    if (income <= 300000) return [{ slab: 'Tax-free (≤₹3L)', tax: 0 }];
    
    if (income > 300000) slabs.push({ slab: '₹3L - ₹6L @ 5%', tax: Math.min(income - 300000, 300000) * 0.05 });
    if (income > 600000) slabs.push({ slab: '₹6L - ₹9L @ 10%', tax: Math.min(income - 600000, 300000) * 0.10 });
    if (income > 900000) slabs.push({ slab: '₹9L - ₹12L @ 15%', tax: Math.min(income - 900000, 300000) * 0.15 });
    if (income > 1200000) slabs.push({ slab: '₹12L - ₹15L @ 20%', tax: Math.min(income - 1200000, 300000) * 0.20 });
    if (income > 1500000) slabs.push({ slab: 'Above ₹15L @ 30%', tax: (income - 1500000) * 0.30 });
    
    return slabs.filter(s => s.tax > 0);
}

// Send reminder
async function sendReminder(userId) {
    try {
        await fetch(`${apiUrl}/reminders/send/${userId}`, { method: 'POST' });
        showToast(`Reminder sent to ${userId}!`);
        addNoticeToList(userId, 'reminder', 'Payment reminder sent');
    } catch (error) {
        showToast('Error sending reminder', 'error');
    }
}

// Notices
let notices = [];

function loadNotices() {
    const container = document.getElementById('notices-list');
    container.innerHTML = notices.length ? notices.map(n => `
        <div class="notice-card ${n.type}">
            <div class="notice-icon ${n.type}">${n.type === 'danger' ? '🚨' : n.type === 'warning' ? '⚠️' : '📧'}</div>
            <div class="notice-content">
                <div class="notice-title">Notice to ${n.userId}</div>
                <div class="notice-message">${n.message}</div>
                <div class="notice-meta"><span>📅 ${n.date}</span><span>📋 ${n.noticeType}</span></div>
            </div>
        </div>
    `).join('') : '<p style="color:var(--text-muted);text-align:center;padding:40px;">No notices issued yet</p>';
}

function addNoticeToList(userId, type, message) {
    notices.unshift({
        userId, type: type === 'penalty' || type === 'final' ? 'danger' : type === 'warning' ? 'warning' : 'info',
        noticeType: type.charAt(0).toUpperCase() + type.slice(1),
        message, date: new Date().toLocaleDateString('en-IN')
    });
}

async function sendNotice() {
    const userId = document.getElementById('notice-user-id').value;
    const noticeType = document.getElementById('notice-type').value;
    
    if (!userId) { showToast('Enter Taxpayer ID', 'error'); return; }
    
    try {
        await fetch(`${apiUrl}/notices/send/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: noticeType })
        });
        
        const messages = {
            reminder: 'Payment reminder has been sent',
            warning: 'First warning notice issued',
            final: 'Final notice before legal action',
            penalty: 'Penalty notice with additional charges'
        };
        
        addNoticeToList(userId, noticeType, messages[noticeType]);
        showToast(`${noticeType.charAt(0).toUpperCase() + noticeType.slice(1)} notice sent to ${userId}!`);
        document.getElementById('notice-user-id').value = '';
        loadNotices();
    } catch (error) {
        showToast('Error sending notice', 'error');
    }
}

// Process payment
async function processPayment() {
    const userId = document.getElementById('payment-user-id').value;
    const amount = parseFloat(document.getElementById('payment-amount').value);
    
    if (!userId || !amount) { showToast('Fill all fields', 'error'); return; }
    
    try {
        await fetch(`${apiUrl}/payments/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, amount })
        });
        showToast(`Payment of ${formatCurrency(amount)} processed for ${userId}!`);
        document.getElementById('payment-user-id').value = '';
        document.getElementById('payment-amount').value = '';
        getUsers();
    } catch (error) {
        showToast('Error processing payment', 'error');
    }
}

// Quick actions
function refreshData() { getUsers(); showToast('Data refreshed!'); }

function checkAllCompliance() {
    const underpaid = allUsers.filter(u => u.compliance_status === 'Underpaid');
    showToast(`Found ${underpaid.length} underpaid taxpayers`, underpaid.length > 0 ? 'warning' : 'success');
}

function sendBulkReminders() {
    const underpaid = allUsers.filter(u => u.compliance_status === 'Underpaid');
    underpaid.forEach(u => addNoticeToList(u.user_id, 'reminder', 'Bulk reminder sent'));
    showToast(`Reminders sent to ${underpaid.length} taxpayers!`);
}

// Initialize
document.addEventListener('DOMContentLoaded', getUsers);