from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc, asc
from datetime import datetime, timedelta
from database.models import User, Category, Task, async_session


async def get_or_create_user(tg_id: int, username: str = None, full_name: str = None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            user = User(tg_id=tg_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def create_task(
        tg_id: int,
        name: str,
        description: str = None,
        category: str = None,
        priority: int = 2,
        deadline: datetime = None
):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        task = Task(
            user_id=user.tg_id,
            name=name,
            description=description,
            category=category,
            priority=priority,
            deadline=deadline
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def get_user_tasks(tg_id: int, completed: bool = False, limit: int = None):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        query = select(Task).where(
            and_(Task.user_id == user.tg_id, Task.is_completed == completed)
        ).order_by(
            desc(Task.priority),
            asc(Task.deadline),
            asc(Task.id))

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


async def get_tasks_for_today(tg_id: int):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        result = await session.execute(
            select(Task).where(
                and_(
                    Task.user_id == user.tg_id,
                    Task.is_completed == False
                )
            ).order_by(desc(Task.priority), asc(Task.created_at))
        )
        tasks = result.scalars().all()

        today_tasks = []
        today = datetime.now().date()

        for task in tasks:
            if task.deadline and task.deadline.date() == today:
                today_tasks.append(task)

        return today_tasks


async def complete_task(tg_id: int, task_id: int):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        await session.execute(
            update(Task).where(
                and_(Task.id == task_id, Task.user_id == user.tg_id)
            ).values(is_completed=True, completed_at=datetime.now())
        )
        await session.commit()


async def delete_task(tg_id: int, task_id: int):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        await session.execute(
            delete(Task).where(and_(Task.id == task_id, Task.user_id == user.tg_id))
        )
        await session.commit()


async def get_statistics(tg_id: int):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        result = await session.execute(
            select(Task).where(Task.user_id == user.tg_id)
        )
        all_tasks = result.scalars().all()

        total = len(all_tasks)
        completed = sum(1 for task in all_tasks if task.is_completed)
        active = total - completed

        priorities = {1: 0, 2: 0, 3: 0}
        for task in all_tasks:
            if not task.is_completed:
                priorities[task.priority] = priorities.get(task.priority, 0) + 1

        categories = {}
        for task in all_tasks:
            if task.category and not task.is_completed:
                categories[task.category] = categories.get(task.category, 0) + 1

        return {
            'total': total,
            'completed': completed,
            'active': active,
            'priorities': priorities,
            'categories': categories
        }


async def get_user_categories(tg_id: int):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        result = await session.execute(
            select(Task.category)
            .where(
                and_(
                    Task.user_id == user.tg_id,
                    Task.category.isnot(None)
                )
            )
            .distinct()
        )
        task_categories = result.scalars().all()

        result2 = await session.execute(
            select(Category.name).where(Category.tg_id == tg_id)
        )
        db_categories = result2.scalars().all()

        all_categories = set(task_categories) | set(db_categories)
        return [str(cat) for cat in all_categories if cat]


async def create_category(tg_id: int, name: str):
    async with async_session() as session:
        existing = await session.execute(
            select(Category).where(
                and_(Category.tg_id == tg_id, Category.name == name)
            )
        )
        if existing.scalar_one_or_none():
            return None

        category = Category(tg_id=tg_id, name=name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


async def get_tasks_by_category(tg_id: int, category_name: str):
    async with async_session() as session:
        user = await get_or_create_user(tg_id)

        result = await session.execute(
            select(Task).where(
                and_(
                    Task.user_id == user.tg_id,
                    Task.category == category_name,
                    Task.is_completed == False
                )
            ).order_by(desc(Task.priority), asc(Task.created_at))
        )
        return result.scalars().all()