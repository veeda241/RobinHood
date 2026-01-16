# RobinHood AI - Tax Compliance Intelligence System

![RobinHood AI](https://img.shields.io/badge/RobinHood-AI%20Tax%20System-667eea?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-38ef7d?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-f45c43?style=for-the-badge&logo=flask&logoColor=white)

A smart tax compliance system that helps citizens pay taxes correctly and enables tax administrators to manage taxpayer records, send notices, and track compliance.

## 🌟 Features

### For Citizens
- **Tax Calculator**: Calculate your tax liability based on the new tax regime (FY 2024-25)
- **Slab-wise Breakdown**: See exactly how much tax applies to each income bracket
- **Compliance Status**: Check if you're compliant or have pending dues

### For Administrators
- **Dashboard**: View all taxpayers with real-time stats
- **Notice System**: Send reminder, warning, final, or penalty notices
- **Payment Processing**: Record tax payments
- **Flagging System**: Flag suspicious accounts for review
- **CLI Tool**: Powerful command-line interface for quick operations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL Server
- pip

### Installation

1. **Clone and navigate to the project**
```bash
cd RobinHood
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up the database**
```bash
mysql -u root -p < setup_database.sql
```

4. **Configure database connection** (edit `db.py` if needed)

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**: http://localhost:5000

## 📊 CLI Usage

The CLI provides powerful administration capabilities:

```bash
# Calculate tax for an income
python robinhood_cli.py calculate 1200000

# Compare multiple incomes
python robinhood_cli.py compare 500000 1000000 1500000

# View tax slabs
python robinhood_cli.py slabs

# List all taxpayers
python robinhood_cli.py users

# View system statistics
python robinhood_cli.py stats

# Add a new taxpayer
python robinhood_cli.py add USER001 800000 --paid 25000

# Record a payment
python robinhood_cli.py pay USER001 50000

# Send a notice
python robinhood_cli.py notice USER001 --type warning

# Send reminders to all underpaid users
python robinhood_cli.py remind

# Flag a user for review
python robinhood_cli.py flag USER001
```

## 📋 Tax Slabs (New Regime 2024-25)

| Income Range | Tax Rate |
|-------------|----------|
| Up to ₹3,00,000 | NIL |
| ₹3,00,001 - ₹6,00,000 | 5% |
| ₹6,00,001 - ₹9,00,000 | 10% |
| ₹9,00,001 - ₹12,00,000 | 15% |
| ₹12,00,001 - ₹15,00,000 | 20% |
| Above ₹15,00,000 | 30% |

## ⚛️ Modern React Frontend (New!)

The project now features a state-of-the-art React frontend built with Vite, Tailwind CSS, and Shadcn UI.

### Development Mode
To run the frontend in development mode with hot reloading:
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at http://localhost:8080. It is configured to proxy API requests to the Python backend on port 5000.

### Building for Production
To build the frontend and serve it via Flask:
```bash
cd frontend
npm install
npm run build
```
Once built, the Flask server will automatically serve the React app from `frontend/dist`.

## 📁 Project Structure

```
RobinHood/
├── app.py              # Flask backend
├── frontend/           # Modern React frontend
│   ├── src/            # React components & hooks
│   ├── dist/           # Built files for production
│   └── vite.config.ts  # Vite configuration
├── models.py           # Database models
├── tax_agent.py        # Tax calculation logic
├── db.py               # Database connection
├── robinhood_cli.py    # CLI administration tool
├── requirements.txt    # Python dependencies
└── setup_database.sql  # Database setup script
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | GET | Get all taxpayers |
| `/api/users` | POST | Add new taxpayer |
| `/api/users/flag/<id>` | PUT | Toggle flag on user |
| `/api/tax/calculate` | POST | Calculate tax |
| `/api/payments/process` | POST | Process payment |
| `/api/notices/send/<id>` | POST | Send notice |
| `/api/stats` | GET | Get system stats |

## 🎨 Features of UI

- Modern dark theme with glassmorphism effects
- Real-time statistics dashboard
- Interactive tax calculator with breakdown
- Notice management system
- Responsive design for all devices

## 📜 License

MIT License - Feel free to use and modify!

## 🎨 Tech Stack

- **Backend**: Python, Flask, MySQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React
- **UI Components**: Shadcn UI (Radix UI)
- **Data Fetching**: TanStack Query (React Query)
- **State Management**: React Hooks & Context

---

Built with ❤️ by RobinHood AI Team