#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Platform Alert System
FiveM DDoS koruma sistemi için çoklu uyarı sistemi
E-posta, Discord, Telegram desteği
"""

import smtplib
import logging
import requests
import threading
import time
import json
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import configparser
import asyncio
import os

class EmailAlerter:
    """E-posta uyarı sistemi"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = logging.getLogger('EmailAlerter')
        
        self.smtp_server = config.get('ALERTS', 'smtp_server', fallback='smtp.gmail.com')
        self.smtp_port = config.getint('ALERTS', 'smtp_port', fallback=587)
        self.username = config.get('ALERTS', 'smtp_username', fallback='')
        self.password = config.get('ALERTS', 'smtp_password', fallback='')
        self.recipients = config.get('ALERTS', 'alert_recipients', fallback='').split(',')
        
        self.enabled = config.getboolean('ALERTS', 'email_alerts_enabled', fallback=False)
        
        if not self.username or not self.password:
            self.enabled = False
            self.logger.warning("E-posta bilgileri eksik, e-posta uyarıları devre dışı")
    
    def send_alert(self, subject: str, message: str, severity: str = "INFO", attachment_path: str = None) -> bool:
        """E-posta uyarısı gönder"""
        if not self.enabled:
            return False
        
        try:
            # E-posta mesajı oluştur
            msg = MimeMultipart()
            msg['From'] = self.username
            msg['Subject'] = f"[FiveM DDoS Alert - {severity}] {subject}"
            
            # HTML formatında mesaj
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #{'#dc3545' if severity == 'CRITICAL' else '#ffc107' if severity == 'WARNING' else '#28a745'}; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; color: #6c757d; }}
                    .alert-info {{ background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 10px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🛡️ FiveM DDoS Koruma Uyarısı</h2>
                    <p>Seviye: {severity}</p>
                </div>
                <div class="content">
                    <div class="alert-info">
                        <strong>Zaman:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        <strong>Sunucu:</strong> FiveM DDoS Protection System<br>
                        <strong>Durum:</strong> {subject}
                    </div>
                    <h3>Detaylar:</h3>
                    <p>{message.replace(chr(10), '<br>')}</p>
                </div>
                <div class="footer">
                    <p>Bu uyarı FiveM DDoS Koruma Sistemi tarafından otomatik olarak gönderilmiştir.</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html_body, 'html'))
            
            # Ek dosya varsa ekle
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MimeBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            # E-posta gönder
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            for recipient in self.recipients:
                if recipient.strip():
                    msg['To'] = recipient.strip()
                    server.send_message(msg)
                    self.logger.info(f"E-posta uyarısı gönderildi: {recipient.strip()}")
                    del msg['To']
            
            server.quit()
            return True
            
        except Exception as e:
            self.logger.error(f"E-posta gönderme hatası: {e}")
            return False

class DiscordAlerter:
    """Discord webhook uyarı sistemi"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = logging.getLogger('DiscordAlerter')
        
        self.webhook_url = config.get('ALERTS', 'discord_webhook_url', fallback='')
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            self.logger.info("Discord webhook URL'si boş, Discord uyarıları devre dışı")
    
    def send_alert(self, title: str, message: str, severity: str = "INFO") -> bool:
        """Discord uyarısı gönder"""
        if not self.enabled:
            return False
        
        try:
            # Renk kodları
            color_map = {
                'INFO': 0x28a745,      # Yeşil
                'WARNING': 0xffc107,   # Sarı
                'CRITICAL': 0xdc3545   # Kırmızı
            }
            
            # Emoji haritası
            emoji_map = {
                'INFO': '🛡️',
                'WARNING': '⚠️',
                'CRITICAL': '🚨'
            }
            
            embed = {
                "title": f"{emoji_map.get(severity, '🛡️')} FiveM DDoS Koruma Uyarısı",
                "description": f"**{title}**",
                "color": color_map.get(severity, 0x28a745),
                "fields": [
                    {
                        "name": "Seviye",
                        "value": severity,
                        "inline": True
                    },
                    {
                        "name": "Zaman",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "inline": True
                    },
                    {
                        "name": "Detaylar",
                        "value": message[:1000] + "..." if len(message) > 1000 else message,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "FiveM DDoS Protection System",
                    "icon_url": "https://cdn.discordapp.com/attachments/123456789/shield.png"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "username": "FiveM DDoS Guard",
                "avatar_url": "https://cdn.discordapp.com/attachments/123456789/shield.png",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                self.logger.info("Discord uyarısı başarıyla gönderildi")
                return True
            else:
                self.logger.error(f"Discord uyarısı gönderilemedi: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Discord uyarısı hatası: {e}")
            return False

class TelegramAlerter:
    """Telegram bot uyarı sistemi"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = logging.getLogger('TelegramAlerter')
        
        self.bot_token = config.get('ALERTS', 'telegram_bot_token', fallback='')
        self.chat_id = config.get('ALERTS', 'telegram_chat_id', fallback='')
        
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            self.logger.info("Telegram bot bilgileri eksik, Telegram uyarıları devre dışı")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_alert(self, title: str, message: str, severity: str = "INFO") -> bool:
        """Telegram uyarısı gönder"""
        if not self.enabled:
            return False
        
        try:
            # Emoji haritası
            emoji_map = {
                'INFO': '🛡️',
                'WARNING': '⚠️',
                'CRITICAL': '🚨'
            }
            
            # Mesaj formatı
            formatted_message = f"""
{emoji_map.get(severity, '🛡️')} *FiveM DDoS Koruma Uyarısı*

*Seviye:* {severity}
*Zaman:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Durum:* {title}

*Detaylar:*
{message}

_FiveM DDoS Protection System_
            """.strip()
            
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Telegram uyarısı başarıyla gönderildi")
                return True
            else:
                self.logger.error(f"Telegram uyarısı gönderilemedi: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram uyarısı hatası: {e}")
            return False

class SMSAlerter:
    """SMS uyarı sistemi (Twilio entegrasyonu)"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = logging.getLogger('SMSAlerter')
        
        # Twilio bilgileri (isteğe bağlı)
        self.account_sid = config.get('ALERTS', 'twilio_account_sid', fallback='')
        self.auth_token = config.get('ALERTS', 'twilio_auth_token', fallback='')
        self.from_number = config.get('ALERTS', 'twilio_from_number', fallback='')
        self.to_numbers = config.get('ALERTS', 'sms_recipients', fallback='').split(',')
        
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        
        if not self.enabled:
            self.logger.info("SMS bilgileri eksik, SMS uyarıları devre dışı")
    
    def send_alert(self, title: str, message: str, severity: str = "INFO") -> bool:
        """SMS uyarısı gönder"""
        if not self.enabled:
            return False
        
        try:
            # Twilio client (lazy import)
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            sms_message = f"FiveM DDoS Alert [{severity}]: {title}\n{message[:100]}..."
            
            success_count = 0
            for number in self.to_numbers:
                if number.strip():
                    try:
                        message = client.messages.create(
                            body=sms_message,
                            from_=self.from_number,
                            to=number.strip()
                        )
                        success_count += 1
                        self.logger.info(f"SMS gönderildi: {number.strip()}")
                    except Exception as e:
                        self.logger.error(f"SMS gönderme hatası ({number.strip()}): {e}")
            
            return success_count > 0
            
        except ImportError:
            self.logger.error("Twilio kütüphanesi bulunamadı. pip install twilio")
            return False
        except Exception as e:
            self.logger.error(f"SMS gönderme hatası: {e}")
            return False

class MultiPlatformAlertSystem:
    """Çoklu platform uyarı sistemi yöneticisi"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.logger = logging.getLogger('AlertSystem')
        
        # Alert service'leri başlat
        self.email_alerter = EmailAlerter(config)
        self.discord_alerter = DiscordAlerter(config)
        self.telegram_alerter = TelegramAlerter(config)
        self.sms_alerter = SMSAlerter(config)
        
        # Alert kuyruğu
        self.alert_queue = []
        self.queue_lock = threading.Lock()
        
        # Rate limiting
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 dakika
        
        # Alert geçmişi
        self.alert_history = []
        self.max_history = 1000
        
        # Background worker
        self.worker_running = False
        self.worker_thread = None
        
        self.critical_threshold = config.getint('ALERTS', 'critical_attack_threshold', fallback=50)
        
        self.logger.info("Multi-platform alert sistemi başlatıldı")
    
    def start_alert_worker(self):
        """Background alert worker'ını başlat"""
        if self.worker_running:
            return
        
        self.worker_running = True
        
        def worker():
            while self.worker_running:
                try:
                    self._process_alert_queue()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Alert worker hatası: {e}")
                    time.sleep(5)
        
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        self.logger.info("Alert worker başlatıldı")
    
    def stop_alert_worker(self):
        """Alert worker'ını durdur"""
        self.worker_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("Alert worker durduruldu")
    
    def _process_alert_queue(self):
        """Alert kuyruğunu işle"""
        with self.queue_lock:
            if not self.alert_queue:
                return
            
            alert = self.alert_queue.pop(0)
        
        try:
            self._send_alert_to_all_platforms(
                alert['title'],
                alert['message'],
                alert['severity']
            )
        except Exception as e:
            self.logger.error(f"Alert gönderme hatası: {e}")
    
    def _send_alert_to_all_platforms(self, title: str, message: str, severity: str):
        """Tüm platformlara uyarı gönder"""
        platforms_sent = []
        
        # E-posta
        if self.email_alerter.send_alert(title, message, severity):
            platforms_sent.append("Email")
        
        # Discord
        if self.discord_alerter.send_alert(title, message, severity):
            platforms_sent.append("Discord")
        
        # Telegram
        if self.telegram_alerter.send_alert(title, message, severity):
            platforms_sent.append("Telegram")
        
        # SMS (sadece kritik uyarılar için)
        if severity == "CRITICAL" and self.sms_alerter.send_alert(title, message, severity):
            platforms_sent.append("SMS")
        
        # Geçmişe ekle
        self.alert_history.append({
            'timestamp': datetime.now(),
            'title': title,
            'message': message,
            'severity': severity,
            'platforms': platforms_sent
        })
        
        # Geçmiş boyutunu kontrol et
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        self.logger.info(f"Alert gönderildi: {title} ({', '.join(platforms_sent)})")
    
    def send_attack_alert(self, attack_info: Dict):
        """Saldırı uyarısı gönder"""
        try:
            ip = attack_info.get('ip', 'Bilinmiyor')
            attack_type = attack_info.get('type', 'Bilinmeyen')
            severity = attack_info.get('severity', 1)
            country = attack_info.get('country', 'Bilinmiyor')
            additional_info = attack_info.get('additional_info', '')
            
            # Rate limiting kontrolü
            alert_key = f"attack_{ip}_{attack_type}"
            current_time = time.time()
            
            if alert_key in self.last_alert_time:
                if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                    return  # Çok sık uyarı gönderme
            
            self.last_alert_time[alert_key] = current_time
            
            # Severity belirleme
            if severity >= 3 or attack_info.get('attack_count', 0) > self.critical_threshold:
                alert_severity = "CRITICAL"
            elif severity >= 2:
                alert_severity = "WARNING"
            else:
                alert_severity = "INFO"
            
            title = f"DDoS Saldırısı Tespit Edildi - {attack_type}"
            
            message = f"""
Saldırgan IP: {ip}
Ülke: {country}
Saldırı Türü: {attack_type}
Severity: {severity}/5
Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Ek Bilgiler:
{additional_info}

Otomatik koruma devrede. Gerekli önlemler alınmıştır.
            """.strip()
            
            self.queue_alert(title, message, alert_severity)
            
        except Exception as e:
            self.logger.error(f"Saldırı uyarısı oluşturma hatası: {e}")
    
    def send_system_alert(self, title: str, message: str, severity: str = "INFO"):
        """Sistem uyarısı gönder"""
        self.queue_alert(title, message, severity)
    
    def queue_alert(self, title: str, message: str, severity: str = "INFO"):
        """Uyarıyı kuyruğa ekle"""
        with self.queue_lock:
            self.alert_queue.append({
                'title': title,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now()
            })
    
    def get_alert_statistics(self) -> Dict:
        """Alert istatistiklerini döndür"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_alerts = [
            alert for alert in self.alert_history
            if alert['timestamp'] > last_24h
        ]
        
        severity_counts = {
            'INFO': len([a for a in recent_alerts if a['severity'] == 'INFO']),
            'WARNING': len([a for a in recent_alerts if a['severity'] == 'WARNING']),
            'CRITICAL': len([a for a in recent_alerts if a['severity'] == 'CRITICAL'])
        }
        
        return {
            'total_alerts_24h': len(recent_alerts),
            'severity_breakdown': severity_counts,
            'queue_size': len(self.alert_queue),
            'enabled_platforms': {
                'email': self.email_alerter.enabled,
                'discord': self.discord_alerter.enabled,
                'telegram': self.telegram_alerter.enabled,
                'sms': self.sms_alerter.enabled
            }
        }

# Test fonksiyonu
if __name__ == "__main__":
    import configparser
    
    # Test konfigürasyonu
    config = configparser.ConfigParser()
    config.read('ddos_config.ini')
    
    alert_system = MultiPlatformAlertSystem(config)
    alert_system.start_alert_worker()
    
    # Test uyarısı
    print("Test uyarısı gönderiliyor...")
    
    attack_info = {
        'ip': '203.0.113.100',
        'type': 'SYN_FLOOD',
        'severity': 3,
        'country': 'TR',
        'additional_info': 'Test saldırı senaryosu',
        'attack_count': 150
    }
    
    alert_system.send_attack_alert(attack_info)
    alert_system.send_system_alert("Test Sistem Uyarısı", "Bu bir test mesajıdır", "WARNING")
    
    # İstatistikleri göster
    time.sleep(5)
    stats = alert_system.get_alert_statistics()
    print(f"Alert istatistikleri: {stats}")
    
    alert_system.stop_alert_worker() 