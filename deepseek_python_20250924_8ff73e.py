import os
import random
import asyncio
import sqlite3
import time
import requests
from telegram import Bot
from telegram.error import RetryAfter

# Configurações
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect('posted.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posted_files
                 (file_url TEXT PRIMARY KEY, posted_at TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

def mark_as_posted(file_url):
    """Marca uma imagem como postada"""
    conn = sqlite3.connect('posted.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO posted_files VALUES (?, ?)", 
              (file_url, time.time()))
    conn.commit()
    conn.close()

def is_already_posted(file_url):
    """Verifica se imagem já foi postada"""
    conn = sqlite3.connect('posted.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM posted_files WHERE file_url = ?", (file_url,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_random_image():
    """Obtém URL de imagem aleatória"""
    image_apis = [
        "https://picsum.photos/1200/800",
        "https://source.unsplash.com/random/1200x800",
        "https://loremflickr.com/1200/800",
        "https://placekitten.com/1200/800"
    ]
    return random.choice(image_apis)

async def download_and_send_image(bot, image_url):
    """Faz download e envia imagem"""
    try:
        print(f"📥 Baixando imagem: {image_url}")
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            filename = f"temp_image_{int(time.time())}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            with open(filename, 'rb') as photo:
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=photo,
                    caption=f"🖼️ Post automático\n⏰ {time.strftime('%d/%m/%Y %H:%M')}"
                )
            
            os.remove(filename)
            print("✅ Imagem enviada com sucesso")
            return True
        else:
            print(f"❌ Erro no download: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no envio: {e}")
        return False

async def main_poster():
    """Função principal do bot"""
    try:
        if not TOKEN or not CHAT_ID:
            print("❌ ERRO: Variáveis TG_BOT_TOKEN ou TG_CHAT_ID não configuradas")
            return
        
        bot = Bot(token=TOKEN)
        init_db()
        
        print("=" * 50)
        print("🤖 BOT INICIADO NO RENDER.COM")
        print(f"⏰ Intervalo: 2 horas")
        print(f"📊 Token: {TOKEN[:10]}...")
        print(f"💬 Chat ID: {CHAT_ID}")
        print("=" * 50)
        
        while True:
            try:
                print(f"\n🔄 Buscando nova imagem...")
                image_url = get_random_image()
                
                if not is_already_posted(image_url):
                    print(f"📸 Nova imagem encontrada: {image_url}")
                    success = await download_and_send_image(bot, image_url)
                    
                    if success:
                        mark_as_posted(image_url)
                        print(f"✅ Postagem realizada com sucesso!")
                    else:
                        print(f"❌ Falha na postagem, tentando novamente mais tarde")
                else:
                    print(f"⏭️ Imagem já postada anteriormente, buscando outra...")
                
                print(f"⏳ Próxima postagem em 2 horas...")
                for i in range(7200):
                    await asyncio.sleep(1)
                    if i % 600 == 0:
                        minutos_restantes = (7200 - i) // 60
                        print(f"⏰ Aguardando... {minutos_restantes} minutos restantes")
                
            except RetryAfter as e:
                wait_time = e.retry_after
                print(f"⏳ Rate limit do Telegram - Esperando {wait_time} segundos...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                print(f"⚠️ Erro no loop principal: {e}")
                print("🔄 Tentando novamente em 5 minutos...")
                await asyncio.sleep(300)
                
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {e}")
        print("🔁 Reiniciando em 10 segundos...")
        await asyncio.sleep(10)
        await main_poster()

if __name__ == "__main__":
    asyncio.run(main_poster())