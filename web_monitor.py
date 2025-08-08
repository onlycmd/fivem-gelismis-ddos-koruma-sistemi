#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FiveM DDoS Protection Web Monitor
Web tabanlı izleme ve yönetim arayüzü
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
from ddos_protection import DDoSProtectionSystem
import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)
app.secret_key = 'fivem_ddos_protection_2024'

# Global DDoS koruma sistemi instance
ddos_system = None

def init_ddos_system():
    """DDoS koruma sistemini başlat"""
    global ddos_system
    if ddos_system is None:
        ddos_system = DDoSProtectionSystem()
        ddos_system.start_monitoring()

@app.route('/')
def dashboard():
    """Ana dashboard"""
    try:
        stats = ddos_system.get_statistics() if ddos_system else {}
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/api/stats')
def api_stats():
    """Gerçek zamanlı istatistikler API"""
    try:
        if ddos_system:
            stats = ddos_system.get_statistics()
            return jsonify(stats)
        return jsonify({'error': 'Sistem başlatılmamış'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/attack_logs')
def api_attack_logs():
    """Saldırı logları API"""
    try:
        conn = sqlite3.connect('ddos_protection.db')
        cursor = conn.cursor()
        
        # Son 24 saatteki saldırıları getir
        cursor.execute('''
            SELECT timestamp, ip_address, attack_type, severity, country, additional_info
            FROM attack_logs 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'timestamp': row[0],
                'ip_address': row[1],
                'attack_type': row[2],
                'severity': row[3],
                'country': row[4],
                'additional_info': row[5]
            })
        
        conn.close()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/traffic_chart')
def api_traffic_chart():
    """Trafik grafiği verisi"""
    try:
        conn = sqlite3.connect('ddos_protection.db')
        cursor = conn.cursor()
        
        # Son 2 saatteki sistem istatistikleri
        cursor.execute('''
            SELECT timestamp, total_requests, blocked_requests, active_connections
            FROM system_stats 
            WHERE timestamp > datetime('now', '-2 hours')
            ORDER BY timestamp
        ''')
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return jsonify({'error': 'Veri bulunamadı'})
        
        timestamps = [row[0] for row in data]
        total_requests = [row[1] for row in data]
        blocked_requests = [row[2] for row in data]
        active_connections = [row[3] for row in data]
        
        # Plotly grafiği oluştur
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=total_requests,
            mode='lines+markers',
            name='Toplam İstekler',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=blocked_requests,
            mode='lines+markers',
            name='Engellenen İstekler',
            line=dict(color='red')
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=active_connections,
            mode='lines+markers',
            name='Aktif Bağlantılar',
            line=dict(color='green'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Gerçek Zamanlı Trafik İzleme',
            xaxis_title='Zaman',
            yaxis_title='İstek Sayısı',
            yaxis2=dict(
                title='Bağlantı Sayısı',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )
        
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return jsonify({'graph': graphJSON})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/blacklist')
def blacklist_page():
    """Kara liste yönetimi sayfası"""
    try:
        blacklisted_ips = list(ddos_system.blacklisted_ips) if ddos_system else []
        return render_template('blacklist.html', blacklisted_ips=blacklisted_ips)
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return render_template('blacklist.html', blacklisted_ips=[])

@app.route('/whitelist')
def whitelist_page():
    """Beyaz liste yönetimi sayfası"""
    try:
        whitelisted_ips = list(ddos_system.whitelisted_ips) if ddos_system else []
        return render_template('whitelist.html', whitelisted_ips=whitelisted_ips)
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return render_template('whitelist.html', whitelisted_ips=[])

@app.route('/add_to_blacklist', methods=['POST'])
def add_to_blacklist():
    """IP'yi kara listeye ekle"""
    try:
        ip = request.form.get('ip', '').strip()
        reason = request.form.get('reason', 'Manuel ekleme')
        
        if not ip:
            flash('IP adresi boş olamaz!', 'error')
            return redirect(url_for('blacklist_page'))
        
        if ddos_system:
            ddos_system.add_to_blacklist(ip, reason)
            flash(f'{ip} adresi kara listeye eklendi.', 'success')
        else:
            flash('DDoS koruma sistemi aktif değil!', 'error')
            
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('blacklist_page'))

@app.route('/remove_from_blacklist', methods=['POST'])
def remove_from_blacklist():
    """IP'yi kara listeden çıkar"""
    try:
        ip = request.form.get('ip', '').strip()
        
        if not ip:
            flash('IP adresi boş olamaz!', 'error')
            return redirect(url_for('blacklist_page'))
        
        if ddos_system:
            ddos_system.remove_from_blacklist(ip)
            flash(f'{ip} adresi kara listeden çıkarıldı.', 'success')
        else:
            flash('DDoS koruma sistemi aktif değil!', 'error')
            
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
    
    return redirect(url_for('blacklist_page'))

@app.route('/settings')
def settings_page():
    """Ayarlar sayfası"""
    try:
        config = ddos_system.config if ddos_system else None
        return render_template('settings.html', config=config)
    except Exception as e:
        flash(f'Hata: {str(e)}', 'error')
        return render_template('settings.html', config=None)

@app.route('/logs')
def logs_page():
    """Detaylı log görüntüleme sayfası"""
    return render_template('logs.html')

@app.route('/api/country_stats')
def api_country_stats():
    """Ülke bazında saldırı istatistikleri"""
    try:
        conn = sqlite3.connect('ddos_protection.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT country, COUNT(*) as attack_count
            FROM attack_logs 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY country
            ORDER BY attack_count DESC
            LIMIT 10
        ''')
        
        country_stats = []
        for row in cursor.fetchall():
            country_stats.append({
                'country': row[0],
                'attack_count': row[1]
            })
        
        conn.close()
        return jsonify(country_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/attack_types')
def api_attack_types():
    """Saldırı türü istatistikleri"""
    try:
        conn = sqlite3.connect('ddos_protection.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT attack_type, COUNT(*) as count
            FROM attack_logs 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY attack_type
            ORDER BY count DESC
        ''')
        
        attack_types = []
        for row in cursor.fetchall():
            attack_types.append({
                'type': row[0],
                'count': row[1]
            })
        
        conn.close()
        return jsonify(attack_types)
        
    except Exception as e:
        return jsonify({'error': str(e)})

# HTML Templates
@app.route('/templates/dashboard.html')
def get_dashboard_template():
    """Dashboard HTML template"""
    return '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FiveM DDoS Koruma Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .attack-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .blocked-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .connection-card {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-active {
            background-color: #28a745;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-shield-alt"></i> FiveM DDoS Koruma
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <span class="status-indicator status-active"></span>
                    Sistem Aktif
                </span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5><i class="fas fa-globe"></i> Toplam İstek</h5>
                            <h3 id="total-requests">{{ stats.total_requests or 0 }}</h3>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card blocked-card">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5><i class="fas fa-ban"></i> Engellenen</h5>
                            <h3 id="blocked-requests">{{ stats.blocked_requests or 0 }}</h3>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card attack-card">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5><i class="fas fa-exclamation-triangle"></i> Saldırı</h5>
                            <h3 id="attack-attempts">{{ stats.attack_attempts or 0 }}</h3>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card connection-card">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5><i class="fas fa-users"></i> Bağlantı</h5>
                            <h3 id="active-connections">{{ stats.active_connections or 0 }}</h3>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-8">
                <div class="chart-container">
                    <h5><i class="fas fa-chart-line"></i> Gerçek Zamanlı Trafik</h5>
                    <div id="traffic-chart"></div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="chart-container">
                    <h5><i class="fas fa-flag"></i> Ülke Bazında Saldırılar</h5>
                    <canvas id="country-chart"></canvas>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="chart-container">
                    <h5><i class="fas fa-list"></i> Son Saldırı Logları</h5>
                    <div class="table-responsive">
                        <table class="table table-striped" id="attack-logs-table">
                            <thead>
                                <tr>
                                    <th>Zaman</th>
                                    <th>IP Adresi</th>
                                    <th>Saldırı Türü</th>
                                    <th>Ülke</th>
                                    <th>Detay</th>
                                </tr>
                            </thead>
                            <tbody id="attack-logs-body">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Gerçek zamanlı güncelleme
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (!data.error) {
                        document.getElementById('total-requests').textContent = data.total_requests || 0;
                        document.getElementById('blocked-requests').textContent = data.blocked_requests || 0;
                        document.getElementById('attack-attempts').textContent = data.attack_attempts || 0;
                        document.getElementById('active-connections').textContent = data.active_connections || 0;
                    }
                })
                .catch(error => console.error('İstatistik güncelleme hatası:', error));
        }

        function updateTrafficChart() {
            fetch('/api/traffic_chart')
                .then(response => response.json())
                .then(data => {
                    if (data.graph) {
                        Plotly.newPlot('traffic-chart', JSON.parse(data.graph).data, JSON.parse(data.graph).layout);
                    }
                })
                .catch(error => console.error('Grafik güncelleme hatası:', error));
        }

        function updateAttackLogs() {
            fetch('/api/attack_logs')
                .then(response => response.json())
                .then(data => {
                    if (!data.error && Array.isArray(data)) {
                        const tbody = document.getElementById('attack-logs-body');
                        tbody.innerHTML = '';
                        
                        data.slice(0, 10).forEach(log => {
                            const row = tbody.insertRow();
                            row.innerHTML = `
                                <td>${new Date(log.timestamp).toLocaleString('tr-TR')}</td>
                                <td><code>${log.ip_address}</code></td>
                                <td><span class="badge bg-danger">${log.attack_type}</span></td>
                                <td>${log.country || 'Bilinmiyor'}</td>
                                <td>${log.additional_info || '-'}</td>
                            `;
                        });
                    }
                })
                .catch(error => console.error('Log güncelleme hatası:', error));
        }

        // Sayfa yüklendiğinde
        document.addEventListener('DOMContentLoaded', function() {
            updateStats();
            updateTrafficChart();
            updateAttackLogs();
            
            // Her 5 saniyede bir güncelle
            setInterval(updateStats, 5000);
            setInterval(updateTrafficChart, 30000);
            setInterval(updateAttackLogs, 10000);
        });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    init_ddos_system()
    
    # Web arayüzünü başlat
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        threaded=True
    ) 