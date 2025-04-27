const express = require('express');
const router = express.Router();
const db = require('../db'); // Import database connection

// API 1: Get all users (for frontend dashboard)
router.get('/users', (req, res) => {
  db.query('SELECT * FROM users', (err, results) => {
    if (err) throw err;
    res.json(results); // Send data as JSON
  });
});

// API 2: Add a new user (for AI input)
router.post('/users', (req, res) => {
  const { user_id, declared_income, observed_transactions, income_source } = req.body;
  db.query(
    'INSERT INTO users (user_id, declared_income, observed_transactions, income_source) VALUES (?, ?, ?, ?)',
    [user_id, declared_income, observed_transactions, income_source],
    (err) => {
      if (err) throw err;
      res.send('User added successfully!');
    }
  );
});

// API 3: Flag suspicious users (called by AI model)
router.put('/users/flag/:id', (req, res) => {
  const { id } = req.params;
  db.query(
    'UPDATE users SET flagged = TRUE WHERE user_id = ?',
    [id],
    (err) => {
      if (err) throw err;
      res.send(`User ${id} flagged as suspicious!`);
    }
  );
});

module.exports = router;
