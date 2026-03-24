from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data.startswith("task:"))
async def task_status_callback(callback: CallbackQuery):
    _, task_id, status = callback.data.split(":")
    await callback.message.answer(f"Задача #{task_id}: новый статус — {status}")
    await callback.answer("Статус принят")
