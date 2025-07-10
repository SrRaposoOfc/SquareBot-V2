# Configurações do Sistema de Pagamento
PAYMENT_ENABLED = True
DEPLOY_PRICE = 5.00  # Preço em reais por deploy

# Configurações da API PixGG (padrão - será sobrescrito por servidor)
PIXGG_CONFIG = {
    "email": "",
    "password": "",
    "base_url": "https://app.pixgg.com"
}

# Arquivo para armazenar credenciais PixGG por servidor
PIXGG_KEYS_FILE = "data/pixgg_keys.json"

# Tempo de expiração do pagamento (em minutos)
PAYMENT_EXPIRATION_MINUTES = 30

# Arquivo para armazenar pagamentos
PAYMENTS_FILE = "data/payments.json"

# Cores para embeds de pagamento
PAYMENT_COLORS = {
    "pending": 0xff9900,    # Laranja
    "completed": 0x00ff00,  # Verde
    "expired": 0xff0000,    # Vermelho
    "cancelled": 0x808080   # Cinza
} 