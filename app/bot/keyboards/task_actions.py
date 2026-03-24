from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принял", callback_data=f"task:{task_id}:accepted")],
            [InlineKeyboardButton(text="Выполнено", callback_data=f"task:{task_id}:done")],
            [InlineKeyboardButton(text="Есть проблема", callback_data=f"task:{task_id}:problem")],
        ]
    )
