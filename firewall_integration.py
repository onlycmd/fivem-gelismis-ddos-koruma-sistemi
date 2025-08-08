#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Firewall Integration
FiveM DDoS koruma sistemi için Windows Firewall entegrasyonu
"""

import subprocess
import logging
import time
import threading
from typing import List, Set, Optional, Tuple, Dict
import socket
import ipaddress
import os
import sys

class WindowsFirewallManager:
    """Windows Firewall yönetici sınıfı"""
    
    def __init__(self, rule_prefix: str = "FiveM_DDoS_"):
        self.rule_prefix = rule_prefix
        self.logger = logging.getLogger('FirewallManager')
        self.blocked_ips = set()
        self.active_rules = set()
        
        # Admin yetkisi kontrolü
        if not self._is_admin():
            self.logger.warning("Firewall yönetimi için admin yetkisi gerekiyor!")
    
    def _is_admin(self) -> bool:
        """Admin yetkisi olup olmadığını kontrol et"""
        try:
            return os.getuid() == 0
        except AttributeError:
            # Windows
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
    
    def _run_command(self, command: str) -> Tuple[bool, str]:
        """Komut çalıştır ve sonucu döndür"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                self.logger.error(f"Komut hatası: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Komut zaman aşımı: {command}")
            return False, "Timeout"
        except Exception as e:
            self.logger.error(f"Komut çalıştırma hatası: {e}")
            return False, str(e)
    
    def block_ip(self, ip: str, reason: str = "") -> bool:
        """IP adresini Windows Firewall ile engelle"""
        try:
            # IP format kontrolü
            ipaddress.ip_address(ip)
            
            if ip in self.blocked_ips:
                self.logger.debug(f"IP {ip} zaten engellendi")
                return True
            
            rule_name = f"{self.rule_prefix}Block_{ip.replace('.', '_')}"
            
            # Inbound rule
            inbound_cmd = f'''netsh advfirewall firewall add rule name="{rule_name}_IN" dir=in action=block remoteip={ip} protocol=any'''
            
            # Outbound rule
            outbound_cmd = f'''netsh advfirewall firewall add rule name="{rule_name}_OUT" dir=out action=block remoteip={ip} protocol=any'''
            
            # Kuralları ekle
            success_in, msg_in = self._run_command(inbound_cmd)
            success_out, msg_out = self._run_command(outbound_cmd)
            
            if success_in and success_out:
                self.blocked_ips.add(ip)
                self.active_rules.add(f"{rule_name}_IN")
                self.active_rules.add(f"{rule_name}_OUT")
                self.logger.info(f"IP {ip} başarıyla engellendi. Sebep: {reason}")
                return True
            else:
                self.logger.error(f"IP {ip} engellenemedi. IN: {msg_in}, OUT: {msg_out}")
                return False
                
        except ValueError:
            self.logger.error(f"Geçersiz IP adresi: {ip}")
            return False
        except Exception as e:
            self.logger.error(f"IP engelleme hatası: {e}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """IP adresinin engelini kaldır"""
        try:
            if ip not in self.blocked_ips:
                self.logger.debug(f"IP {ip} zaten engellenmemiş")
                return True
            
            rule_name = f"{self.rule_prefix}Block_{ip.replace('.', '_')}"
            
            # Kuralları sil
            inbound_cmd = f'''netsh advfirewall firewall delete rule name="{rule_name}_IN"'''
            outbound_cmd = f'''netsh advfirewall firewall delete rule name="{rule_name}_OUT"'''
            
            success_in, msg_in = self._run_command(inbound_cmd)
            success_out, msg_out = self._run_command(outbound_cmd)
            
            if success_in and success_out:
                self.blocked_ips.discard(ip)
                self.active_rules.discard(f"{rule_name}_IN")
                self.active_rules.discard(f"{rule_name}_OUT")
                self.logger.info(f"IP {ip} engeli kaldırıldı")
                return True
            else:
                self.logger.warning(f"IP {ip} engeli kaldırılırken hata. IN: {msg_in}, OUT: {msg_out}")
                return False
                
        except Exception as e:
            self.logger.error(f"IP engel kaldırma hatası: {e}")
            return False
    
    def block_port_range(self, start_port: int, end_port: int, protocol: str = "TCP") -> bool:
        """Port aralığını engelle"""
        try:
            rule_name = f"{self.rule_prefix}Block_Ports_{start_port}_{end_port}_{protocol}"
            
            cmd = f'''netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block protocol={protocol} localport={start_port}-{end_port}'''
            
            success, msg = self._run_command(cmd)
            
            if success:
                self.active_rules.add(rule_name)
                self.logger.info(f"Port aralığı {start_port}-{end_port} ({protocol}) engellendi")
                return True
            else:
                self.logger.error(f"Port aralığı engellenemedi: {msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Port engelleme hatası: {e}")
            return False
    
    def allow_fivem_traffic(self, fivem_port: int = 30120, txadmin_port: int = 40120) -> bool:
        """FiveM trafiğine izin ver"""
        try:
            rules = [
                f'''netsh advfirewall firewall add rule name="{self.rule_prefix}Allow_FiveM_TCP" dir=in action=allow protocol=TCP localport={fivem_port}''',
                f'''netsh advfirewall firewall add rule name="{self.rule_prefix}Allow_FiveM_UDP" dir=in action=allow protocol=UDP localport={fivem_port}''',
                f'''netsh advfirewall firewall add rule name="{self.rule_prefix}Allow_TxAdmin" dir=in action=allow protocol=TCP localport={txadmin_port}'''
            ]
            
            success_count = 0
            for cmd in rules:
                success, msg = self._run_command(cmd)
                if success:
                    success_count += 1
                else:
                    self.logger.warning(f"FiveM kural eklenemedi: {msg}")
            
            if success_count == len(rules):
                self.logger.info("FiveM trafik kuralları başarıyla eklendi")
                return True
            else:
                self.logger.warning(f"FiveM kurallarından sadece {success_count}/{len(rules)} eklenebildi")
                return False
                
        except Exception as e:
            self.logger.error(f"FiveM trafik izni hatası: {e}")
            return False
    
    def block_suspicious_countries(self, country_codes: List[str]) -> bool:
        """Şüpheli ülkelerden gelen trafiği engelle (GeoIP ile)"""
        try:
            # Bu özellik için gelişmiş IP listelerine ihtiyaç var
            # Şimdilik temel implementasyon
            self.logger.info(f"Ülke bazlı engelleme: {country_codes}")
            
            # Bilinen kötü IP aralıkları (örnek)
            suspicious_ranges = [
                "185.220.100.0/22",  # Tor relay
                "198.98.50.0/24",    # Known botnet
                "45.95.168.0/22"     # Suspicious range
            ]
            
            success_count = 0
            for ip_range in suspicious_ranges:
                rule_name = f"{self.rule_prefix}Block_Range_{ip_range.replace('/', '_').replace('.', '_')}"
                cmd = f'''netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip_range}'''
                
                success, msg = self._run_command(cmd)
                if success:
                    self.active_rules.add(rule_name)
                    success_count += 1
                else:
                    self.logger.warning(f"IP aralığı engellenemedi: {msg}")
            
            self.logger.info(f"Şüpheli IP aralıklarından {success_count} tanesi engellendi")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Ülke bazlı engelleme hatası: {e}")
            return False
    
    def enable_ddos_protection_profile(self) -> bool:
        """Windows Firewall'da DDoS koruma profilini etkinleştir"""
        try:
            commands = [
                # SYN flood koruması
                "netsh int tcp set global autotuninglevel=normal",
                "netsh int tcp set global chimney=enabled",
                "netsh int tcp set global rss=enabled",
                "netsh int tcp set global netdma=enabled",
                
                # Rate limiting
                "netsh advfirewall set currentprofile settings remotemanagement disable",
                "netsh advfirewall set currentprofile settings unicastresponsetomulticast disable",
                
                # ICMP flood koruması
                '''netsh advfirewall firewall add rule name="''' + self.rule_prefix + '''Block_ICMP_Flood" dir=in action=block protocol=icmpv4:8,any'''
            ]
            
            success_count = 0
            for cmd in commands:
                success, msg = self._run_command(cmd)
                if success:
                    success_count += 1
                else:
                    self.logger.warning(f"DDoS koruma komutu başarısız: {msg}")
            
            self.logger.info(f"DDoS koruma profili: {success_count}/{len(commands)} kural aktif")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"DDoS koruma profili hatası: {e}")
            return False
    
    def cleanup_rules(self) -> bool:
        """Oluşturulan kuralları temizle"""
        try:
            # Mevcut kuralları listele
            list_cmd = f'''netsh advfirewall firewall show rule name=all | findstr "{self.rule_prefix}"'''
            success, output = self._run_command(list_cmd)
            
            if not success:
                self.logger.info("Temizlenecek kural bulunamadı")
                return True
            
            # Kuralları sil
            delete_cmd = f'''netsh advfirewall firewall delete rule name=all dir=in remoteip=any | findstr "{self.rule_prefix}"'''
            
            # Tek tek silme (daha güvenli)
            deleted_count = 0
            for rule_name in self.active_rules.copy():
                cmd = f'''netsh advfirewall firewall delete rule name="{rule_name}"'''
                success, msg = self._run_command(cmd)
                if success:
                    self.active_rules.discard(rule_name)
                    deleted_count += 1
            
            self.blocked_ips.clear()
            self.logger.info(f"{deleted_count} adet firewall kuralı temizlendi")
            return True
            
        except Exception as e:
            self.logger.error(f"Kural temizleme hatası: {e}")
            return False
    
    def get_blocked_ips_count(self) -> int:
        """Engellenen IP sayısını döndür"""
        return len(self.blocked_ips)
    
    def get_active_rules_count(self) -> int:
        """Aktif kural sayısını döndür"""
        return len(self.active_rules)
    
    def monitor_connections(self, callback_func=None) -> Dict:
        """Ağ bağlantılarını izle"""
        try:
            # Netstat ile aktif bağlantıları listele
            cmd = "netstat -an | findstr :30120"
            success, output = self._run_command(cmd)
            
            if not success:
                return {}
            
            connections = []
            lines = output.strip().split('\n')
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    protocol = parts[0]
                    local_addr = parts[1]
                    foreign_addr = parts[2]
                    state = parts[3] if len(parts) > 3 else "UNKNOWN"
                    
                    connections.append({
                        'protocol': protocol,
                        'local': local_addr,
                        'foreign': foreign_addr,
                        'state': state
                    })
            
            connection_stats = {
                'total_connections': len(connections),
                'tcp_connections': len([c for c in connections if c['protocol'] == 'TCP']),
                'udp_connections': len([c for c in connections if c['protocol'] == 'UDP']),
                'connections': connections
            }
            
            if callback_func:
                callback_func(connection_stats)
            
            return connection_stats
            
        except Exception as e:
            self.logger.error(f"Bağlantı izleme hatası: {e}")
            return {}

class AdvancedFirewallProtection:
    """Gelişmiş firewall koruma özellikleri"""
    
    def __init__(self, firewall_manager: WindowsFirewallManager):
        self.fw_manager = firewall_manager
        self.logger = logging.getLogger('AdvancedFirewall')
        self.protection_active = False
        self.monitoring_thread = None
    
    def enable_adaptive_protection(self, ddos_system) -> bool:
        """Adaptif koruma sistemini etkinleştir"""
        try:
            self.protection_active = True
            
            def adaptive_monitor():
                while self.protection_active:
                    try:
                        stats = ddos_system.get_statistics()
                        
                        # Yüksek saldırı aktivitesi tespit edilirse
                        if stats.get('attack_attempts', 0) > 100:
                            self.logger.warning("Yoğun saldırı tespit edildi - Firewall kuralları sıkılaştırılıyor")
                            self._tighten_security()
                        
                        # Normal seviyeye dönerse kuralları gevşet
                        elif stats.get('attack_attempts', 0) < 10:
                            self._relax_security()
                        
                        time.sleep(30)  # 30 saniyede bir kontrol
                        
                    except Exception as e:
                        self.logger.error(f"Adaptif koruma hatası: {e}")
                        time.sleep(60)
            
            self.monitoring_thread = threading.Thread(target=adaptive_monitor, daemon=True)
            self.monitoring_thread.start()
            
            self.logger.info("Adaptif firewall koruması etkinleştirildi")
            return True
            
        except Exception as e:
            self.logger.error(f"Adaptif koruma başlatma hatası: {e}")
            return False
    
    def _tighten_security(self):
        """Güvenlik seviyesini artır"""
        try:
            # ICMP'yi tamamen engelle
            cmd = f'''netsh advfirewall firewall add rule name="{self.fw_manager.rule_prefix}Emergency_Block_ICMP" dir=in action=block protocol=icmpv4'''
            self.fw_manager._run_command(cmd)
            
            # Belirli portları geçici olarak kısıtla
            suspicious_ports = [22, 23, 135, 139, 445, 1433, 3389]
            for port in suspicious_ports:
                cmd = f'''netsh advfirewall firewall add rule name="{self.fw_manager.rule_prefix}Emergency_Block_Port_{port}" dir=in action=block protocol=TCP localport={port}'''
                self.fw_manager._run_command(cmd)
            
            self.logger.info("Güvenlik seviyesi artırıldı")
            
        except Exception as e:
            self.logger.error(f"Güvenlik sıkılaştırma hatası: {e}")
    
    def _relax_security(self):
        """Güvenlik seviyesini normale döndür"""
        try:
            # Acil durum kurallarını kaldır
            emergency_rules = [
                f"{self.fw_manager.rule_prefix}Emergency_Block_ICMP"
            ]
            
            for rule in emergency_rules:
                cmd = f'''netsh advfirewall firewall delete rule name="{rule}"'''
                self.fw_manager._run_command(cmd)
            
            self.logger.info("Güvenlik seviyesi normale döndürüldü")
            
        except Exception as e:
            self.logger.error(f"Güvenlik gevşetme hatası: {e}")
    
    def disable_adaptive_protection(self):
        """Adaptif korumayı devre dışı bırak"""
        self.protection_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Adaptif firewall koruması devre dışı bırakıldı")

# Test ve örnek kullanım
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fw_manager = WindowsFirewallManager()
    
    print("Windows Firewall DDoS Koruma Sistemi Test Ediliyor...")
    
    # Test IP'leri
    test_ips = ["192.168.1.100", "10.0.0.50"]
    
    # IP engelleme testi
    for ip in test_ips:
        success = fw_manager.block_ip(ip, "Test engelleme")
        print(f"IP {ip} engelleme: {'Başarılı' if success else 'Başarısız'}")
    
    # FiveM trafik izni
    fw_manager.allow_fivem_traffic()
    
    # DDoS koruma profili
    fw_manager.enable_ddos_protection_profile()
    
    # İstatistikleri göster
    print(f"\nEngellenen IP sayısı: {fw_manager.get_blocked_ips_count()}")
    print(f"Aktif kural sayısı: {fw_manager.get_active_rules_count()}")
    
    # Bağlantıları izle
    connections = fw_manager.monitor_connections()
    print(f"Toplam bağlantı: {connections.get('total_connections', 0)}")
    
    input("\nTemizlemek için Enter'a basın...")
    
    # Temizlik
    fw_manager.cleanup_rules()
    print("Firewall kuralları temizlendi.") 