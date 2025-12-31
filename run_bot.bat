@echo off
echo Installing dependencies...
"c:\Users\hyoun\AppData\Local\Microsoft\WindowsApps\python3.12.exe" -m pip install -r requirements.txt
echo.
echo Starting Streamlit App...
"c:\Users\hyoun\AppData\Local\Microsoft\WindowsApps\python3.12.exe" -m streamlit run app.py
pause
