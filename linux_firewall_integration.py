#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Firewall Integration
FiveM DDoS koruma sistemi için Linux firewall entegrasyonu
iptables, ufw, firewall-cmd desteği
"""

import subprocess
import logging
import time
import threading
import os
import sys
import platform
from typing import List, Set, Optional, Tuple, Dict
import ipaddress

class LinuxFirewallManager:
    """Linux Firewall yönetici sınıfı"""
    
    def __init__(self, rule_prefix: str = "FiveM_DDoS_"):
        self.rule_prefix = rule_prefix
        self.logger = logging.getLogger('LinuxFirewallManager')
        self.blocked_ips = set()
        self.active_rules = set()
        self.firewall_type = self._detect_firewall_type()
        
        # Root yetkisi kontrolü
        if not self._is_root():
            self.logger.warning("Firewall yönetimi için root/sudo yetkisi gerekiyor!")
    
    def _is_root(self) -> bool:
        """Root yetkisi olup olmadığını kontrol et"""
        return os.getuid() == 0
    
    def _detect_firewall_type(self) -> str:
        """Sistem firewall türünü tespit et"""
        # UFW (Ubuntu/Debian)
        if self._command_exists('ufw'):
            return 'ufw'
        # firewall-cmd (CentOS/RHEL/Fedora)
        elif self._command_exists('firewall-cmd'):
            return 'firewall-cmd'
        # iptables (Tüm Linux)
        elif self._command_exists('iptables'):
            return 'iptables'
        else:
            self.logger.warning("Desteklenen firewall bulunamadı!")
            return 'none'
    
    def _command_exists(self, command: str) -> bool:
        """Komutun sistemde mevcut olup olmadığını kontrol et"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _run_command(self, command: str, use_sudo: bool = True) -> Tuple[bool, str]:
        """Komut çalıştır ve sonucu döndür"""
        try:
            # Root değilse sudo kullan
            if use_sudo and not self._is_root():
                command = f"sudo {command}"
            
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
    
    def block_ip_ufw(self, ip: str, reason: str = "") -> bool:
        """UFW ile IP engelle"""
        try:
            cmd = f"ufw deny from {ip}"
            success, msg = self._run_command(cmd)
            
            if success:
                self.blocked_ips.add(ip)
                self.active_rules.add(f"ufw_deny_{ip}")
                self.logger.info(f"UFW ile IP {ip} engellendi. Sebep: {reason}")
                return True
            else:
                self.logger.error(f"UFW ile IP {ip} engellenemedi: {msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"UFW IP engelleme hatası: {e}")
            return False
    
    def unblock_ip_ufw(self, ip: str) -> bool:
        """UFW ile IP engeli kaldır"""
        try:
            cmd = f"ufw delete deny from {ip}"
            success, msg = self._run_command(cmd)
            
            if success:
                self.blocked_ips.discard(ip)
                self.active_rules.discard(f"ufw_deny_{ip}")
                self.logger.info(f"UFW ile IP {ip} engeli kaldırıldı")
                return True
            else:
                self.logger.warning(f"UFW ile IP {ip} engeli kaldırılamadı: {msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"UFW IP engel kaldırma hatası: {e}")
            return False
    
    def block_ip_firewall_cmd(self, ip: str, reason: str = "") -> bool:
        """firewall-cmd ile IP engelle"""
        try:
            # Rich rule ile engelleme
            cmd = f'firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address={ip} reject"'
            success, msg = self._run_command(cmd)
            
            if success:
                # Kuralı hemen aktif et
                reload_cmd = "firewall-cmd --reload"
                self._run_command(reload_cmd)
                
                self.blocked_ips.add(ip)
                self.active_rules.add(f"firewall_cmd_rich_{ip}")
                self.logger.info(f"firewall-cmd ile IP {ip} engellendi. Sebep: {reason}")
                return True
            else:
                self.logger.error(f"firewall-cmd ile IP {ip} engellenemedi: {msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"firewall-cmd IP engelleme hatası: {e}")
            return False
    
    def unblock_ip_firewall_cmd(self, ip: str) -> bool:
        """firewall-cmd ile IP engeli kaldır"""
        try:
            cmd = f'firewall-cmd --permanent --remove-rich-rule="rule family=ipv4 source address={ip} reject"'
            success, msg = self._run_command(cmd)
            
            if success:
                # Kuralı hemen aktif et
                reload_cmd = "firewall-cmd --reload"
                self._run_command(reload_cmd)
                
                self.blocked_ips.discard(ip)
                self.active_rules.discard(f"firewall_cmd_rich_{ip}")
                self.logger.info(f"firewall-cmd ile IP {ip} engeli kaldırıldı")
                return True
            else:
                self.logger.warning(f"firewall-cmd ile IP {ip} engeli kaldırılamadı: {msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"firewall-cmd IP engel kaldırma hatası: {e}")
            return False
    
    def block_ip_iptables(self, ip: str, reason: str = "") -> bool:
        """iptables ile IP engelle"""
        try:
            # INPUT ve FORWARD zincirlerine kural ekle
            commands = [
                f"iptables -I INPUT -s {ip} -j DROP",
                f"iptables -I FORWARD -s {ip} -j DROP"
            ]
            
            success_count = 0
            for cmd in commands:
                success, msg = self._run_command(cmd)
                if success:
                    success_count += 1
                else:
                    self.logger.warning(f"iptables komutu başarısız: {cmd} - {msg}")
            
            if success_count > 0:
                self.blocked_ips.add(ip)
                self.active_rules.add(f"iptables_drop_{ip}")
                self.logger.info(f"iptables ile IP {ip} engellendi. Sebep: {reason}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"iptables IP engelleme hatası: {e}")
            return False
    
    def unblock_ip_iptables(self, ip: str) -> bool:
        """iptables ile IP engeli kaldır"""
        try:
            commands = [
                f"iptables -D INPUT -s {ip} -j DROP",
                f"iptables -D FORWARD -s {ip} -j DROP"
            ]
            
            success_count = 0
            for cmd in commands:
                success, msg = self._run_command(cmd)
                if success:
                    success_count += 1
            
            self.blocked_ips.discard(ip)
            self.active_rules.discard(f"iptables_drop_{ip}")
            self.logger.info(f"iptables ile IP {ip} engeli kaldırıldı")
            return True
                
        except Exception as e:
            self.logger.error(f"iptables IP engel kaldırma hatası: {e}")
            return False
    
    def block_ip(self, ip: str, reason: str = "") -> bool:
        """IP adresini firewall ile engelle (otomatik firewall seçimi)"""
        try:
            # IP format kontrolü
            ipaddress.ip_address(ip)
            
            if ip in self.blocked_ips:
                self.logger.debug(f"IP {ip} zaten engellendi")
                return True
            
            # Firewall türüne göre engelleme
            if self.firewall_type == 'ufw':
                return self.block_ip_ufw(ip, reason)
            elif self.firewall_type == 'firewall-cmd':
                return self.block_ip_firewall_cmd(ip, reason)
            elif self.firewall_type == 'iptables':
                return self.block_ip_iptables(ip, reason)
            else:
                self.logger.error("Desteklenen firewall bulunamadı!")
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
            
            # Firewall türüne göre engel kaldırma
            if self.firewall_type == 'ufw':
                return self.unblock_ip_ufw(ip)
            elif self.firewall_type == 'firewall-cmd':
                return self.unblock_ip_firewall_cmd(ip)
            elif self.firewall_type == 'iptables':
                return self.unblock_ip_iptables(ip)
            else:
                self.logger.error("Desteklenen firewall bulunamadı!")
                return False
                
        except Exception as e:
            self.logger.error(f"IP engel kaldırma hatası: {e}")
            return False
    
    def allow_fivem_traffic(self, fivem_port: int = 30120, txadmin_port: int = 40120) -> bool:
        """FiveM trafiğine izin ver"""
        try:
            success = False
            
            if self.firewall_type == 'ufw':
                commands = [
                    f"ufw allow {fivem_port}/tcp",
                    f"ufw allow {fivem_port}/udp",
                    f"ufw allow {txadmin_port}/tcp"
                ]
                
                success_count = 0
                for cmd in commands:
                    if self._run_command(cmd)[0]:
                        success_count += 1
                
                success = success_count == len(commands)
                
            elif self.firewall_type == 'firewall-cmd':
                commands = [
                    f"firewall-cmd --permanent --add-port={fivem_port}/tcp",
                    f"firewall-cmd --permanent --add-port={fivem_port}/udp",
                    f"firewall-cmd --permanent --add-port={txadmin_port}/tcp",
                    "firewall-cmd --reload"
                ]
                
                success_count = 0
                for cmd in commands:
                    if self._run_command(cmd)[0]:
                        success_count += 1
                
                success = success_count == len(commands)
                
            elif self.firewall_type == 'iptables':
                commands = [
                    f"iptables -I INPUT -p tcp --dport {fivem_port} -j ACCEPT",
                    f"iptables -I INPUT -p udp --dport {fivem_port} -j ACCEPT",
                    f"iptables -I INPUT -p tcp --dport {txadmin_port} -j ACCEPT"
                ]
                
                success_count = 0
                for cmd in commands:
                    if self._run_command(cmd)[0]:
                        success_count += 1
                
                success = success_count == len(commands)
            
            if success:
                self.logger.info("FiveM trafik kuralları başarıyla eklendi")
            else:
                self.logger.warning("FiveM trafik kuralları kısmen eklendi")
            
            return success
            
        except Exception as e:
            self.logger.error(f"FiveM trafik izni hatası: {e}")
            return False
    
    def enable_ddos_protection_profile(self) -> bool:
        """Linux'ta DDoS koruma profilini etkinleştir"""
        try:
            success_count = 0
            total_commands = 0
            
            # Kernel parametreleri (sysctl)
            sysctl_commands = [
                # SYN flood koruması
                "sysctl -w net.ipv4.tcp_syncookies=1",
                "sysctl -w net.ipv4.tcp_max_syn_backlog=2048",
                "sysctl -w net.ipv4.tcp_synack_retries=2",
                "sysctl -w net.ipv4.tcp_syn_retries=5",
                
                # Rate limiting
                "sysctl -w net.ipv4.icmp_ratelimit=1000",
                "sysctl -w net.ipv4.icmp_ratemask=0x1818",
                
                # Network buffer boyutları
                "sysctl -w net.core.rmem_default=262144",
                "sysctl -w net.core.rmem_max=16777216",
                "sysctl -w net.core.wmem_default=262144",
                "sysctl -w net.core.wmem_max=16777216",
                
                # Connection tracking
                "sysctl -w net.netfilter.nf_conntrack_max=65536",
                "sysctl -w net.ipv4.ip_local_port_range='1024 65535'"
            ]
            
            for cmd in sysctl_commands:
                total_commands += 1
                success, msg = self._run_command(cmd)
                if success:
                    success_count += 1
                else:
                    self.logger.debug(f"Sysctl komutu başarısız: {cmd}")
            
            # Firewall kuralları
            if self.firewall_type == 'iptables':
                firewall_commands = [
                    # ICMP flood koruması
                    "iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT",
                    "iptables -A INPUT -p icmp --icmp-type echo-request -j DROP",
                    
                    # SYN flood koruması
                    "iptables -A INPUT -p tcp --syn -m limit --limit 1/s -j ACCEPT",
                    "iptables -A INPUT -p tcp --syn -j DROP",
                    
                    # Invalid paket engelleme
                    "iptables -A INPUT -m state --state INVALID -j DROP"
                ]
                
                for cmd in firewall_commands:
                    total_commands += 1
                    success, msg = self._run_command(cmd)
                    if success:
                        success_count += 1
            
            self.logger.info(f"DDoS koruma profili: {success_count}/{total_commands} kural aktif")
            return success_count > total_commands * 0.5  # %50'den fazlası başarılı olmalı
            
        except Exception as e:
            self.logger.error(f"DDoS koruma profili hatası: {e}")
            return False
    
    def cleanup_rules(self) -> bool:
        """Oluşturulan kuralları temizle"""
        try:
            deleted_count = 0
            
            # Engellenen IP'leri temizle
            for ip in self.blocked_ips.copy():
                if self.unblock_ip(ip):
                    deleted_count += 1
            
            self.blocked_ips.clear()
            self.active_rules.clear()
            
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
    
    def get_firewall_status(self) -> Dict:
        """Firewall durumunu döndür"""
        try:
            status = {
                'firewall_type': self.firewall_type,
                'is_root': self._is_root(),
                'blocked_ips_count': len(self.blocked_ips),
                'active_rules_count': len(self.active_rules),
                'system_info': {
                    'os': platform.system(),
                    'distribution': platform.platform(),
                    'kernel': platform.release()
                }
            }
            
            # Firewall servis durumu
            if self.firewall_type == 'ufw':
                success, output = self._run_command("ufw status", use_sudo=False)
                status['service_status'] = 'active' if 'Status: active' in output else 'inactive'
            elif self.firewall_type == 'firewall-cmd':
                success, output = self._run_command("firewall-cmd --state", use_sudo=False)
                status['service_status'] = 'active' if success and 'running' in output else 'inactive'
            else:
                status['service_status'] = 'unknown'
            
            return status
            
        except Exception as e:
            self.logger.error(f"Firewall durum kontrolü hatası: {e}")
            return {}
    
    def monitor_connections(self, port: int = 30120) -> Dict:
        """Ağ bağlantılarını izle"""
        try:
            # ss komutu ile bağlantıları listele
            cmd = f"ss -tuln | grep :{port}"
            success, output = self._run_command(cmd, use_sudo=False)
            
            if not success:
                return {}
            
            connections = []
            lines = output.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        protocol = parts[0]
                        state = parts[1] if len(parts) > 1 else "UNKNOWN"
                        local_addr = parts[3] if len(parts) > 3 else "UNKNOWN"
                        
                        connections.append({
                            'protocol': protocol,
                            'state': state,
                            'local': local_addr
                        })
            
            connection_stats = {
                'total_connections': len(connections),
                'tcp_connections': len([c for c in connections if 'tcp' in c['protocol'].lower()]),
                'udp_connections': len([c for c in connections if 'udp' in c['protocol'].lower()]),
                'connections': connections
            }
            
            return connection_stats
            
        except Exception as e:
            self.logger.error(f"Bağlantı izleme hatası: {e}")
            return {}

# Test ve örnek kullanım
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fw_manager = LinuxFirewallManager()
    
    print("Linux Firewall DDoS Koruma Sistemi Test Ediliyor...")
    print(f"Tespit edilen firewall türü: {fw_manager.firewall_type}")
    
    # Firewall durumu
    status = fw_manager.get_firewall_status()
    print(f"Firewall durumu: {status}")
    
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