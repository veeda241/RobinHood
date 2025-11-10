@echo off
echo "Starting CivTax Application..."

REM Step 1: Set up the database
echo "Setting up the database..."
python setup_db.py

REM Step 2: Start the Flask backend server in a new window
echo "Starting the backend server..."
start cmd /k python app.py

REM Step 3: Wait for the server to start
timeout /t 2 /nobreak > nul

REM Step 4: Open the web browser with a cache-busting parameter
echo "Opening the application in your web browser..."
start http://localhost:5000/?_=%random%

echo "CivTax application is running."
