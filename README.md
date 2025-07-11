# 🤖 Square Bot - Bot de Deploy Automático

Um bot Discord avançado para gerenciamento de deploys na Square Cloud com sistema de pagamento PIX integrado.

Convite do bot:
```bash
[Clique aqui!](https://discord.com/oauth2/authorize?client_id=1391958519510597783&permissions=8&integration_type=0&scope=bot)
```

## 🚀 Funcionalidades

### 📦 **Sistema de Deploy Automático**
- **Comando `/deploy`**: Abre ticket para envio de arquivo ZIP
- **Upload automático**: Salva arquivo e gera pagamento PIX
- **Deploy automático**: Após confirmação de pagamento, faz deploy na Square Cloud
- **Fechamento automático**: Ticket fecha após 10 minutos

### 💳 **Sistema de Pagamento PIX**
- **Integração PixGG**: Gera pagamentos PIX automaticamente
- **Código único**: Cada pagamento tem código identificador único
- **QR Code**: Gera QR Code para pagamento via celular
- **Verificação automática**: Confirma pagamento a cada 10 segundos
- **Limpeza automática**: Remove QR Codes após pagamento/expiração

### 🔑 **Gerenciamento de Chaves**
- **Comando `/key`**: Configura chave da Square Cloud
- **Validação automática**: Testa chave antes de salvar
- **Múltiplos usuários**: Cada usuário tem sua própria chave

### 📊 **Gerenciamento de Aplicações**
- **Comando `/status`**: Lista e gerencia aplicações
- **Controles**: Start, Stop, Restart de aplicações
- **Informações detalhadas**: Status, RAM, CPU, logs
- **Comando `/delete`**: Remove aplicações

### 💰 **Sistema de Pagamentos**
- **Comando `/payments`**: Usuários veem seus pagamentos
- **Comando `/admin_payments`**: Administradores gerenciam pagamentos
- **Histórico completo**: Todos os pagamentos registrados

### 🔧 **Configurações Administrativas**
- **Comando `/config`**: Configura categoria de tickets e PixGG
- **Preços personalizados**: Define valor por deploy por servidor
- **Credenciais PixGG**: Configura email e senha do PixGG

### 💾 **Backup e Domínios**
- **Comando `/backup`**: Cria e gerencia backups
- **Comando `/domain`**: Configura domínios personalizados
- **Gerenciamento completo**: Lista, cria e remove backups/domínios

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Discord Bot Token
- Conta na Square Cloud
- Conta no PixGG (para pagamentos)

### 1. Clone o repositório
```bash
git clone https://github.com/SrRaposoOfc/SquareBotV1
cd square-bot
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o bot
1. Crie um bot no [Discord Developer Portal](https://discord.com/developers/applications)
2. Copie o token do bot
3. Edite o arquivo `config.py`:
```python
BOT_TOKEN = "seu_token_aqui"
BOT_VERSION = "1.0.0"
```

### 4. Configure o PixGG (opcional)
1. Crie uma conta no [PixGG](https://pixgg.com)
2. Use o comando `/config` no Discord para configurar credenciais
3. Defina o preço do deploy

### 5. Execute o bot
```bash
python bot.py
```

## 📋 Comandos Disponíveis

### 👤 **Comandos de Usuário**
- `/ping` - Testa se o bot está online
- `/key` - Configura chave da Square Cloud
- `/deploy` - Abre ticket para deploy
- `/status` - Gerencia aplicações
- `/delete` - Remove aplicações
- `/payments` - Ver pagamentos
- `/backup` - Gerencia backups
- `/domain` - Gerencia domínios
- `/info` - Informações do bot

### 👑 **Comandos de Administrador**
- `/config` - Configura sistema de pagamento
- `/admin_payments` - Gerencia pagamentos

## 🔧 Configuração do Sistema

### Configuração de Tickets
1. Execute `/config` como administrador
2. Selecione categoria para tickets
3. Configure credenciais PixGG
4. Defina preço do deploy

### Configuração de Pagamentos
1. **Email PixGG**: Email da sua conta PixGG
2. **Senha PixGG**: Senha da sua conta PixGG
3. **Preço**: Valor em reais para cada deploy

## 💳 Como Receber Pagamentos via PIX

Para que o sistema de pagamentos funcione, é necessário:
- Criar uma conta no site [pixgg.com](https://pixgg.com)
- No Discord, usar o comando `/config` e informar o **email** e **senha** da sua conta PixGG

> **Atenção:** O bot utiliza essas credenciais para gerar cobranças PIX automaticamente para seus usuários.

## 📁 Estrutura de Arquivos
```
square/
├── bot.py                 # Bot principal
├── payment_manager.py     # Gerenciador de pagamentos
├── config.py              # Configurações do bot
├── requirements.txt       # Dependências Python
├── deploy_uploads/        # Arquivos temporários de upload
├── qrcodes/               # QR Codes gerados (limpeza automática)
├── data/                  # Todos os arquivos .json do sistema
│   ├── server_keys.json       # Chaves dos usuários
│   ├── pixgg_keys.json        # Credenciais PixGG
│   ├── deploy_prices.json     # Preços por servidor
│   ├── ticket_config.json     # Configurações de tickets
│   ├── ticket_uploads.json    # Uploads de tickets
│   ├── ticket_open.json       # Tickets abertos
│   ├── payments.json          # Histórico de pagamentos
│   └── codigo_doacao.json     # Códigos de pagamento PIX temporários
└── ...
```

## 📦 Exemplo de squarecloud.app

Para fazer deploy, seu ZIP deve conter um arquivo `squarecloud.app`:

```env
DISPLAY_NAME=nome da aplicação
MAIN=Arquivo principal
VERSION=recommended
MEMORY=Minimo 512 para sites e 256 para bots
AUTORESTART=true
# Se for site ou API, adicione também:
SUBDOMAIN=subdominio do seu site
```

## 🔄 Fluxo de Deploy

1. **Usuário executa `/deploy`**
2. **Bot abre ticket** no canal configurado
3. **Usuário envia ZIP** da aplicação
4. **Bot gera pagamento PIX** com código único
5. **Usuário paga** via PIX (QR Code ou código)
6. **Bot detecta pagamento** automaticamente
7. **Bot atualiza painel** mostrando confirmação
8. **Bot faz deploy** na Square Cloud automaticamente
9. **Ticket fecha** após 10 minutos

## 🧹 Limpeza Automática

O sistema limpa automaticamente:
- **QR Codes processados**: Removidos após confirmação
- **QR Codes expirados**: Removidos após 10 minutos
- **QR Codes órfãos**: Limpeza periódica a cada 10 minutos
- **Arquivos temporários**: Removidos após deploy

## 🔒 Segurança

- **Chaves criptografadas**: Chaves da Square Cloud são salvas localmente
- **Verificação de permissões**: Apenas quem criou o pagamento pode ver PIX/QR
- **Expiração automática**: Pagamentos expiram em 10 minutos
- **Limpeza de dados**: Arquivos sensíveis são removidos automaticamente

## 🐛 Solução de Problemas

### Bot não responde
- Verifique se o token está correto
- Confirme se o bot tem permissões no servidor
- Verifique se as dependências estão instaladas

### Erro no PixGG
- Confirme credenciais no comando `/config`
- Verifique se a conta PixGG está ativa
- Teste login manual no site PixGG

### Erro no deploy
- Verifique se a chave da Square Cloud está correta
- Confirme se o ZIP contém `squarecloud.app`
- Verifique se a aplicação não excede limites da Square Cloud

## 📝 Logs

O bot gera logs detalhados:
- `DEBUG`: Informações de debug
- `INFO`: Informações gerais
- `WARNING`: Avisos
- `ERROR`: Erros

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

Para suporte:
- Abra uma issue no GitHub
- Entre em contato via Discord
- Consulte a documentação da Square Cloud

---

**Desenvolvido por Sr.Raposo para a comunidade Square Cloud** 
