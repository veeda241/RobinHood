const apiUrl = '/api';

async function getUsers() {
    const response = await fetch(`${apiUrl}/users`);
    const users = await response.json();
    const tableBody = document.querySelector('#users-table tbody');
    tableBody.innerHTML = '';
    users.forEach(user => {
        let actions = `<button class="btn btn-danger" onclick="flagUser('${user.user_id}')">Flag</button>`;
        if (user.compliance_status === 'Underpaid') {
            actions += ` <button class="btn" onclick="sendReminder('${user.user_id}')">Send Reminder</button>`;
        }
        const row = `
            <tr>
                <td>${user.user_id}</td>
                <td>${user.declared_income}</td>
                <td>${user.tax_paid}</td>
                <td>${user.expected_tax}</td>
                <td>${user.compliance_status}</td>
                <td>
                    ${actions}
                </td>
            </tr>
        `;
        tableBody.innerHTML += row;
    });
}

async function addUser() {
    const userId = document.getElementById('user_id').value;
    const declaredIncome = document.getElementById('declared_income').value;
    await fetch(`${apiUrl}/users`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, declared_income: parseFloat(declaredIncome) })
    });
    alert('User added successfully!');
    document.getElementById('user_id').value = '';
    document.getElementById('declared_income').value = '';
    getUsers();
}

async function flagUser(userId) {
    await fetch(`${apiUrl}/users/flag/${userId}`, {
        method: 'PUT'
    });
    alert(`User ${userId} flagged as suspicious!`);
    getUsers();
}

async function calculateTax() {
    const income = document.getElementById('income').value;
    const response = await fetch(`${apiUrl}/tax/calculate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ income: parseFloat(income) })
    });
    const data = await response.json();
    document.getElementById('tax-amount').innerText = data.tax;
}

async function calculateSimulatedTax() {
    const income = document.getElementById('simulated_income').value;
    const response = await fetch(`${apiUrl}/tax/calculate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ income: parseFloat(income) })
    });
    const data = await response.json();
    document.getElementById('simulated-tax-amount').innerText = data.tax;
}

async function sendReminder(userId) {
    await fetch(`${apiUrl}/reminders/send/${userId}`, {
        method: 'POST'
    });
    alert(`Reminder sent to ${userId}!`);
}

getUsers();