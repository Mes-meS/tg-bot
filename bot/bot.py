import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Берём токен из переменных окружения (их укажете в панели)
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

# Ваши паки (оставляем как есть)
PAKS = {
    "pak1": ("marin(472)", "https://t.me/+_HeIkzWyoWAzZTgy", 350),
    "pak2": ("haruhi_suzumiya(111)", "https://t.me/+QgREEpJi0t1jZDVi", 100),
}

pending = {}
user_purchases = {}  # {user_id: [{"name": "pak1", "link": "url"}, ...]}
async def start(update: Update, context):
    keyboard = []
    for pak_id, (name, link, price) in PAKS.items():
        keyboard.append([InlineKeyboardButton(f"{name} - {price}₽", callback_data=pak_id)])
    await update.message.reply_text(
        "Добро пожаловать в магазин паков!\n\nВыбери пак для покупки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu(update: Update, context):
    """Команда /menu - показывает меню с товарами"""
    keyboard = []
    for pak_id, (name, link, price) in PAKS.items():
        keyboard.append([InlineKeyboardButton(f"{name} - {price}₽", callback_data=pak_id)])
    await update.message.reply_text(
        "🏠 Меню магазина:\n\nВыбери пак для покупки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy(update: Update, context):
    query = update.callback_query
    await query.answer()
    pak_id = query.data
    "buy_"
    name, link, price = PAKS[pak_id]
    pending[query.from_user.id] = pak_id
    keyboard = [[InlineKeyboardButton("✅ Я оплатил", callback_data="paid")]]
    await query.edit_message_text(
        f"💎 {name}\n💰 Цена: {price}₽\n\n"
        f"📌 Реквизиты:\nСбер: -\n\n"
        f"✅ После оплаты нажми кнопку и отправь чек:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def paid(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in pending:
        await query.edit_message_text("❌ Сначала выбери товар через /start")
        return
    await query.edit_message_text("📸 Отправь фото чека в этот чат")
    context.user_data['waiting'] = pending[user_id]

async def handle_photo(update: Update, context):
    if 'waiting' not in context.user_data:
        await update.message.reply_text("❌ Сначала выбери товар через /start")
        return
    
    user_id = update.message.from_user.id
    pak_id = context.user_data['waiting']
    name, link, price = PAKS[pak_id]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ДА, выдать ссылку", callback_data=f"approve_{user_id}_{pak_id}")],
        [InlineKeyboardButton("❌ НЕТ, отказать", callback_data=f"deny_{user_id}")]
    ])
    
    await update.message.forward(ADMIN_ID)
    await context.bot.send_message(
        ADMIN_ID,
        f"🧾 НОВЫЙ ЧЕК\n👤 Пользователь: {user_id}\n📦 Товар: {name}\n💰 Сумма: {price}₽",
        reply_markup=keyboard
    )
    
    await update.message.reply_text("✅ Чек отправлен администратору. Ожидай ответа.")
    del context.user_data['waiting']

async def admin_approve(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    _, user_id_str, pak_id = query.data.split("_")
    user_id = int(user_id_str)
    name, link, price = PAKS[pak_id]
    
    # Создаём кнопку "Вернуться в меню"
    menu_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="back_to_menu")],
        [InlineKeyboardButton("🛍️ Мои покупки", callback_data="my_purchases")]
    ])
    
    # Сохраняем покупку (без дублей)
if user_id not in user_purchases:
    user_purchases[user_id] = []

# Проверяем, есть ли уже такой пак
already_bought = False
for pak in user_purchases[user_id]:
    if pak['name'] == name:
        already_bought = True
        break

if not already_bought:
    user_purchases[user_id].append({"name": name, "link": link})
    
await context.bot.send_message(
        user_id,
        f"✅ ОПЛАТА ПОДТВЕРЖДЕНА!\n\n📦 Товар: {name}\n🔗 Ссылка: {link}\n\nСпасибо за покупку!",
        disable_web_page_preview=True,
        reply_markup=menu_keyboard
    )
    
    await query.edit_message_text(f"✅ ВЫДАНО пользователю {user_id}\nТовар: {name}")
async def admin_deny(update: Update, context):
    
    query = update.callback_query
    await query.answer()
    
    _, user_id_str = query.data.split("_")
    user_id = int(user_id_str)
    
    await context.bot.send_message(
        user_id,
        "❌ ОПЛАТА НЕ ПОДТВЕРЖДЕНА\n\nПроверьте чек и попробуйте снова."
    )
    
    await query.edit_message_text(f"❌ ОТКАЗАНО пользователю {user_id}")

async def back_to_menu(update: Update, context):
    """Кнопка возврата в меню"""
    query = update.callback_query
    await query.answer()
    
    # Создаём клавиатуру с товарами
    keyboard = []
    for pak_id, (name, link, price) in PAKS.items():
        keyboard.append([InlineKeyboardButton(f"{name} - {price}₽", callback_data=pak_id)])
    
    # Отправляем сообщение с меню
    await query.edit_message_text(
        "🏠 Добро пожаловать в магазин паков!\n\nВыбери пак для покупки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def my_purchases(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_purchases or not user_purchases[user_id]:
        await query.edit_message_text("❌ У вас пока нет покупок")
        return
    
    text = "📦 ВАШИ ПОКУПКИ:\n\n"
    for pak in user_purchases[user_id]:
        text += f"🔹 {pak['name']}\n🔗 {pak['link']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🛍️ Купить пак", callback_data="pak1")]]  # Или свои кнопки
    await query.edit_message_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
async def show_products(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for pak_id, (name, link, price) in PAKS.items():
        keyboard.append([InlineKeyboardButton(f"{name} - {price}₽", callback_data=f"buy_{pak_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    
    await query.edit_message_text(
        "🛍️ Выбери пак для покупки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )    
    
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(my_purchases, pattern="^my_purchases$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    # Добавляем обработчики callback-кнопок
    app.add_handler(CallbackQueryHandler(show_products, pattern="^show_products$"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(paid, pattern="^paid$"))
    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(admin_deny, pattern="^deny_"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    
    # Добавляем обработчик фото
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
