from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from bot.keyboards import (all_info, back_to_menu_kb, back_in_task_kb,
                           confirm_kb, category_kb, deadline_kb,
                           priority_kb, categories_kb)
from database.requests import (get_or_create_user, create_task,
                               get_user_tasks, get_tasks_for_today,
                               get_statistics, get_user_categories,
                               create_category, complete_task, delete_task, get_tasks_by_category)

from datetime import datetime

router = Router()

#СТАРТОВЫЕ ОБРАБОТЧИКИ (start, help)
##################################################################################################

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("""
🚀  UnderCtrl — ваш персональный помощник по задачам!

Я помогу организовать дела, установить сроки и распределить задачи по категориям и приоритетам.

  Что вы можете сделать:
• 📝 Создавать задачи с дедлайнами
• 🏷️ Сортировать по категориям
• ⭐ Выставлять приоритеты
• 📊 Смотреть статистику
• ✏️ Удалять задачи и приоритеты

Начните с команды /next или 
посмотрите /help для основных возможностей!
    """)


@router.message(Command('help'))
async def cmd_help(message: Message):
    sent_message = await message.answer("""
⭐ Основные команды:

◎ /next - Быстрое начало работы
◎ /help - Справка""", reply_markup=all_info)

    global help_message_id
    help_message_id = sent_message.message_id

##################################################################################################

#КЛАССЫ ДЛЯ СОСТОЯНИЙ
##################################################################################################

class CreateTask(StatesGroup):
    name = State()
    description = State()
    category = State()
    priority = State()
    deadline = State()
    confirmation = State()

class CategoryActions(StatesGroup):
    waiting_for_category_name = State()
    choosing_category = State()

##################################################################################################

#3 НИЖНИЕ КНОПКИ ПОД КЛАВИАТУРОЙ
##################################################################################################

@router.message(F.text == 'Главное меню')
async def main_menu_button(message: Message):
    await message.answer(
        '🚀 Главное меню UnderCtrl\n\n'
        'Выберите действие:', reply_markup=all_info)

@router.message(F.text == 'Добавить задачу')
async def add_tasks_button(message: Message, state: FSMContext):
    await state.set_state(CreateTask.name)
    await message.answer('Введите название задачи: ', reply_markup=back_in_task_kb)

@router.message(F.text == 'Список задач')
async def list_tasks(message: Message):
    tasks = await get_user_tasks(message.from_user.id, completed=False)

    if not tasks:
        await message.answer('📭 Нет активных задач!')
        return

    message_text = format_tasks_list(tasks)
    await message.answer(message_text)

def format_tasks_list(tasks):
    priority_emojis = {
        1: '⚪ Низкий',
        2: '🟡 Средний',
        3: '🔴 Высокий'
    }

    text = "📋 Ваши задачи:\n\n"

    for index, task in enumerate(tasks, start=1):
        deadline = task.deadline.strftime('%d.%m.%Y %H:%M') if task.deadline else 'без срока'
        category = f"🏷️ {task.category}\n" if task.category else ""
        priority = priority_emojis.get(task.priority, '⚪ Низкий')

        text += (
            f"ID: {index}\n"
            f"📝 {task.name}\n"
            f"📄 {task.description or 'Без описания'}\n"
            f"{category}"
            f"📊 {priority}\n"
            f"⏰ Дедлайн: {deadline}\n"
            f"────────────────────\n"
        )

    text += (
        "\n📝 Команды:\n"
        "/done <ID> — отметить как выполненную\n"
        "/delete <ID> — удалить задачу\n"
        "Пример: /done 1"
    )

    return text

@router.message(F.text == 'Задачи на сегодня')
async def tasks_on_today(message: Message):
    tasks = await get_tasks_for_today(message.from_user.id)

    if not tasks:
        await message.answer('🎉 На сегодня задач нет!')
        return

    message_text = "📅 Задачи на сегодня:\n\n"
    priority_emojis = {1: '⚪', 2: '🟡', 3: '🔴'}

    for task in tasks:
        if task.deadline:
            time_str = task.deadline.strftime('%H:%M')
            deadline_info = f"⏰ {time_str}"
        else:
            deadline_info = ""

        priority_emoji = priority_emojis.get(task.priority, '⚪')
        category_text = f"🏷️ {task.category}" if task.category else ""

        message_text += (
            f"{priority_emoji} {task.name}\n"
            f"{deadline_info} {category_text}\n"
            f"{task.description}\n"
            f"────────────────────\n")

    await message.answer(message_text)

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ВОЗВРАТА В МЕНЮ
##################################################################################################

@router.callback_query(F.data == 'back_to_menu')
async def back_inline(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await callback.message.answer('Главное меню: ', reply_markup=all_info)
    await callback.answer()

##################################################################################################

#ОБРАБОТЧИК СОСТОЯНИЙ ДЛЯ ВОЗВРАТА ШАГОВ НАЗАД ПРИ СОЗДАНИИ ЗАДАЧИ
##################################################################################################

@router.callback_query(F.data == 'back_in_task')
async def back_in_task_handler(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state == CreateTask.confirmation.state:
        await state.set_state(CreateTask.deadline)
        await callback.message.answer(
            'Введите ограничение по времени для задачи в формате ДД-ММ-ГГГГ ЧЧ:ММ:СС\n'
            'или нажмите пропустить: ',
            reply_markup=deadline_kb)

    elif current_state == CreateTask.deadline.state:
        await state.set_state(CreateTask.priority)
        await callback.message.answer(
            '📊 Выберите приоритет задачи:',
            reply_markup=priority_kb
        )

    if current_state == CreateTask.priority.state:
        await state.set_state(CreateTask.category)
        await callback.message.answer('Введите название категории, или нажмите пропустить', reply_markup=category_kb)

    elif current_state == CreateTask.category.state:
        await state.set_state(CreateTask.description)
        await callback.message.answer('Введите описание задачи:', reply_markup=back_in_task_kb)

    elif current_state == CreateTask.description.state:
        await state.set_state(CreateTask.name)
        await callback.message.answer('Введите название задачи:', reply_markup=back_in_task_kb)

    elif current_state == CreateTask.name.state:
        await state.clear()
        await callback.message.answer('❌ Создание задачи отменено', reply_markup=all_info)
        await callback.answer()

##################################################################################################

#ЭТОТ ОБРАБОТЧИК ВЫВОДИТ СООБЩЕНИЕ ПОСЛЕ СОХРАНЕНИЕ ЗАДАЧИ С УКАЗАНИЕМ ЕЕ ID
##################################################################################################
@router.callback_query(F.data == 'save_task')
async def save_task_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    deadline_str = data.get('deadline')
    deadline = None
    if deadline_str and deadline_str != "не установлен":
        try:
            deadline = datetime.strptime(deadline_str, '%d-%m-%Y %H:%M:%S')
        except:
            pass

    task = await create_task(
        tg_id=callback.from_user.id,
        name=data.get('name'),
        description=data.get('description'),
        category=data.get('category'),
        priority=data.get('priority', 2),
        deadline=deadline
    )

    await state.clear()
    await callback.message.answer(f"✅ Задача успешно сохранена: \n ID: {task.id}", reply_markup=all_info)
    await callback.answer()

##################################################################################################

#В ЭТОЙ ЧАСТИ ВСЕ ОБРАБОТЧИКИ ДЛЯ ПРОЦЕССА СОЗДАНИЯ ЗАДАЧ, С ИХ ВНУТРЕННИМИ ИНЛАЙН КНОПКАМИ ДЛЯ СКИПА ВЫБОРА
##################################################################################################
@router.callback_query(F.data == 'add task')
async def add_tasks_inline(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await state.set_state(CreateTask.name)
    await callback.message.answer('Введите название задачи: ', reply_markup=back_in_task_kb, show_alert=True)
    await callback.answer()


@router.message(CreateTask.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateTask.description)
    await message.answer('Введите описание задачи: ', reply_markup=back_in_task_kb)


@router.message(CreateTask.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    categories = await get_user_categories(message.from_user.id)

    categories_text = ""
    if categories:
        categories_text = "\n\n📁 Ваши категории:\n" + "\n".join(f"• {cat}" for cat in categories[:5])
        if len(categories) > 5:
            categories_text += f"\n... и еще {len(categories) - 5}"

    await state.set_state(CreateTask.category)
    await message.answer(
        f'Введите название категории, или нажмите "Пропустить":{categories_text}',
        reply_markup=category_kb)

@router.callback_query(F.data == 'skip_category')
async def skip_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    if current_state != CreateTask.category.state:
        return

    await state.update_data(category=None)
    await state.set_state(CreateTask.priority)
    await callback.message.answer('📊 Выберите приоритет задачи:', reply_markup=priority_kb)

@router.message(CreateTask.category)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(CreateTask.priority)
    await message.answer('📊 Выберите приоритет задачи:', reply_markup=priority_kb)


@router.callback_query(F.data.startswith('priority_'))
async def set_priority(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    if current_state != CreateTask.priority.state:
        return

    priority_data = callback.data.split('_')[1]
    priority_map = {
        'low': {'emoji': '⚪', 'text': 'Низкий', 'value': 1},
        'medium': {'emoji': '🟡', 'text': 'Средний', 'value': 2},
        'high': {'emoji': '🔴', 'text': 'Высокий', 'value': 3}
    }

    priority_info = priority_map[priority_data]

    await state.update_data(
        priority=priority_info['value'],
        priority_emoji=priority_info['emoji'],
        priority_text=priority_info['text']
    )

    await state.set_state(CreateTask.deadline)
    await callback.message.answer(
        '⏰ Введите дедлайн в формате ДД-ММ-ГГГГ ЧЧ:ММ:СС\n'
        'или нажмите "Пропустить":',
        reply_markup=deadline_kb
    )


@router.callback_query(F.data == 'skip_priority')
async def skip_priority(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    if current_state != CreateTask.priority.state:
        return

    await state.update_data(
        priority=2,
        priority_emoji='🟡',
        priority_text='Средний (по умолчанию)'
    )

    await state.set_state(CreateTask.deadline)
    await callback.message.answer(
        '⏰ Введите дедлайн в формате ДД-ММ-ГГГГ ЧЧ:ММ:СС\n'
        'или нажмите "Пропустить":',
        reply_markup=deadline_kb
    )


@router.message(CreateTask.deadline)
async def add_deadline(message: Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await show_confirmation(message, state)


@router.callback_query(F.data == 'skip_deadline')
async def skip_deadline(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    if current_state != CreateTask.deadline.state:
        return

    await state.update_data(deadline=None)
    await show_confirmation(callback.message, state)

##################################################################################################

#ФУНКЦИЯ, КОТОРАЯ ВЫВОДИТ ВВЕДЕННЫЕ ДАННЫЕ ДЛЯ ЗАДАЧИ ПЕРЕД ЕЕ СОХРАНЕНИЕМ
##################################################################################################
async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(CreateTask.confirmation)

    category_text = data.get("category", "не указана")
    if category_text is None:
        category_text = "не указана"

    deadline_text = data.get("deadline", "не установлен")
    if deadline_text is None:
        deadline_text = "не установлен"

    priority_emoji = data.get("priority_emoji", "⚪")
    priority_text = data.get("priority_text", "Низкий")

    await message.answer(
        f'══════════════════════════\n'
        f'📋 ПРОВЕРКА ДАННЫХ ЗАДАЧИ\n'
        f'══════════════════════════\n\n'
        f'📝 Название: {data["name"]}\n'
        f'📄 Описание: {data.get("description", "не указано")}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'🏷️ Категория: {category_text}\n'
        f'📊 Приоритет: {priority_emoji} {priority_text}\n'
        f'⏰ Дедлайн: {deadline_text}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        f'❓ Сохранить задачу ❓',
        reply_markup=confirm_kb)

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ВЫВОДА ВСЕХ ЗАДАЧ
##################################################################################################

@router.callback_query(F.data == 'list task')
async def lists_tasks_inline(callback: CallbackQuery):
    tasks = await get_user_tasks(callback.from_user.id, completed=False)

    if not tasks:
        await callback.message.answer('📭 Нет активных задач!')
        await callback.answer()
        return

    message_text = format_tasks_list(tasks)
    await callback.message.answer(message_text)
    await callback.answer()

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ВЫВОДА ЗАДАЧ НА СЕГОДНЯ
##################################################################################################

@router.callback_query(F.data == 'task on today')
async def task_on_today_inline(callback: CallbackQuery):
    tasks = await get_tasks_for_today(callback.from_user.id)

    if not tasks:
        await callback.message.answer('🎉 На сегодня задач нет!')
        await callback.answer()
        return

    message_text = "📅 Задачи на сегодня:\n\n"
    priority_emojis = {1: '⚪', 2: '🟡', 3: '🔴'}

    for task in tasks:
        if task.deadline:
            time_str = task.deadline.strftime('%H:%M')
            deadline_info = f"⏰ {time_str}"
        else:
            deadline_info = ""

        priority_emoji = priority_emojis.get(task.priority, '⚪')
        category_text = f"🏷️ {task.category}" if task.category else ""

        message_text += (
            f"{priority_emoji} {task.name}\n"
            f"{deadline_info} {category_text}\n"
            f"{task.description}\n"
            f"────────────────────\n")

    await callback.message.answer(message_text)
    await callback.answer('📅 Задачи на сегодня')

##################################################################################################

#ОБРАБОТЧИК ИНЛАЙН КНОПКИ ДЛЯ ВЫБОРА ДЕЙСТВИЙ С ЗАДАЧАМИ
##################################################################################################

@router.callback_query(F.data == 'category task')
async def category_inline(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        '🏷️ Управление категориями:\n\n'
        'Выберите действие:', reply_markup=categories_kb)
    await callback.answer()

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ПРОСМОТРА СОХРАНЕННЫХ КАТЕГОРИЙ
##################################################################################################

@router.callback_query(F.data == 'show_categories')
async def show_categories_handler(callback: CallbackQuery):
    categories = await get_user_categories(callback.from_user.id)

    if not categories:
        await callback.message.answer('📭 У вас пока нет категорий!')
        await callback.answer()
        return

    message_text = "📁 Ваши категории:\n\n"

    for category_name in categories:
        tasks = await get_tasks_by_category(callback.from_user.id, category_name)
        count = len(tasks)

        message_text += f"• {category_name} ({count} задач)\n"

    await callback.message.answer(message_text)
    await callback.answer()

##################################################################################################

#ОБРАБОТЧИКИ ДЛЯ СОЗДАНИЯ КАТЕГОРИЙ
##################################################################################################

@router.callback_query(F.data == 'create_category')
async def create_category_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryActions.waiting_for_category_name)

    await callback.message.answer('➕ Создание категории\n\n'
        'Введите название новой категории:', reply_markup=back_to_menu_kb)
    await callback.answer()


@router.message(CategoryActions.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    category_name = message.text.strip()

    if len(category_name) > 50:
        await message.answer('❌ Название категории слишком длинное (макс. 50 символов)')
        return

    category = await create_category(message.from_user.id, category_name)

    if category is None:
        await message.answer(f'❌ Категория "{category_name}" уже существует!')
    else:
        await message.answer(f'✅ Категория "{category_name}" успешно создана!\n\n'
                             f'Теперь при создании задач вы сможете выбрать эту категорию.')

    await state.clear()

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ПОМЕТКИ ЗАДАЧИ КАК ВЫПОЛНЕННОЙ
##################################################################################################

@router.message(F.text.startswith('/done'))
async def mark_task_done(message: Message):
    try:
        local_id = int(message.text.split()[1])
        tasks = await get_user_tasks(message.from_user.id, completed=False)

        if local_id < 1 or local_id > len(tasks):
            await message.answer("❌ Неверный ID задачи")
            return

        task = tasks[local_id - 1]
        await complete_task(message.from_user.id, task.id)

        await message.answer(f"✅ Задача «{task.name}» отмечена как выполненная!")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /done <ID>\nПример: /done 1")

##################################################################################################

#ОБРАБОТЧИК ДЛЯ УДАЛЕНИЯ ЗАДАЧИ
##################################################################################################

@router.message(F.text.startswith('/delete'))
async def delete_task_handler(message: Message):
    try:
        local_id = int(message.text.split()[1])
        tasks = await get_user_tasks(message.from_user.id, completed=False)

        if local_id < 1 or local_id > len(tasks):
            await message.answer("❌ Неверный ID задачи")
            return

        task = tasks[local_id - 1]
        await delete_task(message.from_user.id, task.id)

        await message.answer(f"🗑️ Задача «{task.name}» удалена!")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /delete <ID>\nПример: /delete 1")

##################################################################################################

#ОБРАБОТЧИК ДЛЯ УДАЛЕНИЯ (НО ОН ПОКА НЕ РЕАЛИЗОВАН)
##################################################################################################

@router.callback_query(F.data == 'delete_category')
async def delete_category_handler(callback: CallbackQuery):
    await callback.message.answer(
        "🗑️ Удаление категорий:\n\n"
        "К сожалению, функционал удаления категорий временно недоступен.\n"
        "Вы можете игнорировать ненужные категории при создании задач.\n\n"
        "В будущих версиях эта функция будет добавлена!", reply_markup=categories_kb)
    await callback.answer()

##################################################################################################

#ОБРАБОТЧИК ДЛЯ ПРОСМОТРА СТАТИСТИКИ
##################################################################################################

@router.callback_query(F.data == 'stats')
async def stats_inline(callback: CallbackQuery):
    stats = await get_statistics(callback.from_user.id)

    message_text = (
        f"📊 Статистика:\n\n"
        f"📈 Всего задач: {stats['total']}\n"
        f"✅ Выполнено: {stats['completed']}\n"
        f"⏳ Активных: {stats['active']}\n"
        f"🔴 Высокий приоритет: {stats['priorities'].get(3, 0)}\n"
        f"🟡 Средний: {stats['priorities'].get(2, 0)}\n"
        f"⚪ Низкий: {stats['priorities'].get(1, 0)}"
    )
    await callback.message.answer(message_text)
    await callback.answer()

##################################################################################################