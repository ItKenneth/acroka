import os
import random
import string
import subprocess
import asyncio
import psutil
import platform
from telethon import TelegramClient, events
from datetime import datetime, timedelta

# Конфигурация
API_ID = '24755102'  # Замените на ваш API_ID
API_HASH = 'fb23dc1caeb3349abb5e0ebcdafc0bcf'  # Замените на ваш API_HASH
TOKEN_FILE = 'bottoken.txt'  
INFO_FILE = 'userinfo.txt'  # Файл для хранения информации о пользователе

# Создаем клиента для вашего userbot
client = TelegramClient('userbot', API_ID, API_HASH)

class DeferredMessage:
    def __init__(self, client):
        self.client = client
        self.interval = 3600  # По умолчанию, 1 час
        self.message_count = 10  # По умолчанию, 10 сообщений

    async def отложка(self, event):
        """Используй .отложка <количество> <период> <текст> для планирования отправки сообщений"""
        args = event.message.message.split(' ', 3)  # Разделяем сообщение на части

        if len(args) < 4:
            await event.reply("❗ Пожалуйста, укажите количество сообщений, период (в минутах) и текст в формате: <количество> <период> <текст>")
            return
        
        try:
            self.message_count = int(args[1].strip())
            self.interval = int(args[2].strip()) * 60  # Конвертируем минуты в секунды
        except ValueError:
            await event.reply("❌ Пожалуйста, укажите корректные числовые значения для количества и периода.")
            return
        
        text = args[3].strip()
        
        if not text:
            await event.reply("✋ Пожалуйста, укажите текст сообщения.")
            return

        await event.reply("✅ Сообщения успешно запланированы!")

        chat_id = event.chat_id
        
        for i in range(self.message_count):
            send_time = datetime.now() + timedelta(seconds=self.interval * i)
            await self.client.send_message(chat_id, text, schedule=send_time)

        final_message = (f"📅 Запланировано отправить {self.message_count} сообщений с интервалом в {self.interval // 60} минут(ы).\n"
                         f"🛠️ Made with love")

        await self.client.send_message(chat_id, final_message)

# Создаем экземпляр класса отложенных сообщений
deferred_message = DeferredMessage(client)

@client.on(events.NewMessage(pattern=r'\.отложка'))
async def handler(event):
    await deferred_message.отложка(event)
    

class ChatCounter:
    """Считывает и сортирует все чаты в Telegram: личные чаты, группы, каналы и боты"""

    strings = {
        "personal_chats": "👤 Личные чаты: {}",
        "groups": "👥 Группы: {}",
        "channels": "📡 Каналы: {}",
        "bots": "🤖 Боты: {}",
        "total": "📊 Всего чатов найдено: {}",
        "estimate_time": "⏳ Время подсчета: {:.2f} секунд",
        "calculating": "🔄 Идет расчет...",
        "no_chats": "❌ Чаты не найдены.",
        "error": "⚠️ Произошла ошибка: {}"
    }

    def __init__(self, client):
        self.client = client

    async def count_chats(self, event):
        """Вспомогательная функция для подсчета всех чатов."""
        
        # Инициализация счетчиков
        total_chats = personal_chats = groups = channels = bots = 0

        start_time = time.time()
        await event.reply(self.strings["calculating"])

        try:
            async for dialog in self.client.iter_dialogs():
                total_chats += 1
                if dialog.is_user:
                    personal_chats += 1
                elif dialog.is_group:
                    groups += 1
                elif dialog.is_channel:
                    channels += 1
                elif getattr(dialog.entity, 'bot', False):
                    bots += 1

            if total_chats == 0:
                await event.reply(self.strings["no_chats"])
                return

            elapsed_time = time.time() - start_time

            final_response = (
                "📋 Результаты подсчета:\n\n"
                f"{self.strings['personal_chats'].format(personal_chats)}\n"
                f"{self.strings['groups'].format(groups)}\n"
                f"{self.strings['channels'].format(channels)}\n"
                f"{self.strings['bots'].format(bots)}\n"
                f"{self.strings['total'].format(total_chats)}\n"
                f"{self.strings['estimate_time'].format(elapsed_time)}"
            )

            await event.reply(final_response)

        except FloodWaitError as e:
            await event.reply(f"⚠️ Превышено время ожидания: {str(e)} секунд. Пожалуйста, подождите.")
        except Exception as e:
            await event.reply(self.strings["error"].format(str(e)))

    @classmethod
    def register(cls, client):
        """Метод для регистрации обработчика события"""
        
        chat_counter = cls(client)

        @client.on(events.NewMessage(pattern=r'\.countchats', incoming=True))
        async def handler(event):
            """Обработчик команды .countchats"""
            await chat_counter.count_chats(event)
    

def get_system_info():
    """Получает информацию о системе."""
    system_info = {}

    if platform.system() == "Windows":
        try:
            memory = str(subprocess.check_output(["wmic", "os", "get", "FreePhysicalMemory"])).strip()
            system_info["memory"] = f"Свободная память: {memory} KB"
        except Exception:
            system_info["memory"] = "Не удалось получить информацию о памяти."

        try:
            system_info["cpu_load"] = f"Нагрузка процессора: {psutil.cpu_percent(interval=1)}%"
        except Exception:
            system_info["cpu_load"] = "Не удалось получить информацию о нагрузке процессора."

        try:
            system_info["disk_usage"] = "Использование диска: {}%".format(psutil.disk_usage('C:/').percent)
        except Exception:
            system_info["disk_usage"] = "Не удалось получить информацию о загрузке диска."

    elif platform.system() == "Linux":
        try:
            system_info["memory"] = "Использовано: {}/{}".format(psutil.virtual_memory().used,
                                                                 psutil.virtual_memory().total)
        except Exception:
            system_info["memory"] = "Не удалось получить информацию о памяти."

        try:
            system_info["cpu_load"] = "Нагрузка процессора: {}".format(psutil.cpu_percent(interval=1)) + "%"
        except Exception:
            system_info["cpu_load"] = "Не удалось получить информацию о нагрузке процессора."

        try:
            system_info["disk_usage"] = "Использование диска: {}/{}".format(psutil.disk_usage('/').used,
                                                                           psutil.disk_usage('/').total)
        except Exception:
            system_info["disk_usage"] = "Не удалось получить информацию о загрузке диска."

    else:
        system_info["memory"] = "Информация о памяти недоступна."
        system_info["cpu_load"] = "Информация о нагрузке процессора недоступна."
        system_info["disk_usage"] = "Информация о загрузке диска недоступна."

    return system_info

def load_user_info():
    """Загружает информацию о пользователе из файла."""
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, 'r') as f:
            return f.read().strip()
    return None     

@client.on(events.NewMessage(pattern=r'\.info'))
async def info_handler(event):
    """Обработчик команды .info"""
    user_info = load_user_info() or "Не задана информация."
    system_info = get_system_info()
    
    user = await client.get_me()
    owner_name = user.first_name or "Неизвестный"

    # Формируем текст информации
    info_text = "\n".join([
        f"Владелец: {owner_name}",
        f"Информация о пользователе: {user_info}",
        system_info['memory'],
        system_info['cpu_load'],
        system_info['disk_usage']
    ])
    await event.edit(f"Информация об устройстве:\n{info_text}")

@client.on(events.NewMessage(pattern=r'\.setinfo (.+)'))
async def set_info_handler(event):
    """Обработчик команды .setinfo"""
    user_info = event.pattern_match.group(1)
    
    if user_info:
        with open(INFO_FILE, 'w') as f:
            f.write(user_info)
        await event.edit("Информация успешно сохранена!\n\n"
                         "Теперь вы можете использовать команду .info для просмотра информации.")
    else:
        await event.edit("Пожалуйста, укажите информацию для сохранения.")

@client.on(events.NewMessage(pattern=r'\.ping'))
async def ping_handler(event):
    """Обработчик команды .ping"""
    process = subprocess.Popen(['ping', '-c', '1', 'google.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        result = "✅ Пинг к Google: Время: {}мс".format(stdout.decode().split('time=')[1].split(' ')[0])
    else:
        result = "❌ Ошибка пинга!"

    await event.edit(result)

def generate_username():
    """Генерирует случайное имя пользователя для бота, заканчивающееся на _bot."""
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    return f'acroka_{random_part}_bot'

async def create_bot():
    """Создает нового бота через BotFather и сохраняет токен в файле."""
    botfather = await client.get_input_entity('BotFather')
    bot_title = 'Acroka'

    print("Отправка команды /newbot")
    await client.send_message(botfather, '/newbot')
    await asyncio.sleep(2)

    print("Отправка названия бота")
    await client.send_message(botfather, bot_title)
    await asyncio.sleep(2)

    username = generate_username()
    print("Отправка имени пользователя:", username)
    await client.send_message(botfather, username)
    await asyncio.sleep(5)

    print("Ожидание ответа от BotFather...")
    async for message in client.iter_messages(botfather, limit=10):
        if 'Use this token to access the HTTP API:' in message.message:
            print("Сообщение получено от BotFather:", message.message)

            lines = message.message.split('\n')
            for i, line in enumerate(lines):
                if 'Use this token to access the HTTP API:' in line:
                    if i + 1 < len(lines):
                        token = lines[i + 1].strip()
                        print(f"Извлеченный токен: {token}")
                        break
            else:
                print("Не удалось извлечь токен.")
                return None, None
            break
    else:
        print("Сообщение с токеном от BotFather не получено.")
        return None, None

    user_id = token.split(':')[0]
    with open(TOKEN_FILE, 'w') as f:
        f.write(f"{username}:{user_id}:{token}")
    
    print(f"Новый токен сохранен в {TOKEN_FILE}: {username}:{user_id}:{token}")
    return username, user_id, token

async def run_bot(token):
    """Запускает созданного бота с использованием токена."""
    bot_client = TelegramClient('bot', API_ID, API_HASH)

    await bot_client.start(bot_token=token)

    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        """Обрабатывает команду /start и отвечает на неё."""
        await event.reply('Hello! Меня зовут Acroka я userbot!\n\nДля просмотра основных команд используй .help')

    await bot_client.run_until_disconnected()

async def main():
    """Основная функция."""
    print("Запуск основной функции.")
    
    try:
        await client.start()
        print("Успешно авторизовались.")
    except Exception as e:
        print("Ошибка авторизации:", e)
        return

    # Проверяем существование токена
    if not os.path.exists(TOKEN_FILE) or os.stat(TOKEN_FILE).st_size == 0:
        print("Создание нового токена бота.")
        username, user_id, token = await create_bot()
        
        if token:
            await asyncio.sleep(5)  # Подождите немного для старта бота
        else:
            print("Ошибка: не удалось получить токен для вашего бота.")
            return
    else:
        print("Загрузка существующего токена...")
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = f.read().strip()
                username, user_id, token = data.split(':', 2)
        except ValueError:
            print("Ошибка: неправильный формат данных в файле. Убедитесь, что он в формате username:user_id:token.")
            return

    # Запускаем бота в отдельной корутине
    bot_running = asyncio.create_task(run_bot(token))

    await asyncio.sleep(3)  # Дайте время боту запуститься
    
    # Теперь отправляем команду /start боту
    await client.send_message(f'@{username}', '/start')  # Отправка команды /start боту

    await bot_running  # Дождитесь завершения выполнения бота

if __name__ == '__main__':
    asyncio.run(main())
