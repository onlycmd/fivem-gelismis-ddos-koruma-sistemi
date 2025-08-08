-- FiveM DDoS Protection Integration
-- FiveM sunucusu için DDoS koruma entegrasyon scripti
-- Bu script FiveM sunucusunda DDoS koruma sistemi ile iletişim kurar

fx_version 'cerulean'
game 'gta5'

author 'AI Assistant'
description 'FiveM DDoS Protection System Integration'
version '1.0.0'

-- Server tarafı scriptler
server_scripts {
    'server/ddos_protection.lua',
    'server/connection_monitor.lua',
    'server/player_security.lua'
}

-- Client tarafı scriptler (isteğe bağlı)
client_scripts {
    'client/security_overlay.lua'
}

-- Konfigürasyon dosyası
shared_scripts {
    'config.lua'
}

-- Python DDoS koruma sistemi ile iletişim modülü 