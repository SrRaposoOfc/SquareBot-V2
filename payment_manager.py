import requests
import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from payment_config import *
from discord.ext import tasks
import os
import aiohttp

# Variável global para armazenar pagamentos confirmados
confirmed_payments = []

class PaymentManager:
    def __init__(self, guild_id=None):
        self.guild_id = guild_id
        self.auth_token = None
        self.api_key = None
        self.payments = self.load_payments()
        self.donation_queue = []
        self.processing_donation = False
        self.processed_payment_ids = set()
        if guild_id:
            self.login()
    
    def load_pixgg_keys(self):
        """Carrega credenciais PixGG do arquivo JSON"""
        try:
            with open(PIXGG_KEYS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_pixgg_keys(self, pixgg_keys):
        """Salva credenciais PixGG no arquivo JSON"""
        with open(PIXGG_KEYS_FILE, 'w') as f:
            json.dump(pixgg_keys, f, indent=2)
    
    def get_pixgg_credentials(self, guild_id):
        """Obtém credenciais PixGG de um servidor específico"""
        pixgg_keys = self.load_pixgg_keys()
        return pixgg_keys.get(str(guild_id))
    
    def set_pixgg_credentials(self, guild_id, email, password):
        """Define credenciais PixGG para um servidor específico"""
        pixgg_keys = self.load_pixgg_keys()
        pixgg_keys[str(guild_id)] = {
            "email": email,
            "password": password
        }
        self.save_pixgg_keys(pixgg_keys)
    
    def remove_pixgg_credentials(self, guild_id):
        """Remove credenciais PixGG de um servidor específico"""
        pixgg_keys = self.load_pixgg_keys()
        if str(guild_id) in pixgg_keys:
            del pixgg_keys[str(guild_id)]
            self.save_pixgg_keys(pixgg_keys)
            return True
        return False
    
    def load_deploy_prices(self):
        """Carrega preços de deploy do arquivo JSON"""
        try:
            with open('data/deploy_prices.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_deploy_prices(self, prices):
        """Salva preços de deploy no arquivo JSON"""
        with open('data/deploy_prices.json', 'w') as f:
            json.dump(prices, f, indent=2)
    
    def get_deploy_price(self, guild_id):
        """Obtém o preço de deploy de um servidor específico"""
        prices = self.load_deploy_prices()
        return prices.get(str(guild_id), DEPLOY_PRICE)
    
    def set_deploy_price(self, guild_id, price):
        """Define o preço de deploy para um servidor específico"""
        prices = self.load_deploy_prices()
        prices[str(guild_id)] = price
        self.save_deploy_prices(prices)
    
    def load_payments(self):
        """Carrega pagamentos do arquivo JSON"""
        try:
            with open(PAYMENTS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_payments(self):
        """Salva pagamentos no arquivo JSON"""
        with open(PAYMENTS_FILE, 'w') as f:
            json.dump(self.payments, f, indent=2)
    
    def login(self):
        """Faz login na API PixGG"""
        if not self.guild_id:
            return False
            
        credentials = self.get_pixgg_credentials(self.guild_id)
        if not credentials:
            return False
            
        url = f"{PIXGG_CONFIG['base_url']}/users/login"
        
        payload = {
            "name": "",
            "email": credentials['email'],
            "password": credentials['password']
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://app.pixgg.com",
            "Referer": "https://app.pixgg.com/",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("authToken", "")
                self.api_key = data.get("apiKey", "")
                print("✅ Login no PixGG realizado com sucesso!")
                return True
            else:
                print(f"❌ Erro no login: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na requisição de login: {e}")
            return False
    
    def create_payment(self, user_id, user_name):
        """Cria um novo pagamento"""
        if not self.auth_token:
            if not self.login():
                return None
        
        payment_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=PAYMENT_EXPIRATION_MINUTES)
        
        # Obter preço específico do servidor
        deploy_price = self.get_deploy_price(self.guild_id)
        
        # Criar pagamento na API PixGG
        payment_data = self.create_pixgg_payment(payment_id, deploy_price)
        
        if not payment_data:
            return None
        
        # Salvar pagamento localmente
        self.payments[payment_id] = {
            "user_id": user_id,
            "user_name": user_name,
            "amount": deploy_price,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "pixgg_data": payment_data
        }
        
        self.save_payments()
        return payment_id
    
    def create_pixgg_payment(self, payment_id, amount):
        """Cria doação na API PixGG"""
        url = f"{PIXGG_CONFIG['base_url']}/checkouts"
        
        # Extrair streamer ID do token JWT
        streamer_id = self.extract_streamer_id_from_token()
        
        payload = {
            "streamerId": streamer_id,
            "donatorNickname": payment_id,  # Usar payment_id como nickname
            "donatorMessage": f"Deploy Square Cloud - {payment_id}",
            "donatorAmount": amount,
            "country": "Brazil",
            "fileId": None,
            "minimumDonateAmount": None
        }
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {self.auth_token}",
            "content-type": "application/json",
            "origin": "https://pixgg.com",
            "referer": "https://pixgg.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print(f"✅ Doação PixGG criada com sucesso!")
                return data
            else:
                print(f"❌ Erro ao criar doação PixGG: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na requisição PixGG: {e}")
            return None
    
    def extract_streamer_id_from_token(self):
        """Extrai o streamer ID do token JWT"""
        try:
            import base64
            token_parts = self.auth_token.split('.')
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.b64decode(payload).decode('utf-8')
            payload_data = json.loads(decoded_payload)
            
            user_data_str = payload_data.get('http://schemas.microsoft.com/ws/2008/06/identity/claims/userdata', '{}')
            user_data = json.loads(user_data_str)
            return user_data.get('Id', 55350)  # Fallback
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair streamer ID: {e}")
            return 55350  # Fallback
    
    def check_payment_status(self, payment_id):
        """Verifica o status de um pagamento"""
        if payment_id not in self.payments:
            return None
        
        payment = self.payments[payment_id]
        
        # Verificar se expirou
        expires_at = datetime.fromisoformat(payment['expires_at'])
        if datetime.now() > expires_at and payment['status'] == 'pending':
            payment['status'] = 'expired'
            self.save_payments()
            return 'expired'
        
        # Verificar na API PixGG
        if payment['status'] == 'pending':
            status = self.check_pixgg_payment_status(payment_id)
            if status and status != 'pending':
                payment['status'] = status
                self.save_payments()
        
        return payment['status']
    
    def check_pixgg_payment_status(self, payment_id):
        """Verifica status da doação na API PixGG"""
        if not self.auth_token:
            if not self.login():
                return None
        
        url = f"{PIXGG_CONFIG['base_url']}/Reports/Donations?page=1&pageSize=10&donatorNickName={payment_id}"
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f"Bearer {self.auth_token}",
            "origin": "https://pixgg.com",
            "referer": "https://pixgg.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                doacoes = response.json()
                
                for doacao in doacoes:
                    if doacao['donatorNickname'] == payment_id:
                        status = doacao.get('status', 'pending')
                        return status
                
                return 'pending'
            else:
                print(f"❌ Erro ao verificar doação PixGG: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na verificação PixGG: {e}")
            return None
    
    def get_payment_info(self, payment_id):
        """Retorna informações completas de um pagamento"""
        if payment_id not in self.payments:
            return None
        
        payment = self.payments[payment_id]
        status = self.check_payment_status(payment_id)
        
        # Obter dados do PIX do PixGG
        pixgg_data = payment.get('pixgg_data', {})
        
        return {
            "payment_id": payment_id,
            "user_id": payment['user_id'],
            "user_name": payment['user_name'],
            "amount": payment['amount'],
            "status": status,
            "created_at": payment['created_at'],
            "expires_at": payment['expires_at'],
            "pixgg_data": {
                "pix_url": pixgg_data.get('pixUrl', ''),
                "qr_code": pixgg_data.get('pixUrl', ''),  # Usar PIX URL como QR code
                "pix_code": pixgg_data.get('pixUrl', ''),  # Usar PIX URL como código
                "transaction_id": pixgg_data.get('transactionId', ''),
                "payment_status": pixgg_data.get('status', ''),
                "payment_link": pixgg_data.get('paymentLink', '')
            }
        }
    
    def mark_payment_completed(self, payment_id):
        """Marca um pagamento como concluído (para admins)"""
        if payment_id in self.payments:
            self.payments[payment_id]['status'] = 'completed'
            self.save_payments()
            return True
        return False
    
    def get_user_payments(self, user_id):
        """Retorna todos os pagamentos de um usuário"""
        user_payments = []
        for payment_id, payment in self.payments.items():
            if payment['user_id'] == user_id:
                payment_info = self.get_payment_info(payment_id)
                if payment_info:
                    user_payments.append(payment_info)
        return user_payments
    
    def get_pending_payments(self):
        """Retorna todos os pagamentos pendentes"""
        pending = []
        for payment_id in self.payments:
            status = self.check_payment_status(payment_id)
            if status == 'pending':
                payment_info = self.get_payment_info(payment_id)
                if payment_info:
                    pending.append(payment_info)
        return pending 

    def start_auto_check(self):
        """Inicia a verificação automática periódica"""
        if not hasattr(self, 'check_donations') or self.check_donations.is_running() == False:
            self.check_donations.start()
            print(f"✅ Verificação automática iniciada para guild {self.guild_id}")
    
    def stop_auto_check(self):
        """Para a verificação automática"""
        if hasattr(self, 'check_donations') and self.check_donations.is_running():
            self.check_donations.cancel()
            print(f"⏹️ Verificação automática parada para guild {self.guild_id}")

    @tasks.loop(seconds=10)
    async def check_donations(self):
        """Verifica automaticamente os pagamentos pendentes a cada 10 segundos"""
        try:
            # Limpar QR Codes órfãos a cada 60 verificações (10 minutos)
            if not hasattr(self, '_cleanup_counter'):
                self._cleanup_counter = 0
            self._cleanup_counter += 1
            
            if self._cleanup_counter >= 60:
                self.cleanup_orphaned_qr_codes()
                self._cleanup_counter = 0
            
            # Ler códigos pendentes do arquivo
            codes_data = self.read_code_from_file()
            if not codes_data:
                return

            if codes_data:
                print(f"DEBUG: Verificando {len(codes_data)} códigos pendentes...")
                
                # Verificar todos os pagamentos no PixGG de uma vez
                try:
                    headers = {
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6IlZpbmljaXVzcmluYWxkaTI0OUBnbWFpbC5jb20iLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3VzZXJkYXRhIjoie1wiTmFtZVwiOlwiVmluaWNpdXMgZGEgU2lsdmEgUmluYWxkaVwiLFwiRW1haWxcIjpcIlZpbmljaXVzcmluYWxkaTI0OUBnbWFpbC5jb21cIixcIklkXCI6NTUzNTB9Iiwicm9sZSI6IlN0cmVhbWVyIiwibmJmIjoxNzQ5OTEwMTQyLCJleHAiOjE3NTI1MDIxNDIsImlhdCI6MTc0OTkxMDE0Mn0.sT_72TU5Kb-kmdQAc_MzbPfrcznQ8KumeGA5AMCIrOg",
                        "origin": "https://pixgg.com",
                        "referer": "https://pixgg.com/",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
                    }

                    # Buscar todas as doações recentes
                    url = "https://app.pixgg.com/Reports/Donations?page=1&pageSize=50"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as resp:
                            if resp.status == 200:
                                donations = await resp.json()
                                print(f"DEBUG: {len(donations)} doações encontradas no PixGG")
                                
                                # Processar cada código pendente
                                for code, user_id in codes_data:
                                    # Procurar pagamento correspondente
                                    payment_found = False
                                    for donation in donations:
                                        if str(donation.get('donatorNickname', '')).strip().upper() == str(code).strip().upper():
                                            amount = donation.get('totalAmount', 0)
                                            print(f"✅ Pagamento confirmado: R${amount} - Código: {code}")
                                            
                                            # Marcar como processado
                                            self.mark_code_as_processed(code)
                                            
                                            # Atualizar status do pagamento
                                            self.update_payment_status(user_id, 'completed', donation)
                                            
                                            # Atualizar painel de pagamento
                                            await self.update_payment_panel(user_id, code, "confirmed")
                                            
                                            # Adicionar à lista de pagamentos confirmados para processamento pelo bot
                                            confirmed_payments.append({
                                                'user_id': user_id,
                                                'code': code,
                                                'amount': amount,
                                                'timestamp': datetime.now().isoformat()
                                            })
                                            
                                            # Fazer deploy automático
                                            await self.notify_payment_completed(user_id, code)
                                            payment_found = True
                                            break
                                    
                                    if not payment_found:
                                        print(f"DEBUG: Nenhuma doação encontrada para o código {code}")
                            else:
                                print(f"ERRO: Falha na requisição - Status {resp.status}")
                
                except Exception as e:
                    print(f"ERRO ao verificar pagamentos: {e}")

        except Exception as e:
            print(f"ERRO em check_donations: {str(e)}")



    def read_code_from_file(self):
        """Lê códigos pendentes do arquivo JSON e remove expirados"""
        try:
            if not os.path.exists('data/codigo_doacao.json'):
                return []
            
            with open('data/codigo_doacao.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                codes = data.get('codes', [])
                
                # Filtrar códigos não processados e não expirados
                current_time = datetime.now().timestamp()
                valid_codes = []
                expired_codes = []
                
                for code_data in codes:
                    if not code_data.get('processed', False):
                        try:
                            # Verificar se o código não expirou (10 minutos)
                            expires_at = float(code_data.get('expires_at', 0))
                            if current_time <= expires_at:
                                valid_codes.append(code_data)
                            else:
                                expired_codes.append(code_data)
                                print(f"DEBUG: Código {code_data.get('code')} expirado. Removendo da fila.")
                                
                                # Deletar QR Code do código expirado
                                if 'qr_code_filename' in code_data and os.path.exists(code_data['qr_code_filename']):
                                    try:
                                        os.remove(code_data['qr_code_filename'])
                                        print(f"DEBUG: Arquivo QR Code expirado {code_data['qr_code_filename']} removido.")
                                    except Exception as e:
                                        print(f"ERRO ao remover arquivo QR Code expirado {code_data['qr_code_filename']}: {e}")
                        except (ValueError, TypeError) as e:
                            print(f"ERRO ao processar timestamp do código {code_data.get('code')}: {e}")
                            expired_codes.append(code_data)
                
                # Remover códigos expirados e salvar arquivo atualizado
                if expired_codes:
                    codes = [code for code in codes if code not in expired_codes]
                    with open('data/codigo_doacao.json', 'w', encoding='utf-8') as f:
                        json.dump({'codes': codes}, f, indent=4)
                    print(f"DEBUG: {len(expired_codes)} códigos expirados removidos.")
                
                if valid_codes:
                    return [(code['code'], code['user_id']) for code in valid_codes]
                
                return []
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"ERRO ao ler arquivo codigo_doacao.json: {e}")
            return []

    def mark_code_as_processed(self, code):
        """Marca um código como processado e limpa expirados"""
        try:
            if not os.path.exists('data/codigo_doacao.json'):
                return

            with open('data/codigo_doacao.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                codes = data.get('codes', [])

            qr_file_to_delete = None
            expired_codes = []
            current_time = datetime.now().timestamp()
            
            # Marcar código como processado e verificar expirados
            for code_data in codes:
                if code_data['code'] == code:
                    code_data['processed'] = True
                    if 'qr_code_filename' in code_data and os.path.exists(code_data['qr_code_filename']):
                        qr_file_to_delete = code_data['qr_code_filename']
                elif not code_data.get('processed', False):
                    # Verificar se outros códigos expiraram
                    expires_at = float(code_data.get('expires_at', 0))
                    if current_time > expires_at:
                        expired_codes.append(code_data)
                        print(f"DEBUG: Código {code_data.get('code')} expirado durante processamento.")
                        
                        # Deletar QR Code do código expirado
                        if 'qr_code_filename' in code_data and os.path.exists(code_data['qr_code_filename']):
                            try:
                                os.remove(code_data['qr_code_filename'])
                                print(f"DEBUG: Arquivo QR Code expirado {code_data['qr_code_filename']} removido.")
                            except Exception as e:
                                print(f"ERRO ao remover arquivo QR Code expirado {code_data['qr_code_filename']}: {e}")

            # Remover códigos expirados
            codes = [code for code in codes if code not in expired_codes]

            # Salvar arquivo atualizado
            with open('data/codigo_doacao.json', 'w', encoding='utf-8') as f:
                json.dump({'codes': codes}, f, indent=4)

            # Deletar o arquivo QR Code do código processado
            if qr_file_to_delete:
                try:
                    os.remove(qr_file_to_delete)
                    print(f"DEBUG: Arquivo QR Code processado {qr_file_to_delete} removido.")
                except Exception as e:
                    print(f"ERRO ao remover arquivo QR Code processado {qr_file_to_delete}: {e}")

            # Se todos os códigos foram processados, deletar o arquivo
            if all(code_data.get('processed', False) for code_data in codes):
                os.remove('data/codigo_doacao.json')
                print("Todos os códigos foram processados. Arquivo codigo_doacao.json removido.")

            if expired_codes:
                print(f"DEBUG: {len(expired_codes)} códigos expirados removidos durante processamento.")

        except Exception as e:
            print(f"ERRO ao marcar código como processado: {e}")

    async def check_pixgg_payment(self, code):
        """Verifica se o pagamento foi realizado no PixGG"""
        try:
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6IlZpbmljaXVzcmluYWxkaTI0OUBnbWFpbC5jb20iLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3VzZXJkYXRhIjoie1wiTmFtZVwiOlwiVmluaWNpdXMgZGEgU2lsdmEgUmluYWxkaVwiLFwiRW1haWxcIjpcIlZpbmljaXVzcmluYWxkaTI0OUBnbWFpbC5jb21cIixcIklkXCI6NTUzNTB9Iiwicm9sZSI6IlN0cmVhbWVyIiwibmJmIjoxNzQ5OTEwMTQyLCJleHAiOjE3NTI1MDIxNDIsImlhdCI6MTc0OTkxMDE0Mn0.sT_72TU5Kb-kmdQAc_MzbPfrcznQ8KumeGA5AMCIrOg",
                "origin": "https://pixgg.com",
                "referer": "https://pixgg.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            }

            url = f"https://app.pixgg.com/Reports/Donations?page=1&pageSize=10&donatorNickName={code}"
            print(f"DEBUG: Verificando pagamento para código: {code}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        print(f"ERRO: Falha na requisição - Status {resp.status}")
                        return None

                    checkouts = await resp.json()
                    if not checkouts:
                        return None

                    donation = checkouts[0]
                    return donation

        except Exception as e:
            print(f"ERRO ao verificar pagamento PixGG: {e}")
            return None

    def update_payment_status(self, user_id, status, payment_data):
        """Atualiza o status de um pagamento"""
        for payment in self.payments:
            if payment['user_id'] == user_id and payment['status'] == 'pending':
                payment['status'] = status
                payment['pixgg_data'] = payment_data
                payment['completed_at'] = datetime.now().isoformat()
                self.save_payments()
                break
    
    def save_code_to_file(self, code, user_id, qr_code_filename):
        """Salva código no arquivo JSON com timestamp de expiração"""
        filename = "data/codigo_doacao.json"
        print(f"DEBUG: Tentando salvar código no arquivo: {filename}")
        try:
            # Carregar dados existentes ou criar nova lista
            if os.path.exists(filename):
                print(f"DEBUG: Arquivo {filename} encontrado. Carregando dados existentes.")
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    codes = data.get('codes', [])
            else:
                print(f"DEBUG: Arquivo {filename} não encontrado. Criando novo.")
                codes = []

            # Adicionar novo código com timestamp de criação
            current_time = datetime.now().timestamp()
            new_entry = {
                'code': code,
                'user_id': user_id,
                'timestamp': current_time,
                'expires_at': current_time + 600,  # 10 minutos = 600 segundos
                'processed': False,
                'qr_code_filename': qr_code_filename
            }
            codes.append(new_entry)
            print(f"DEBUG: Novo código adicionado: {new_entry}")

            # Salvar todos os códigos
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({'codes': codes}, f, indent=4)
            print(f"DEBUG: Arquivo {filename} atualizado com sucesso para o código: {code}")

        except json.JSONDecodeError as e:
            print(f"ERRO: O arquivo {filename} está corrompido ou vazio (JSON inválido): {e}")
            print("DEBUG: Criando um novo arquivo para evitar problemas futuros.")
            current_time = datetime.now().timestamp()
            codes = [{
                'code': code,
                'user_id': user_id,
                'timestamp': current_time,
                'expires_at': current_time + 600,  # 10 minutos
                'processed': False,
                'qr_code_filename': qr_code_filename
            }]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({'codes': codes}, f, indent=4)
            print(f"DEBUG: Arquivo {filename} recriado com sucesso com o novo código.")

        except Exception as e:
            print(f"ERRO ao salvar código no arquivo {filename}: {e}")

    def generate_unique_code(self):
        """Gera um código único para identificação"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
            # Verificar se o código já existe no arquivo
            if os.path.exists('data/codigo_doacao.json'):
                try:
                    with open('data/codigo_doacao.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        codes = data.get('codes', [])
                        if not any(code_data['code'] == code for code_data in codes):
                            return code
                except:
                    return code
            else:
                return code

    def cleanup_orphaned_qr_codes(self):
        """Remove QR Codes órfãos que não estão mais referenciados no arquivo JSON"""
        try:
            # Obter lista de códigos válidos do arquivo JSON
            valid_qr_files = set()
            if os.path.exists('data/codigo_doacao.json'):
                with open('data/codigo_doacao.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    codes = data.get('codes', [])
                    for code_data in codes:
                        if 'qr_code_filename' in code_data:
                            valid_qr_files.add(code_data['qr_code_filename'])
            
            # Verificar arquivos na pasta qrcodes
            qr_folder = "qrcodes"
            if os.path.exists(qr_folder):
                for filename in os.listdir(qr_folder):
                    if filename.endswith('.png'):
                        file_path = os.path.join(qr_folder, filename)
                        if file_path not in valid_qr_files:
                            try:
                                os.remove(file_path)
                                print(f"DEBUG: QR Code órfão removido: {file_path}")
                            except Exception as e:
                                print(f"ERRO ao remover QR Code órfão {file_path}: {e}")
                                
        except Exception as e:
            print(f"ERRO ao limpar QR Codes órfãos: {e}")

    async def update_payment_panel(self, user_id, code, status):
        """Atualiza o painel de pagamento quando o status muda"""
        try:
            if status == "confirmed":
                print(f"✅ Painel atualizado: Pagamento confirmado para código {code}")
                # A atualização real será feita no bot.py para evitar importações circulares
                
        except Exception as e:
            print(f"ERRO ao atualizar painel para usuário {user_id}: {e}")

    async def notify_payment_completed(self, user_id, code):
        """Notifica o usuário que o pagamento foi confirmado e faz deploy automaticamente"""
        try:
            print(f"✅ Pagamento confirmado para usuário {user_id}. Fazendo deploy automático...")
            
            # Em vez de importar diretamente, vamos usar uma abordagem assíncrona
            # O bot.py irá chamar esta função quando necessário
            # Por enquanto, apenas logamos a confirmação
            print(f"🔄 Deploy automático será processado pelo bot principal para usuário {user_id}")
            
        except Exception as e:
            print(f"ERRO ao notificar usuário {user_id}: {e}")

    def _notify_payment_completed(self, payment_id):
        """Notifica quando um pagamento é confirmado automaticamente"""
        payment = self.payments[payment_id]
        user_id = payment['user_id']
        amount = payment['amount']
        
        print(f"🎉 Pagamento confirmado automaticamente!")
        print(f"   User ID: {user_id}")
        print(f"   Amount: R$ {amount:.2f}")
        print(f"   Payment ID: {payment_id}")
        
        # Aqui você pode adicionar notificação via Discord se necessário
        # Por exemplo, enviar DM para o usuário ou notificar em um canal específico 

def get_confirmed_payments():
    """Obtém e limpa a lista de pagamentos confirmados"""
    global confirmed_payments
    payments = confirmed_payments.copy()
    confirmed_payments.clear()
    return payments 