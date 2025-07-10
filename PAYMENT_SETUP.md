# Sistema de Pagamento - Square Cloud Bot

## Configuração

### 1. Configurar PixGG

1. Acesse [app.pixgg.com](https://app.pixgg.com)
2. Faça login com suas credenciais
3. Obtenha suas credenciais de API

### 2. Configurar o Bot (Método Automático - Recomendado)

Use o comando `/config` no Discord:

1. Execute `/config` e selecione a categoria para tickets
2. Se já existe uma conta vinculada, você verá a opção de desvincular
3. Clique em "🔑 Configurar PixGG" para vincular uma nova conta
4. Digite seu email e senha do PixGG
5. O sistema testará automaticamente as credenciais
6. Após confirmar, você pode alterar o preço clicando em "💰 Alterar Preço"

**Nota:** Cada servidor pode ter sua própria conta PixGG vinculada.

### 3. Configurar o Bot (Método Manual)

Edite o arquivo `payment_config.py`:

```python
# Configurações da API PixGG
PIXGG_CONFIG = {
    "email": "seu_email@exemplo.com",
    "password": "sua_senha",
    "base_url": "https://app.pixgg.com"
}

# Preço do deploy
DEPLOY_PRICE = 5.00  # Preço em reais por deploy
```

## Como Funciona

### Sistema de Vinculação por Servidor

- **Contas Independentes**: Cada servidor Discord pode ter sua própria conta PixGG vinculada
- **Configuração Segura**: As credenciais são armazenadas por servidor no arquivo `pixgg_keys.json`
- **Fácil Gerenciamento**: Admins podem vincular/desvincular contas usando `/config`
- **Isolamento**: Pagamentos de um servidor não interferem em outros

### Fluxo de Pagamento

1. **Usuário executa `/deploy`** → Cria ticket
2. **Usuário envia ZIP** → Bot salva o arquivo
3. **Bot mostra PIX** → QR Code e código copia e cola
4. **Usuário paga** → Via PIX
5. **Admin confirma** → Usando `/admin_payments`
6. **Bot faz deploy** → Envia para Square Cloud

### Comandos Disponíveis

#### Para Usuários
- `/payments` - Ver histórico de pagamentos
- `/deploy` - Abrir ticket para deploy (agora com pagamento)

#### Para Administradores
- `/admin_payments` - Gerenciar pagamentos pendentes
- `/config` - Configurar categoria de tickets e sistema de pagamento

## Estrutura de Arquivos

```
square/
├── bot.py              # Bot principal
├── payment_config.py   # Configurações de pagamento
├── payment_manager.py  # Gerenciador de pagamentos
├── payments.json       # Dados dos pagamentos (gerado automaticamente)
└── requirements.txt    # Dependências
```

## Dependências

Certifique-se de ter instalado:

```bash
pip install requests
```

## Segurança

- As credenciais do PixGG ficam no arquivo `payment_config.py`
- O arquivo `payments.json` contém dados sensíveis (não commitar no git)
- Apenas administradores podem confirmar pagamentos

## Troubleshooting

### Erro de Login PixGG
- Verifique se as credenciais estão corretas
- Confirme se a conta PixGG está ativa

### Pagamento não aparece
- Use `/admin_payments` para ver pagamentos pendentes
- Verifique se o ID do pagamento está correto

### Bot não responde
- Verifique se o `payment_manager.py` está no mesmo diretório
- Confirme se todas as dependências estão instaladas 