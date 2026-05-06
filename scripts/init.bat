@echo off
echo MES Inventory HomeBase Setup
echo.
echo Installing dependencies...
pip install flask flask-cors
echo.
echo Initializing database...
cd server
python init_db.py
echo.
echo Setup complete!
echo Run run-server.bat to start the web server.
pause
