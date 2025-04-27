const mysql = require('mysql');

// Configure MySQL connection (XAMPP default credentials)
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',      // Default XAMPP username
  password: '',      // Default XAMPP password (empty)
  database: 'robinhood_db' // Create this DB in phpMyAdmin
});

// Connect to MySQL
db.connect(err => {
  if (err) throw err;
  console.log('MySQL Connected!');
});

module.exports = db;
