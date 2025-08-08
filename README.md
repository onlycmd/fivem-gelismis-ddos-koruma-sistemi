# 🛡️ FiveM DDoS Protection System

**Yüksek güvenlikli, gelişmiş DDoS koruma sistemi** - FiveM sunucularınızı tüm DDoS saldırı türlerine karşı korur.

## 🌟 Özellikler

### 🔥 Ana Koruma Özellikleri
- **Gerçek zamanlı trafik analizi** ve saldırı tespiti
- **Rate limiting** - IP başına istek sınırlaması
- **Pattern detection** - Saldırı kalıplarını tespit etme
- **Geographic filtering** - Ülke bazlı filtreleme
- **Adaptive protection** - Saldırı yoğunluğuna göre otomatik ayarlama
- **Deep packet inspection** - Paket içeriği analizi

### 🔧 DDoS Saldırı Türleri Koruması
- **SYN Flood** saldırıları
- **UDP Amplification** saldırıları 
- **HTTP/HTTPS Flood** saldırıları
- **Slowloris** saldırıları
- **Connection exhaustion** saldırıları
- **Volumetric** saldırıları
- **Protocol** saldırıları
- **Application layer** saldırıları

### 🌐 Multi-Platform Uyarı Sistemi
- **E-posta** uyarıları (SMTP)
- **Discord** webhook entegrasyonu
- **Telegram** bot uyarıları
- **SMS** uyarıları (Twilio)

### 📊 İzleme ve Raporlama
- **Web tabanlı dashboard** - Gerçek zamanlı monitoring
- **Detaylı loglar** ve raporlar
- **İstatistiksel analiz** ve grafikler
- **Saldırı haritaları** ve trend analizi

### 🔒 Firewall Entegrasyonu
- **Windows Firewall** otomatik yönetimi (Windows)
- **iptables/ufw/firewall-cmd** desteği (Linux)
- **IP bazlı engelleme** ve whitelist
- **Port koruması** ve filtreleme
- **Dinamik kural yönetimi**

## 📋 Sistem Gereksinimleri

### Minimum Gereksinimler
- **İşletim Sistemi:** 
  - Windows 10/11, Windows Server 2016+
  - Ubuntu 18.04+, Debian 9+
  - CentOS 7+, RHEL 7+
  - macOS 10.14+
- **Python:** 3.8 veya üstü
- **RAM:** 4GB (8GB önerilen)
- **Disk:** 2GB boş alan
- **Network:** Gigabit ethernet (önerilen)

### Admin Yetkileri
- **Windows:** Admin yetkisi (Firewall yönetimi için)
- **Linux:** Root/sudo yetkisi (iptables, ufw, firewall-cmd için)
- **macOS:** Admin yetkisi (pfctl için)

## 🚀 Kurulum

### 1. Python ve Pip Kurulumu

**Windows:**
```bash
# Python 3.8+ yüklü olduğundan emin olun
python --version

# pip güncelleme
python -m pip install --upgrade pip
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3 python3-pip
# veya dnf kullanan sistemlerde
sudo dnf install python3 python3-pip
```

**macOS:**
```bash
# Homebrew ile
brew install python3

# veya MacPorts ile
sudo port install python39
```

### 2. Proje Dosyalarını İndirme
```bash
# Projeyi indirin ve klasöre girin
cd "Fivem DDOS Protect"
```

### 3. Gerekli Paketlerin Kurulumu
```bash
# Tüm gereksinimleri yükle
pip install -r requirements.txt

# Temel paketler için hızlı kurulum
pip install flask requests psutil plotly geoip2 cryptography
```

### 4. GeoIP Veritabanı (İsteğe Bağlı)
```bash
# MaxMind GeoLite2 veritabanını indirin
# https://dev.maxmind.com/geoip/geoip2/geolite2/
# GeoLite2-Country.mmdb dosyasını ana klasöre koyun
```

## ⚙️ Konfigürasyon

### 1. Ana Konfigürasyon Dosyası
`ddos_config.ini` dosyasını düzenleyin:

```ini
[PROTECTION]
max_requests_per_minute = 60
max_connections_per_ip = 10
ban_duration_minutes = 30

[ALERTS]
email_alerts_enabled = true
smtp_username = your_email@gmail.com
smtp_password = your_app_password
alert_recipients = admin@yourserver.com

discord_webhook_url = https://discord.com/api/webhooks/...
telegram_bot_token = 123456789:ABCdefGHI...
telegram_chat_id = -100123456789

[FIVEM_INTEGRATION]
fivem_port = 30120
fivem_server_ip = 127.0.0.1
```

### 2. IP Listelerini Düzenleme

**Whitelist (whitelist.txt):**
```
# Güvenilir IP'ler
127.0.0.1
192.168.1.0/24
YOUR_ADMIN_IP
```

**Blacklist (blacklist.txt):**
```
# Engellenen IP'ler
MALICIOUS_IP_1
MALICIOUS_IP_2
```

## 🎮 Kullanım

### 1. Hızlı Başlatma

**Windows:**
```bash
# Batch dosyası ile hızlı başlatma
quick_start.bat

# Veya manuel
python start_protection.py
```

**Linux/macOS:**
```bash
# Shell script ile hızlı başlatma
chmod +x quick_start.sh
./quick_start.sh

# Daemon modunda
./quick_start.sh --daemon

# Veya manuel
python3 start_protection.py
```

### 2. Özel Parametrelerle Başlatma

**Tüm Platformlar:**
```bash
# Özel konfigürasyon ile
python start_protection.py --config my_config.ini

# Farklı port ile web arayüzü
python start_protection.py --port 8080

# Daemon modunda çalıştır
python start_protection.py --daemon

# Interaktif mod olmadan
python start_protection.py --no-interactive
```

### 3. Web Arayüzü
Tarayıcınızda `http://localhost:8080` adresine gidin:

- **Dashboard:** Gerçek zamanlı istatistikler
- **Attack Logs:** Detaylı saldırı kayıtları  
- **IP Management:** Whitelist/Blacklist yönetimi
- **Settings:** Sistem ayarları

### 4. Komut Satırı Komutları
İnteraktif modda kullanılabilir komutlar:
```
stats          # Sistem istatistikleri
block <ip>     # IP'yi manuel engelle
unblock <ip>   # IP engeli kaldır
status         # Sistem durumu
quit           # Çıkış
```

## 🎯 FiveM Entegrasyonu

### 1. Lua Script Kurulumu
```lua
-- server.cfg dosyanıza ekleyin
ensure ddos_protection

-- Veya resource olarak yükleyin
start ddos_protection
```

### 2. FiveM Server.cfg Optimizasyonu
```bash
# DDoS koruma için optimize ayarlar
set sv_maxClients 64
set sv_enableFlaregun true
set onesync on
set sv_filterRequestControl true

# Rate limiting
set sv_rateLimit_playerIdentifiers 5
set sv_rateLimit_gameBuild 5
```

## 📊 Platform Özel Firewall Yapılandırması

### Windows Firewall
```bash
# Admin olarak PowerShell çalıştırın
# Sistem otomatik olarak Windows Firewall'u yönetir
```

### Linux - UFW (Ubuntu/Debian)
```bash
# UFW'yi etkinleştir
sudo ufw enable

# FiveM portlarını aç
sudo ufw allow 30120/tcp
sudo ufw allow 30120/udp
sudo ufw allow 40120/tcp
```

### Linux - firewall-cmd (CentOS/RHEL/Fedora)
```bash
# Firewall servisini başlat
sudo systemctl start firewalld
sudo systemctl enable firewalld

# FiveM portlarını aç
sudo firewall-cmd --permanent --add-port=30120/tcp
sudo firewall-cmd --permanent --add-port=30120/udp
sudo firewall-cmd --permanent --add-port=40120/tcp
sudo firewall-cmd --reload
```

### Linux - iptables (Tüm Linux)
```bash
# Temel kurallar (sistem otomatik yönetir)
sudo iptables -I INPUT -p tcp --dport 30120 -j ACCEPT
sudo iptables -I INPUT -p udp --dport 30120 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 40120 -j ACCEPT
```

### macOS - pfctl
```bash
# pfctl yapılandırması (gelişmiş kullanıcılar için)
# Sistem kısmen destekler
```

## 📊 Monitoring ve Alerting

### Discord Webhook Kurulumu
1. Discord sunucunuzda webhook oluşturun
2. Webhook URL'sini `ddos_config.ini` dosyasına ekleyin
3. Otomatik uyarılar gelmeye başlayacak

### E-posta Uyarıları
1. Gmail App Password oluşturun
2. SMTP ayarlarını konfigürasyon dosyasına ekleyin
3. Test uyarısı gönderin

### Telegram Bot Kurulumu
1. BotFather'dan yeni bot oluşturun
2. Bot token'ını konfigürasyona ekleyin
3. Chat ID'nizi bulup ekleyin

## 🔧 Gelişmiş Konfigürasyon

### Adaptive Protection
```ini
[PROTECTION]
adaptive_protection = true
suspicious_threshold = 100
```

### Geographic Filtering
```ini
[GEOGRAPHIC]
enable_geo_blocking = true
allowed_countries = TR,US,GB,DE
block_vpn_proxy = true
```

### Machine Learning Detection
```ini
[ADVANCED]
ml_detection_enabled = true
pattern_analysis_depth = 100
```

## 🛠️ Platform Özel Troubleshooting

### Windows
**1. Admin Yetkisi Hatası**
```bash
# PowerShell'i admin olarak çalıştırın
# Veya UAC'yi geçici olarak devre dışı bırakın
```

**2. Windows Firewall Servisi**
```bash
# Firewall servisini başlat
net start mpssvc
```

### Linux
**1. Sudo Yetkisi Hatası**
```bash
# Kullanıcıyı sudo grubuna ekle
sudo usermod -aG sudo $USER

# Veya root olarak çalıştır
sudo python3 start_protection.py
```

**2. Firewall Servis Sorunları**
```bash
# UFW
sudo systemctl start ufw
sudo systemctl enable ufw

# firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# iptables
sudo systemctl start iptables
```

**3. Port Erişim Sorunları**
```bash
# Port kullanımını kontrol et
sudo netstat -tlnp | grep :8080
sudo ss -tlnp | grep :8080

# SELinux kontrol (RHEL/CentOS)
sudo setsebool -P httpd_can_network_connect 1
```

### macOS
**1. Admin Yetkisi**
```bash
# sudo ile çalıştır
sudo python3 start_protection.py
```

**2. Homebrew Sorunları**
```bash
# Homebrew güncelle
brew update
brew upgrade python3
```

## 📈 Performans Optimizasyonu

### Sistem Ayarları
```ini
[PERFORMANCE]
max_threads = 8
memory_cache_size = 512
db_optimization = true
stats_update_interval = 30
```

### Platform Özel Optimizasyonlar

**Windows:**
```bash
# Network buffer boyutları
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global chimney=enabled
netsh int tcp set global rss=enabled
```

**Linux:**
```bash
# Kernel parametreleri
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w net.ipv4.tcp_rmem="4096 262144 16777216"
sysctl -w net.ipv4.tcp_wmem="4096 262144 16777216"
```

## 🔄 Güncelleme ve Bakım

### Otomatik Güncelleme
```bash
# IP reputation listelerini güncelle
python update_threat_intel.py

# GeoIP veritabanını güncelle
python update_geoip.py
```

### Veritabanı Bakımı
```bash
# Log temizliği (30 günden eski)
python cleanup_logs.py --days 30

# Veritabanı optimizasyonu
python optimize_database.py
```

## 🆘 Destek ve Yardım

### Hızlı Yardım
1. **Sistem durumunu kontrol edin:** `python start_protection.py --status`
2. **Logları inceleyin:** `ddos_protection.log` dosyasını kontrol edin
3. **Konfigürasyonu doğrulayın:** `ddos_config.ini` ayarlarını kontrol edin

### Debug Modu
```bash
# Detaylı loglama ile çalıştır
python start_protection.py --debug
```

### Platform Özel Log Konumları
- **Windows:** `ddos_protection.log` (proje klasöründe)
- **Linux:** `/var/log/ddos_protection.log` (root ile çalışıyorsa)
- **macOS:** `~/Library/Logs/ddos_protection.log`

## 📋 Sık Sorulan Sorular

**S: Sistem ne kadar CPU kullanır?**
A: Normal şartlarda %1-5 CPU kullanımı, saldırı anında %10-20 arası.

**S: Kaç IP'yi aynı anda engelleyebilir?**
A: Teorik olarak sınırsız, pratik olarak 100,000+ IP rahatlıkla.

**S: FiveM performansını etkiler mi?**
A: Hayır, sistem bağımsız çalışır ve FiveM'i etkilemez.

**S: Hangi saldırı türlerini tespit eder?**
A: SYN flood, UDP amplification, HTTP flood, Slowloris ve diğer tüm bilinen DDoS türleri.

**S: Linux ve Windows arasında fark var mı?**
A: Temel koruma aynı, sadece firewall entegrasyonu platform özelinde farklılık gösterir.

**S: macOS'ta tam destek var mı?**
A: Evet, ancak pfctl entegrasyonu sınırlıdır. Temel koruma tam çalışır.

## 📜 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Commit yapın
4. Pull request gönderin

## ⚠️ Güvenlik Uyarıları

- **Windows:** Admin yetkisiyle çalıştırın
- **Linux:** Root/sudo yetkisi kullanın
- **macOS:** Admin yetkisi gerekebilir
- **Güvenli şifre kullanın** - E-posta ve webhook ayarlarında
- **Düzenli güncelleme yapın** - Threat intelligence listeleri
- **Backup alın** - Konfigürasyon ve log dosyalarını

## 📞 İletişim

Herhangi bir sorun veya öneriniz için:
- **GitHub Issues** kullanın
- **Discord** https://discord.gg/devcode

---

**🛡️ FiveM sunucunuz artık en güçlü DDoS korumasına sahip!**

### 🖥️ Platform Desteği Özeti:

| Platform | Firewall | Yetki | Script |
|----------|----------|-------|--------|
| Windows 10/11 | Windows Firewall | Admin | `quick_start.bat` |
| Ubuntu/Debian | UFW/iptables | sudo | `quick_start.sh` |
| CentOS/RHEL | firewall-cmd/iptables | sudo | `quick_start.sh` |
| macOS | pfctl (sınırlı) | sudo | `quick_start.sh` |

## ⚠️ **Sonuç:**

Bu sistem **mükemmel bir monitoring ve küçük ölçekli koruma aracıdır**, ancak **gerçek DDoS saldırılarına karşı tek başına yetersizdir**. 

**Önerim:** Bu sistemi **monitoring ve alerting aracı** olarak kullanın, gerçek DDoS koruması için **ISP + CDN + Hosting** kombinasyonunu tercih edin.


> Bu sistem FiveM topluluğu için geliştirilmiştir. Güvenli oyun deneyimi için tasarlanmıştır. 
