from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, Message,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.filters import Command
from aiogram import Router


router = Router()

@router.message(Command('next'))
async def cmd_next(message: Message):
    kb = [
        [KeyboardButton(text='Главное меню')],
        [KeyboardButton(text='Добавить задачу')],
        [KeyboardButton(text='Список задач')],
        [KeyboardButton(text='Задачи на сегодня')]
    ]

    keyboard = ReplyKeyboardMarkup(keyboard = kb, resize_keyboard = True, input_field_placeholder = 'Выберите пункт меню...')
    await message.answer('Выберите желаемое действие: ', reply_markup = keyboard)

all_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить задачу', callback_data = 'add task')],
    [InlineKeyboardButton(text='Список задач', callback_data = 'list task')],
    [InlineKeyboardButton(text='Задачи на сегодня', callback_data = 'task on today')],
    [InlineKeyboardButton(text='Категории задач', callback_data = 'category task')],
    [InlineKeyboardButton(text='Статистика', callback_data = 'stats')]
])

back_to_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🏠 Назад в меню', callback_data= 'back_to_menu')]
])

back_in_task_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data= 'back_in_task')],
    [InlineKeyboardButton(text='🏠 Назад в меню', callback_data= 'back_to_menu')]
])

confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Сохранить', callback_data= 'save_task')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data= 'back_in_task')],
    [InlineKeyboardButton(text='❌ Отменить', callback_data= 'back_to_menu')]
])

category_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_category')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_in_task')],
    [InlineKeyboardButton(text='🏠 В меню', callback_data='back_to_menu')]
])

deadline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_deadline')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_in_task')],
    [InlineKeyboardButton(text='🏠 В меню', callback_data='back_to_menu')]
])

priority_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚪ Низкий', callback_data='priority_low')],
    [InlineKeyboardButton(text='🟡 Средний', callback_data='priority_medium')],
    [InlineKeyboardButton(text='🔴 Высокий', callback_data='priority_high')],
    [InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_priority')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_in_task')],
    [InlineKeyboardButton(text='🏠 В меню', callback_data='back_to_menu')]
])

categories_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📁 Показать все категории', callback_data='show_categories')],
        [InlineKeyboardButton(text='➕ Создать категорию', callback_data='create_category')],
        [InlineKeyboardButton(text='🏠 Назад в меню', callback_data='back_to_menu')],
        [InlineKeyboardButton(text='🗑️ Удалить категорию', callback_data='delete_category')]
])