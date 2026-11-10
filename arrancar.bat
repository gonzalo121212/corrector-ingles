@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "HASH="
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile requirements.txt SHA256') do if not defined HASH set "HASH=%%h"
set "HASH=%HASH: =%"
set "MARCA="
if exist ".venv\.instalado" set /p MARCA=<".venv\.instalado"
if defined HASH if "%MARCA%"=="%HASH%" goto arrancar
if exist ".venv\Scripts\python.exe" goto instalar

set "PY="
py -3.12 --version >nul 2>nul
if not errorlevel 1 set "PY=py -3.12"
if defined PY goto crear
python --version >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto crear
echo No se encuentra Python. Instala Python 3.12 desde python.org y vuelve a probar.
pause
exit /b 1

:crear
%PY% --version
echo Primera vez: se van a instalar las dependencias.
echo Tarda un par de minutos. No cierres la ventana.
%PY% -m venv .venv
if errorlevel 1 goto fallo

:instalar
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fallo
>".venv\.instalado" echo %HASH%

:arrancar
".venv\Scripts\python.exe" -m corrector
if errorlevel 1 goto fallo
exit /b 0

:fallo
echo.
echo Algo ha fallado. Lee el mensaje de arriba.
pause
exit /b 1
