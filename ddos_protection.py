#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FiveM DDoS Protection System
Yüksek Güvenlikli DDoS Koruma Sistemi
Geliştirici: AI Assistant
Versiyon: 1.0
"""

import asyncio
import logging
import time
import json
import sqlite3
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import ipaddress
import requests
import socket
import psutil
import hashlib
from typing import Dict, List, Set, Tuple, Optional
import configparser
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import geoip2.database
import os
import sys

class DDoSProtectionSystem:
    """FiveM için gelişmiş DDoS koruma sistemi"""
    
    def __init__(self, config_file: str = "ddos_config.ini"):
        self.config = self._load_config(config_file)
        self.setup_logging()
        self.setup_database()
        
        # Koruma parametreleri
        self.ip_connections = defaultdict(int)
        self.ip_request_times = defaultdict(deque)
        self.blocked_ips = set()
        self.whitelisted_ips = set()
        self.blacklisted_ips = set()
        self.suspicious_patterns = {}
        
        # İstatistikler
        self.total_requests = 0
        self.blocked_requests = 0
        self.attack_attempts = 0
        
        # Threadsafe locks
        self.ip_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Sistem durumu
        self.running = False
        self.last_cleanup = time.time()
        
        # GeoIP veritabanı
        self.geoip_reader = None
        self._load_geoip_db()
        
        self.logger.info("DDoS Koruma Sistemi başlatıldı")
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """Konfigürasyon dosyasını yükle"""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Varsayılan değerler
        if not config.has_section('PROTECTION'):
            config.add_section('PROTECTION')
            config.set('PROTECTION', 'max_requests_per_minute', '60')
            config.set('PROTECTION', 'max_connections_per_ip', '10')
            config.set('PROTECTION', 'ban_duration_minutes', '30')
            config.set('PROTECTION', 'whitelist_file', 'whitelist.txt')
            config.set('PROTECTION', 'blacklist_file', 'blacklist.txt')
            
        if not config.has_section('DETECTION'):
            config.add_section('DETECTION')
            config.set('DETECTION', 'suspicious_threshold', '100')
            config.set('DETECTION', 'packet_size_threshold', '65536')
            config.set('DETECTION', 'enable_pattern_detection', 'true')
            
        if not config.has_section('GEOGRAPHIC'):
            config.add_section('GEOGRAPHIC')
            config.set('GEOGRAPHIC', 'allowed_countries', 'TR,US,EU')
            config.set('GEOGRAPHIC', 'enable_geo_blocking', 'false')
            
        return config
    
    def setup_logging(self):
        """Loglama sistemini kur"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('ddos_protection.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('DDoSProtection')
    
    def setup_database(self):
        """SQLite veritabanını kur"""
        self.db_conn = sqlite3.connect('ddos_protection.db', check_same_thread=False)
        self.db_lock = threading.Lock()
        
        cursor = self.db_conn.cursor()
        
        # Saldırı kayıtları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                ip_address TEXT,
                attack_type TEXT,
                severity INTEGER,
                packets_count INTEGER,
                blocked BOOLEAN,
                country TEXT,
                additional_info TEXT
            )
        ''')
        
        # IP istatistikleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_statistics (
                ip_address TEXT PRIMARY KEY,
                total_requests INTEGER,
                blocked_requests INTEGER,
                last_seen DATETIME,
                risk_score INTEGER,
                is_banned BOOLEAN,
                ban_expires DATETIME
            )
        ''')
        
        # Sistem istatistikleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                total_requests INTEGER,
                blocked_requests INTEGER,
                active_connections INTEGER,
                cpu_usage REAL,
                memory_usage REAL,
                network_in REAL,
                network_out REAL
            )
        ''')
        
        self.db_conn.commit()
        self.logger.info("Veritabanı başarıyla kuruldu")
    
    def _load_geoip_db(self):
        """GeoIP veritabanını yükle"""
        try:
            if os.path.exists('GeoLite2-Country.mmdb'):
                self.geoip_reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
                self.logger.info("GeoIP veritabanı yüklendi")
            else:
                self.logger.warning("GeoIP veritabanı bulunamadı. Coğrafi filtreleme devre dışı.")
        except Exception as e:
            self.logger.error(f"GeoIP veritabanı yüklenemedi: {e}")
    
    def get_country_code(self, ip: str) -> Optional[str]:
        """IP adresinin ülke kodunu döndür"""
        if not self.geoip_reader:
            return None
        
        try:
            response = self.geoip_reader.country(ip)
            return response.country.iso_code
        except Exception:
            return None
    
    def is_ip_whitelisted(self, ip: str) -> bool:
        """IP adresinin whitelist'te olup olmadığını kontrol et"""
        return ip in self.whitelisted_ips
    
    def is_ip_blacklisted(self, ip: str) -> bool:
        """IP adresinin blacklist'te olup olmadığını kontrol et"""
        return ip in self.blacklisted_ips
    
    def add_to_blacklist(self, ip: str, reason: str = ""):
        """IP'yi blacklist'e ekle"""
        with self.ip_lock:
            self.blacklisted_ips.add(ip)
            self.blocked_ips.add(ip)
        
        self.logger.warning(f"IP {ip} blacklist'e eklendi. Sebep: {reason}")
        self._log_to_database(ip, "BLACKLIST_ADD", 3, reason)
    
    def remove_from_blacklist(self, ip: str):
        """IP'yi blacklist'ten çıkar"""
        with self.ip_lock:
            self.blacklisted_ips.discard(ip)
            self.blocked_ips.discard(ip)
        
        self.logger.info(f"IP {ip} blacklist'ten çıkarıldı")
    
    def load_ip_lists(self):
        """Whitelist ve blacklist dosyalarını yükle"""
        # Whitelist yükle
        whitelist_file = self.config.get('PROTECTION', 'whitelist_file')
        if os.path.exists(whitelist_file):
            with open(whitelist_file, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        self.whitelisted_ips.add(ip)
            self.logger.info(f"{len(self.whitelisted_ips)} IP whitelist'e yüklendi")
        
        # Blacklist yükle
        blacklist_file = self.config.get('PROTECTION', 'blacklist_file')
        if os.path.exists(blacklist_file):
            with open(blacklist_file, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('#'):
                        self.blacklisted_ips.add(ip)
                        self.blocked_ips.add(ip)
            self.logger.info(f"{len(self.blacklisted_ips)} IP blacklist'e yüklendi")
    
    def analyze_traffic_pattern(self, ip: str, packet_size: int, request_type: str) -> Tuple[bool, str]:
        """Trafik kalıplarını analiz et ve şüpheli aktivite tespit et"""
        current_time = time.time()
        
        # Rate limiting kontrolü
        max_requests = int(self.config.get('PROTECTION', 'max_requests_per_minute'))
        
        with self.ip_lock:
            # Eski kayıtları temizle (1 dakika)
            while (self.ip_request_times[ip] and 
                   current_time - self.ip_request_times[ip][0] > 60):
                self.ip_request_times[ip].popleft()
            
            # Yeni isteği ekle
            self.ip_request_times[ip].append(current_time)
            
            # Rate limit kontrolü
            if len(self.ip_request_times[ip]) > max_requests:
                return True, "RATE_LIMIT_EXCEEDED"
        
        # Paket boyutu kontrolü
        max_packet_size = int(self.config.get('DETECTION', 'packet_size_threshold'))
        if packet_size > max_packet_size:
            return True, "LARGE_PACKET_ATTACK"
        
        # Kalıp analizi
        if self.config.getboolean('DETECTION', 'enable_pattern_detection'):
            if self._detect_attack_patterns(ip, request_type, packet_size):
                return True, "SUSPICIOUS_PATTERN"
        
        return False, "NORMAL"
    
    def _detect_attack_patterns(self, ip: str, request_type: str, packet_size: int) -> bool:
        """Saldırı kalıplarını tespit et"""
        current_time = time.time()
        
        # IP için kalıp verilerini başlat
        if ip not in self.suspicious_patterns:
            self.suspicious_patterns[ip] = {
                'request_types': defaultdict(int),
                'packet_sizes': [],
                'request_intervals': [],
                'last_request_time': current_time
            }
        
        pattern_data = self.suspicious_patterns[ip]
        
        # İstek türü analizi
        pattern_data['request_types'][request_type] += 1
        
        # Paket boyutu analizi
        pattern_data['packet_sizes'].append(packet_size)
        if len(pattern_data['packet_sizes']) > 100:
            pattern_data['packet_sizes'].pop(0)
        
        # İstek aralığı analizi
        interval = current_time - pattern_data['last_request_time']
        pattern_data['request_intervals'].append(interval)
        if len(pattern_data['request_intervals']) > 50:
            pattern_data['request_intervals'].pop(0)
        
        pattern_data['last_request_time'] = current_time
        
        # Şüpheli kalıpları kontrol et
        
        # 1. Çok hızlı istekler (botnet)
        if len(pattern_data['request_intervals']) >= 10:
            avg_interval = sum(pattern_data['request_intervals']) / len(pattern_data['request_intervals'])
            if avg_interval < 0.1:  # 100ms'den hızlı
                return True
        
        # 2. Aynı boyutta çok sayıda paket (amplification)
        if len(pattern_data['packet_sizes']) >= 20:
            unique_sizes = len(set(pattern_data['packet_sizes']))
            if unique_sizes < 3:  # Çok az çeşitlilik
                return True
        
        # 3. Tek tip istek bombardımanı
        if sum(pattern_data['request_types'].values()) > 50:
            max_type_count = max(pattern_data['request_types'].values())
            total_requests = sum(pattern_data['request_types'].values())
            if max_type_count / total_requests > 0.9:  # %90'dan fazla aynı tip
                return True
        
        return False
    
    def _log_to_database(self, ip: str, attack_type: str, severity: int, additional_info: str = ""):
        """Saldırı kaydını veritabanına logla"""
        try:
            with self.db_lock:
                cursor = self.db_conn.cursor()
                
                country = self.get_country_code(ip) or "UNKNOWN"
                
                cursor.execute('''
                    INSERT INTO attack_logs 
                    (timestamp, ip_address, attack_type, severity, packets_count, blocked, country, additional_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    ip,
                    attack_type,
                    severity,
                    1,  # packet count
                    True,
                    country,
                    additional_info
                ))
                
                self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"Veritabanına loglama hatası: {e}")
    
    def process_connection(self, ip: str, port: int, packet_size: int = 0, request_type: str = "UNKNOWN") -> bool:
        """Bağlantıyı işle ve DDoS kontrolü yap"""
        current_time = time.time()
        
        with self.stats_lock:
            self.total_requests += 1
        
        # Whitelist kontrolü
        if self.is_ip_whitelisted(ip):
            return True
        
        # Blacklist kontrolü
        if self.is_ip_blacklisted(ip):
            with self.stats_lock:
                self.blocked_requests += 1
            return False
        
        # Coğrafi filtreleme
        if self.config.getboolean('GEOGRAPHIC', 'enable_geo_blocking'):
            country = self.get_country_code(ip)
            allowed_countries = self.config.get('GEOGRAPHIC', 'allowed_countries').split(',')
            if country and country not in allowed_countries:
                self.add_to_blacklist(ip, f"Coğrafi filtreleme: {country}")
                with self.stats_lock:
                    self.blocked_requests += 1
                return False
        
        # Bağlantı sayısı kontrolü
        max_connections = int(self.config.get('PROTECTION', 'max_connections_per_ip'))
        with self.ip_lock:
            self.ip_connections[ip] += 1
            if self.ip_connections[ip] > max_connections:
                self.add_to_blacklist(ip, f"Çok fazla bağlantı: {self.ip_connections[ip]}")
                with self.stats_lock:
                    self.blocked_requests += 1
                return False
        
        # Trafik kalıbı analizi
        is_suspicious, reason = self.analyze_traffic_pattern(ip, packet_size, request_type)
        if is_suspicious:
            self.add_to_blacklist(ip, f"Şüpheli trafik kalıbı: {reason}")
            with self.stats_lock:
                self.blocked_requests += 1
                self.attack_attempts += 1
            return False
        
        return True
    
    def cleanup_expired_bans(self):
        """Süresi dolan banları temizle"""
        current_time = time.time()
        ban_duration = int(self.config.get('PROTECTION', 'ban_duration_minutes')) * 60
        
        with self.ip_lock:
            # Eski bağlantı kayıtlarını temizle
            for ip in list(self.ip_connections.keys()):
                if current_time - self.last_cleanup > 300:  # 5 dakikada bir temizle
                    self.ip_connections[ip] = max(0, self.ip_connections[ip] - 1)
                    if self.ip_connections[ip] == 0:
                        del self.ip_connections[ip]
        
        self.last_cleanup = current_time
    
    def get_statistics(self) -> Dict:
        """Sistem istatistiklerini döndür"""
        with self.stats_lock:
            stats = {
                'total_requests': self.total_requests,
                'blocked_requests': self.blocked_requests,
                'attack_attempts': self.attack_attempts,
                'blocked_ips_count': len(self.blocked_ips),
                'whitelisted_ips_count': len(self.whitelisted_ips),
                'blacklisted_ips_count': len(self.blacklisted_ips),
                'active_connections': sum(self.ip_connections.values()),
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }
        
        return stats
    
    def save_statistics_to_db(self):
        """İstatistikleri veritabanına kaydet"""
        try:
            stats = self.get_statistics()
            
            with self.db_lock:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    INSERT INTO system_stats 
                    (timestamp, total_requests, blocked_requests, active_connections, 
                     cpu_usage, memory_usage, network_in, network_out)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    stats['total_requests'],
                    stats['blocked_requests'],
                    stats['active_connections'],
                    stats['cpu_usage'],
                    stats['memory_usage'],
                    0,  # network_in placeholder
                    0   # network_out placeholder
                ))
                
                self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"İstatistik kaydetme hatası: {e}")
    
    def start_monitoring(self):
        """İzleme sistemini başlat"""
        self.running = True
        self.start_time = time.time()
        self.load_ip_lists()
        
        self.logger.info("DDoS koruma sistemi aktif oldu")
        
        # Periyodik temizlik ve istatistik kaydetme
        def background_tasks():
            while self.running:
                try:
                    self.cleanup_expired_bans()
                    self.save_statistics_to_db()
                    time.sleep(60)  # Her dakika
                except Exception as e:
                    self.logger.error(f"Arka plan görevi hatası: {e}")
        
        threading.Thread(target=background_tasks, daemon=True).start()
    
    def stop_monitoring(self):
        """İzleme sistemini durdur"""
        self.running = False
        if self.geoip_reader:
            self.geoip_reader.close()
        self.db_conn.close()
        self.logger.info("DDoS koruma sistemi durduruldu")

if __name__ == "__main__":
    # Test için basit kullanım
    ddos_protection = DDoSProtectionSystem()
    ddos_protection.start_monitoring()
    
    # Test senaryoları
    test_ips = [
        "192.168.1.100",
        "10.0.0.1",
        "203.0.113.1",
        "198.51.100.1"
    ]
    
    print("DDoS Koruma Sistemi Test Ediliyor...")
    
    for ip in test_ips:
        result = ddos_protection.process_connection(ip, 30120, 1024, "TCP_CONNECT")
        print(f"IP: {ip} - Sonuç: {'İzinli' if result else 'Engellenmiş'}")
    
    # İstatistikleri göster
    stats = ddos_protection.get_statistics()
    print("\nSistem İstatistikleri:")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    input("\nÇıkmak için Enter'a basın...")
    ddos_protection.stop_monitoring() 