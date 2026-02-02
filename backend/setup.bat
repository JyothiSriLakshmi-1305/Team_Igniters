@echo off
echo ====================================
echo Smart Attendance System - Setup
echo ====================================
echo.

echo Installing Python packages...
pip install -r requirements.txt

echo.
echo Creating directories...
python -c "from config import Config; Config.create_directories()"

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Run: python face_capture.py (capture students)
echo 2. Run: python train_model.py (train model)
echo 3. Run: python app.py (start backend)
echo.
pause