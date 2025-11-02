const apiUrl = 'http://localhost:5000/api';

async function getUsers() {
    const response = await fetch(`${apiUrl}/users`);
    const users = await response.json();
    const tableBody = document.querySelector('#users-table tbody');
    tableBody.innerHTML = '';
    users.forEach(user => {
        const row = `
            <tr>
                <td>${user.user_id}</td>
                <td>${user.declared_income}</td>
                <td>${user.observed_transactions}</td>
                <td>${user.income_source}</td>
                <td>${user.tax_paid}</td>
                <td>${user.flagged}</td>
                <td>
                    <button class="btn" onclick="flagUser('${user.user_id}')">Flag</button>
                </td>
            </tr>
        `;
        tableBody.innerHTML += row;
    });
}

        async function addUser() {
            const user_id = document.getElementById('user_id').value;
            const declared_income = document.getElementById('declared_income').value;
            const observed_transactions = document.getElementById('observed_transactions').value;
            const income_source = document.getElementById('income_source').value;
            await fetch(`${apiUrl}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id, declared_income, observed_transactions, income_source })
            });
            alert('User added successfully!');
            document.getElementById('user_id').value = '';
            document.getElementById('declared_income').value = '';
            document.getElementById('observed_transactions').value = '';
            document.getElementById('income_source').value = '';
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

        async function processPayment() {
            const userId = document.getElementById('payment_user_id').value;
            const amount = document.getElementById('payment_amount').value;
            await fetch(`${apiUrl}/tax/pay`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ userId, amount: parseFloat(amount) })
            });
            alert(`Payment of ${amount} processed for user ${userId}!`);
            document.getElementById('payment_user_id').value = '';
            document.getElementById('payment_amount').value = '';
            getUsers();
        }
getUsers();
