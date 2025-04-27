const express = require('express');
const cors = require('cors');
const db = require('./db'); // Import DB connection

const app = express();
app.use(cors());
app.use(express.json()); // You don't need body-parser anymore

// Import routes
const userRoutes = require('./routes/users');
app.use('/api', userRoutes);

// Default route (optional)
app.get('/', (req, res) => {
    res.send('Welcome to Robinhood Backend 🚀');
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
