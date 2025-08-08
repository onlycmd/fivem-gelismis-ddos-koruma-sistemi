@echo off
title FiveM DDoS Protection System - Quick Start
color 0A

echo.
echo  =================================================================
echo    🛡️  FiveM DDoS Protection System - Hızlı Başlatma
echo  =================================================================
echo.

echo ⏳ Python kontrolü yapılıyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadı! Python 3.8+ yüklü olduğundan emin olun.
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python bulundu!
echo.

echo ⏳ Gerekli paketler kontrol ediliyor...
python -c "import flask, requests, psutil" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Bazı paketler eksik! Yükleniyor...
    pip install flask requests psutil plotly configparser
    if errorlevel 1 (
        echo ❌ Paket yükleme başarısız!
        pause
        exit /b 1
    )
    echo ✅ Paketler yüklendi!
) else (
    echo ✅ Tüm paketler mevcut!
)

echo.
echo ⏳ Konfigürasyon dosyaları kontrol ediliyor...

if not exist "ddos_config.ini" (
    echo ⚠️  Konfigürasyon dosyası bulunamadı, oluşturuluyor...
    copy /y nul ddos_config.ini >nul
)

if not exist "whitelist.txt" (
    echo ⚠️  Whitelist dosyası bulunamadı, oluşturuluyor...
    copy /y nul whitelist.txt >nul
)

if not exist "blacklist.txt" (
    echo ⚠️  Blacklist dosyası bulunamadı, oluşturuluyor...
    copy /y nul blacklist.txt >nul
)

echo ✅ Konfigürasyon dosyaları hazır!
echo.

echo 🚀 FiveM DDoS koruma sistemi başlatılıyor...
echo.
echo  📊 Web Arayüzü: http://localhost:8080
echo  🛡️  Sistem aktif olduktan sonra FiveM sunucunuz korunacak
echo  ⚠️  Admin yetkisi gerekebilir (Firewall yönetimi için)
echo.

pause

rem Admin yetkisi kontrolü
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Admin yetkisi tespit edilemedi!
    echo    Firewall entegrasyonu için admin olarak çalıştırın.
    echo.
)

echo ▶️  Sistem başlatılıyor...
echo.

python start_protection.py

echo.
echo 🔴 Sistem durduruldu.
pause 