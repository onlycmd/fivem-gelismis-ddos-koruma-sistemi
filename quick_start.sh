#!/bin/bash

# FiveM DDoS Protection System - Quick Start (Linux/macOS)
# Renkli çıktı için ANSI kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Terminal başlığı
echo -e "${GREEN}"
echo "================================================================="
echo "    🛡️  FiveM DDoS Protection System - Hızlı Başlatma"
echo "================================================================="
echo -e "${NC}"

# Python kontrolü
echo -e "${YELLOW}⏳ Python kontrolü yapılıyor...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✅ Python3 bulundu!${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}✅ Python bulundu!${NC}"
else
    echo -e "${RED}❌ Python bulunamadı! Python 3.8+ yüklü olduğundan emin olun.${NC}"
    echo -e "${BLUE}   Ubuntu/Debian: sudo apt install python3 python3-pip${NC}"
    echo -e "${BLUE}   CentOS/RHEL: sudo yum install python3 python3-pip${NC}"
    echo -e "${BLUE}   macOS: brew install python3${NC}"
    exit 1
fi

# Python versiyonu kontrolü
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${CYAN}   Python Versiyonu: $PYTHON_VERSION${NC}"

# Pip kontrolü
echo -e "${YELLOW}⏳ Pip kontrolü yapılıyor...${NC}"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo -e "${RED}❌ Pip bulunamadı!${NC}"
    echo -e "${BLUE}   Ubuntu/Debian: sudo apt install python3-pip${NC}"
    echo -e "${BLUE}   CentOS/RHEL: sudo yum install python3-pip${NC}"
    echo -e "${BLUE}   macOS: python3 -m ensurepip${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pip bulundu!${NC}"

# Gerekli paketleri kontrol et
echo -e "${YELLOW}⏳ Gerekli paketler kontrol ediliyor...${NC}"
if $PYTHON_CMD -c "import flask, requests, psutil" 2>/dev/null; then
    echo -e "${GREEN}✅ Tüm paketler mevcut!${NC}"
else
    echo -e "${YELLOW}⚠️  Bazı paketler eksik! Yükleniyor...${NC}"
    
    # Temel paketleri yükle
    echo -e "${CYAN}   Flask, requests, psutil yükleniyor...${NC}"
    if $PIP_CMD install flask requests psutil plotly configparser --user; then
        echo -e "${GREEN}✅ Paketler yüklendi!${NC}"
    else
        echo -e "${RED}❌ Paket yükleme başarısız!${NC}"
        echo -e "${YELLOW}   Manuel yükleme deneyin: $PIP_CMD install -r requirements.txt${NC}"
        exit 1
    fi
fi

# Konfigürasyon dosyaları kontrolü
echo -e "${YELLOW}⏳ Konfigürasyon dosyaları kontrol ediliyor...${NC}"

if [ ! -f "ddos_config.ini" ]; then
    echo -e "${YELLOW}⚠️  Konfigürasyon dosyası bulunamadı, oluşturuluyor...${NC}"
    touch ddos_config.ini
fi

if [ ! -f "whitelist.txt" ]; then
    echo -e "${YELLOW}⚠️  Whitelist dosyası bulunamadı, oluşturuluyor...${NC}"
    touch whitelist.txt
fi

if [ ! -f "blacklist.txt" ]; then
    echo -e "${YELLOW}⚠️  Blacklist dosyası bulunamadı, oluşturuluyor...${NC}"
    touch blacklist.txt
fi

echo -e "${GREEN}✅ Konfigürasyon dosyaları hazır!${NC}"

# Sistem bilgisi
echo -e "${CYAN}📊 Sistem Bilgisi:${NC}"
echo -e "${BLUE}   OS: $(uname -s) $(uname -r)${NC}"
echo -e "${BLUE}   Mimari: $(uname -m)${NC}"
echo -e "${BLUE}   Python: $PYTHON_VERSION${NC}"

# Yetki kontrolü
echo -e "${YELLOW}⏳ Sistem yetkileri kontrol ediliyor...${NC}"
if [ "$EUID" -eq 0 ]; then
    echo -e "${GREEN}✅ Root yetkisi tespit edildi (Firewall entegrasyonu için ideal)${NC}"
elif groups $USER | grep -q "\bsudo\b"; then
    echo -e "${YELLOW}⚠️  Sudo yetkisi mevcut (Firewall için sudo gerekebilir)${NC}"
else
    echo -e "${YELLOW}⚠️  Root/sudo yetkisi tespit edilemedi${NC}"
    echo -e "${CYAN}   Firewall entegrasyonu sınırlı olabilir${NC}"
fi

# Port kontrolü
echo -e "${YELLOW}⏳ Port kullanımı kontrol ediliyor...${NC}"
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":8080 "; then
        echo -e "${YELLOW}⚠️  Port 8080 kullanımda, farklı port kullanılacak${NC}"
        WEB_PORT="8081"
    else
        WEB_PORT="8080"
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":8080 "; then
        echo -e "${YELLOW}⚠️  Port 8080 kullanımda, farklı port kullanılacak${NC}"
        WEB_PORT="8081"
    else
        WEB_PORT="8080"
    fi
else
    WEB_PORT="8080"
fi

echo -e "${GREEN}✅ Web arayüzü portu: $WEB_PORT${NC}"

# Firewall uyarısı (Linux için)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${YELLOW}🔥 Firewall Uyarısı:${NC}"
    echo -e "${CYAN}   Ubuntu/Debian: sudo ufw işlemleri için izin gerekebilir${NC}"
    echo -e "${CYAN}   CentOS/RHEL: sudo firewall-cmd işlemleri için izin gerekebilir${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}🔥 macOS Uyarısı:${NC}"
    echo -e "${CYAN}   pfctl firewall yönetimi için admin yetkisi gerekebilir${NC}"
fi

# Başlatma bilgisi
echo -e "${GREEN}🚀 FiveM DDoS koruma sistemi başlatılıyor...${NC}"
echo ""
echo -e "${PURPLE}  📊 Web Arayüzü: http://localhost:$WEB_PORT${NC}"
echo -e "${PURPLE}  🛡️  Sistem aktif olduktan sonra FiveM sunucunuz korunacak${NC}"
echo -e "${PURPLE}  ⚠️  Firewall entegrasyonu için admin/sudo yetkisi gerekebilir${NC}"
echo ""

# Kullanıcı onayı
echo -e "${YELLOW}Devam etmek için Enter'a basın, çıkmak için Ctrl+C...${NC}"
read -r

# Sistem başlatma
echo -e "${GREEN}▶️  Sistem başlatılıyor...${NC}"
echo ""

# Arka plan kontrolü
if [ "$1" = "--daemon" ]; then
    echo -e "${CYAN}🔄 Daemon modunda başlatılıyor...${NC}"
    nohup $PYTHON_CMD start_protection.py --daemon --port $WEB_PORT > ddos_protection.log 2>&1 &
    DDOS_PID=$!
    echo -e "${GREEN}✅ Sistem arka planda başlatıldı (PID: $DDOS_PID)${NC}"
    echo -e "${BLUE}   Log dosyası: ddos_protection.log${NC}"
    echo -e "${BLUE}   Durdurmak için: kill $DDOS_PID${NC}"
    echo ""
    echo -e "${PURPLE}🌐 Web arayüzü: http://localhost:$WEB_PORT${NC}"
else
    # Normal mod
    if [ -t 0 ]; then
        # İnteraktif terminal
        $PYTHON_CMD start_protection.py --port $WEB_PORT
    else
        # Non-interaktif
        $PYTHON_CMD start_protection.py --no-interactive --port $WEB_PORT
    fi
    
    echo ""
    echo -e "${RED}🔴 Sistem durduruldu.${NC}"
fi

# Cleanup fonksiyonu
cleanup() {
    echo -e "\n${YELLOW}🧹 Temizlik yapılıyor...${NC}"
    if [ ! -z "$DDOS_PID" ] && kill -0 $DDOS_PID 2>/dev/null; then
        echo -e "${CYAN}   Sistem durduruluyor...${NC}"
        kill $DDOS_PID
        sleep 2
        if kill -0 $DDOS_PID 2>/dev/null; then
            kill -9 $DDOS_PID
        fi
    fi
    echo -e "${GREEN}✅ Temizlik tamamlandı.${NC}"
}

# SIGINT ve SIGTERM yakalama
trap cleanup INT TERM

# Script bittiğinde
if [ "$1" != "--daemon" ]; then
    echo -e "${BLUE}Kurulum ve çalıştırma tamamlandı!${NC}"
    echo -e "${GREEN}🛡️ FiveM sunucunuz artık DDoS koruması altında!${NC}"
fi 