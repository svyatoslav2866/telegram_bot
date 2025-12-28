import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from datetime import datetime

from bot.handlers import (cmd_start, cmd_help, format_tasks_list,mark_task_done,
    delete_task_handler, main_menu_button, list_tasks, process_category_name,
    tasks_on_today, stats_inline, back_in_task_handler, CreateTask)

@pytest.fixture
def test_message():
    message = AsyncMock()
    message.answer = AsyncMock()
    message.from_user.id = 12345
    return message


@pytest.fixture
def test_task():
    return SimpleNamespace(
        id=1,
        name="Сдать курсовую",
        description="Уже наконец-то",
        category="Учёба",
        priority=3,
        deadline=None
    )


@pytest.mark.asyncio
async def test_cmd_start_sends_welcome_message(test_message):
    await cmd_start(test_message)

    test_message.answer.assert_called_once()
    assert "UnderCtrl" in test_message.answer.call_args.args[0]


@pytest.mark.asyncio
async def test_cmd_help_sends_help_message(test_message):
    await cmd_help(test_message)

    test_message.answer.assert_called_once()
    assert "Основные команды" in test_message.answer.call_args.args[0]


def test_format_tasks_list_single_task(test_task):
    result = format_tasks_list([test_task])

    assert "Сдать курсовую" in result
    assert "Учёба" in result
    assert "Высокий" in result
    assert "Ваши задачи" in result

@pytest.mark.asyncio
async def test_mark_task_done_success(test_message, test_task):

    test_message.text = "/done 1"

    with patch("bot.handlers.get_user_tasks", return_value=[test_task]), \
         patch("bot.handlers.complete_task", new_callable=AsyncMock):

        await mark_task_done(test_message)

        test_message.answer.assert_called_once()
        assert "отмечена как выполненная" in test_message.answer.call_args.args[0]


@pytest.mark.asyncio
async def test_mark_task_done_invalid_id(test_message):
    test_message.text = "/done 999"

    with patch("bot.handlers.get_user_tasks", return_value=[]):
        await mark_task_done(test_message)

        test_message.answer.assert_called_once()
        assert "Неверный ID" in test_message.answer.call_args.args[0]


@pytest.mark.asyncio
async def test_delete_task_success(test_message, test_task):
    test_message.text = "/delete 1"

    with patch("bot.handlers.get_user_tasks", return_value=[test_task]), \
         patch("bot.handlers.delete_task", new_callable=AsyncMock):

        await delete_task_handler(test_message)

        test_message.answer.assert_called_once()
        assert "удалена" in test_message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_delete_wrong_id(test_message):
    test_message.text = "/delete 5"

    with patch("bot.handlers.get_user_tasks", return_value=[]):
        await delete_task_handler(test_message)

        test_message.answer.assert_called_once()
        assert "Неверный ID задачи" in test_message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_delete_task_invalid_format(test_message):
    test_message.text = "/delete"

    await delete_task_handler(test_message)

    test_message.answer.assert_called_once()
    assert "Использование" in test_message.answer.call_args.args[0]

def test_format_tasks_list_with_deadline():
    task = SimpleNamespace(
        id=1,
        name="Дедлайн тест",
        description="Описание",
        category=None,
        priority=2,
        deadline=datetime(2025, 1, 1, 12, 0)
    )

    result = format_tasks_list([task])

    assert "01.01.2025 12:00" in result

@pytest.mark.asyncio
async def test_main_menu_button(test_message):
    test_message.text = "Главное меню"

    await main_menu_button(test_message)

    test_message.answer.assert_called_once()
    assert "Главное меню UnderCtrl" in test_message.answer.call_args.args[0]


@pytest.mark.asyncio
async def test_list_tasks_empty(test_message):

    with patch("bot.handlers.get_user_tasks", return_value=[]):
        await list_tasks(test_message)

        test_message.answer.assert_called_once()
        assert "Нет активных задач" in test_message.answer.call_args.args[0]

from bot.handlers import tasks_on_today

@pytest.mark.asyncio
async def test_tasks_today_empty(test_message):

    with patch("bot.handlers.get_tasks_for_today", return_value=[]):
        await tasks_on_today(test_message)

        test_message.answer.assert_called_once()
        assert "На сегодня задач нет" in test_message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_stats_inline(test_message):

    test_callback = AsyncMock()
    test_callback.from_user.id = 123
    test_callback.message.answer = AsyncMock()
    test_callback.answer = AsyncMock()

    stats_data = {
        "total": 5,
        "completed": 2,
        "active": 3,
        "priorities": {1: 1, 2: 1, 3: 1}
    }

    with patch("bot.handlers.get_statistics", return_value=stats_data):
        await stats_inline(test_callback)

        test_callback.message.answer.assert_called_once()
        assert "Всего задач" in test_callback.message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_cancel_task_creation(test_message):

    test_callback = AsyncMock()
    test_callback.data = "back_in_task"
    test_callback.message.answer = AsyncMock()
    test_callback.answer = AsyncMock()

    test_state = AsyncMock()
    test_state.get_state.return_value = CreateTask.name.state

    await back_in_task_handler(test_callback, test_state)

    test_callback.message.answer.assert_called_once()
    assert "Создание задачи отменено" in test_callback.message.answer.call_args.args[0]

@pytest.mark.asyncio
async def test_category_already_exists(test_message):

    test_message.text = "Учеба"
    test_message.from_user.id = 1
    state = AsyncMock()

    with patch("bot.handlers.create_category", return_value=None):
        await process_category_name(test_message, state)

        test_message.answer.assert_called_once()
        assert "уже существует" in test_message.answer.call_args.args[0]

