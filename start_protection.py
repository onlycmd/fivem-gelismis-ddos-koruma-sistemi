#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FiveM DDoS Protection System Starter
Tüm koruma bileşenlerini başlatan ana script
"""

import sys
import os
import time
import threading
import signal
import argparse
import logging
from pathlib import Path

# Kendi modüllerimizi import et
from ddos_protection import DDoSProtectionSystem
from firewall_integration import WindowsFirewallManager, AdvancedFirewallProtection
from alert_system import MultiPlatformAlertSystem
from web_monitor import app, init_ddos_system

class FiveMDDoSProtectionManager:
    """FiveM DDoS koruma sistemi yöneticisi"""
    
    def __init__(self, config_file: str = "ddos_config.ini"):
        self.config_file = config_file
        self.logger = self._setup_logging()
        
        # Sistem bileşenleri
        self.ddos_system = None
        self.firewall_manager = None
        self.advanced_firewall = None
        self.alert_system = None
        self.web_app_thread = None
        
        # Durum kontrolleri
        self.running = False
        self.shutdown_requested = False
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("FiveM DDoS Protection Manager başlatılıyor...")
    
    def _setup_logging(self) -> logging.Logger:
        """Loglama sistemini kur"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Ana logger
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('protection_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger('ProtectionManager')
    
    def _signal_handler(self, signum, frame):
        """Sistem sinyallerini yakala"""
        self.logger.info(f"Sinyal yakalandı: {signum}. Sistem kapatılıyor...")
        self.shutdown_requested = True
        self.stop_all_services()
    
    def check_requirements(self) -> bool:
        """Sistem gereksinimlerini kontrol et"""
        try:
            self.logger.info("Sistem gereksinimleri kontrol ediliyor...")
            
            # Python versiyonu
            if sys.version_info < (3, 8):
                self.logger.error("Python 3.8 veya üstü gerekli!")
                return False
            
            # Gerekli dosyalar
            required_files = [
                'ddos_config.ini',
                'whitelist.txt',
                'blacklist.txt'
            ]
            
            for file in required_files:
                if not os.path.exists(file):
                    self.logger.warning(f"Dosya bulunamadı, oluşturuluyor: {file}")
                    Path(file).touch()
            
            # Admin yetkisi kontrolü (Windows)
            try:
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    self.logger.warning("Firewall entegrasyonu için admin yetkisi öneriliyor")
            except:
                pass
            
            # Gerekli Python paketleri
            required_packages = [
                'flask', 'requests', 'psutil', 'plotly'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                self.logger.error(f"Eksik paketler: {', '.join(missing_packages)}")
                self.logger.error("Eksik paketleri yüklemek için: pip install -r requirements.txt")
                return False
            
            self.logger.info("Sistem gereksinimleri karşılanıyor ✓")
            return True
            
        except Exception as e:
            self.logger.error(f"Gereksinim kontrolü hatası: {e}")
            return False
    
    def start_ddos_protection(self) -> bool:
        """Ana DDoS koruma sistemini başlat"""
        try:
            self.logger.info("DDoS koruma sistemi başlatılıyor...")
            self.ddos_system = DDoSProtectionSystem(self.config_file)
            self.ddos_system.start_monitoring()
            self.logger.info("DDoS koruma sistemi aktif ✓")
            return True
        except Exception as e:
            self.logger.error(f"DDoS koruma sistemi başlatma hatası: {e}")
            return False
    
    def start_firewall_protection(self) -> bool:
        """Firewall koruma sistemini başlat"""
        try:
            self.logger.info("Firewall koruma sistemi başlatılıyor...")
            self.firewall_manager = WindowsFirewallManager()
            
            # Temel firewall kuralları
            self.firewall_manager.allow_fivem_traffic()
            self.firewall_manager.enable_ddos_protection_profile()
            
            # Gelişmiş firewall koruması
            self.advanced_firewall = AdvancedFirewallProtection(self.firewall_manager)
            if self.ddos_system:
                self.advanced_firewall.enable_adaptive_protection(self.ddos_system)
            
            self.logger.info("Firewall koruma sistemi aktif ✓")
            return True
        except Exception as e:
            self.logger.error(f"Firewall koruma sistemi hatası: {e}")
            return False
    
    def start_alert_system(self) -> bool:
        """Uyarı sistemini başlat"""
        try:
            self.logger.info("Uyarı sistemi başlatılıyor...")
            self.alert_system = MultiPlatformAlertSystem(self.ddos_system.config)
            self.alert_system.start_alert_worker()
            
            # Test uyarısı gönder
            self.alert_system.send_system_alert(
                "DDoS Koruma Sistemi Başlatıldı",
                "FiveM DDoS koruma sistemi başarıyla aktif edildi.",
                "INFO"
            )
            
            self.logger.info("Uyarı sistemi aktif ✓")
            return True
        except Exception as e:
            self.logger.error(f"Uyarı sistemi hatası: {e}")
            return False
    
    def start_web_interface(self, host: str = "0.0.0.0", port: int = 8080) -> bool:
        """Web monitoring arayüzünü başlat"""
        try:
            self.logger.info(f"Web arayüzü başlatılıyor: http://{host}:{port}")
            
            def run_web_app():
                try:
                    init_ddos_system()
                    app.run(host=host, port=port, debug=False, threaded=True)
                except Exception as e:
                    self.logger.error(f"Web arayüzü hatası: {e}")
            
            self.web_app_thread = threading.Thread(target=run_web_app, daemon=True)
            self.web_app_thread.start()
            
            self.logger.info("Web arayüzü aktif ✓")
            return True
        except Exception as e:
            self.logger.error(f"Web arayüzü başlatma hatası: {e}")
            return False
    
    def monitor_system_health(self):
        """Sistem sağlığını izle"""
        self.logger.info("Sistem sağlık izleme başlatıldı")
        
        while self.running and not self.shutdown_requested:
            try:
                # DDoS sistemi kontrolü
                if self.ddos_system and not self.ddos_system.running:
                    self.logger.warning("DDoS sistemi durmuş, yeniden başlatılıyor...")
                    self.ddos_system.start_monitoring()
                
                # İstatistikleri logla
                if self.ddos_system:
                    stats = self.ddos_system.get_statistics()
                    self.logger.info(
                        f"Sistem Durumu - "
                        f"Toplam İstek: {stats.get('total_requests', 0)}, "
                        f"Engellenen: {stats.get('blocked_requests', 0)}, "
                        f"Saldırı: {stats.get('attack_attempts', 0)}"
                    )
                
                # Kritik saldırı kontrolü
                if self.ddos_system and self.alert_system:
                    stats = self.ddos_system.get_statistics()
                    if stats.get('attack_attempts', 0) > 100:
                        self.alert_system.send_system_alert(
                            "Kritik Saldırı Aktivitesi",
                            f"Son dönemde {stats['attack_attempts']} saldırı tespit edildi!",
                            "CRITICAL"
                        )
                
                time.sleep(60)  # Her dakika kontrol et
                
            except Exception as e:
                self.logger.error(f"Sistem izleme hatası: {e}")
                time.sleep(30)
    
    def start_all_services(self, web_host: str = "0.0.0.0", web_port: int = 8080) -> bool:
        """Tüm servisleri başlat"""
        try:
            self.logger.info("=== FiveM DDoS Koruma Sistemi Başlatılıyor ===")
            
            # Gereksinimleri kontrol et
            if not self.check_requirements():
                return False
            
            # Ana DDoS koruma sistemi
            if not self.start_ddos_protection():
                return False
            
            # Firewall koruması
            self.start_firewall_protection()  # Hata olsa bile devam et
            
            # Uyarı sistemi
            self.start_alert_system()  # Hata olsa bile devam et
            
            # Web arayüzü
            self.start_web_interface(web_host, web_port)  # Hata olsa bile devam et
            
            self.running = True
            
            # Sistem durumu mesajı
            self.logger.info("=== FiveM DDoS Koruma Sistemi Aktif ===")
            self.logger.info(f"Web Arayüzü: http://{web_host}:{web_port}")
            self.logger.info("Sistem tüm DDoS saldırılarına karşı korunuyor!")
            
            # Sistem sağlık izleme
            health_thread = threading.Thread(target=self.monitor_system_health, daemon=True)
            health_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Sistem başlatma hatası: {e}")
            return False
    
    def stop_all_services(self):
        """Tüm servisleri durdur"""
        try:
            self.logger.info("Servisler durduruluyor...")
            self.running = False
            
            # DDoS sistemi
            if self.ddos_system:
                self.ddos_system.stop_monitoring()
                self.logger.info("DDoS koruma sistemi durduruldu")
            
            # Gelişmiş firewall
            if self.advanced_firewall:
                self.advanced_firewall.disable_adaptive_protection()
                self.logger.info("Gelişmiş firewall koruması durduruldu")
            
            # Firewall temizliği
            if self.firewall_manager:
                self.firewall_manager.cleanup_rules()
                self.logger.info("Firewall kuralları temizlendi")
            
            # Uyarı sistemi
            if self.alert_system:
                # Son uyarı gönder
                self.alert_system.send_system_alert(
                    "DDoS Koruma Sistemi Durduruldu",
                    "FiveM DDoS koruma sistemi kapatıldı.",
                    "WARNING"
                )
                self.alert_system.stop_alert_worker()
                self.logger.info("Uyarı sistemi durduruldu")
            
            self.logger.info("Tüm servisler başarıyla durduruldu")
            
        except Exception as e:
            self.logger.error(f"Servis durdurma hatası: {e}")
    
    def run_interactive_mode(self):
        """Interaktif mod - kullanıcı komutları"""
        print("\n=== FiveM DDoS Koruma Sistemi - Interaktif Mod ===")
        print("Komutlar:")
        print("  stats  - Sistem istatistikleri")
        print("  block <ip> - IP'yi manuel engelle")
        print("  unblock <ip> - IP engeli kaldır")
        print("  status - Sistem durumu")
        print("  quit   - Çıkış")
        print("================================================\n")
        
        while self.running and not self.shutdown_requested:
            try:
                command = input("DDoS-Protection> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "stats":
                    if self.ddos_system:
                        stats = self.ddos_system.get_statistics()
                        print("\n=== Sistem İstatistikleri ===")
                        for key, value in stats.items():
                            print(f"{key}: {value}")
                        print()
                elif cmd == "block" and len(command) > 1:
                    ip = command[1]
                    if self.ddos_system:
                        self.ddos_system.add_to_blacklist(ip, "Manuel engelleme")
                        print(f"IP {ip} engellendi.")
                elif cmd == "unblock" and len(command) > 1:
                    ip = command[1]
                    if self.ddos_system:
                        self.ddos_system.remove_from_blacklist(ip)
                        print(f"IP {ip} engeli kaldırıldı.")
                elif cmd == "status":
                    print(f"\nSistem Durumu:")
                    print(f"  DDoS Koruması: {'Aktif' if self.ddos_system and self.ddos_system.running else 'Pasif'}")
                    print(f"  Firewall: {'Aktif' if self.firewall_manager else 'Pasif'}")
                    print(f"  Uyarı Sistemi: {'Aktif' if self.alert_system else 'Pasif'}")
                    print(f"  Web Arayüzü: {'Aktif' if self.web_app_thread else 'Pasif'}")
                else:
                    print("Bilinmeyen komut. 'quit' yazarak çıkabilirsiniz.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Komut hatası: {e}")

def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description='FiveM DDoS Protection System')
    parser.add_argument('--config', default='ddos_config.ini', help='Konfigürasyon dosyası')
    parser.add_argument('--host', default='0.0.0.0', help='Web arayüzü host')
    parser.add_argument('--port', type=int, default=8080, help='Web arayüzü port')
    parser.add_argument('--no-interactive', action='store_true', help='Interaktif modu devre dışı bırak')
    parser.add_argument('--daemon', action='store_true', help='Daemon modunda çalıştır')
    
    args = parser.parse_args()
    
    # Protection manager'ı başlat
    protection_manager = FiveMDDoSProtectionManager(args.config)
    
    # Tüm servisleri başlat
    if not protection_manager.start_all_services(args.host, args.port):
        print("Sistem başlatılamadı!")
        return 1
    
    try:
        if args.daemon:
            # Daemon modunda sürekli çalış
            while protection_manager.running and not protection_manager.shutdown_requested:
                time.sleep(1)
        elif not args.no_interactive:
            # Interaktif mod
            protection_manager.run_interactive_mode()
        else:
            # Basit bekleme modu
            print("Sistemi durdurmak için Ctrl+C'ye basın...")
            while protection_manager.running and not protection_manager.shutdown_requested:
                time.sleep(1)
                
    except KeyboardInterrupt:
        pass
    finally:
        protection_manager.stop_all_services()
    
    return 0

if __name__ == "__main__":
    exit(main()) 