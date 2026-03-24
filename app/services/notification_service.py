from app.core.config import settings


class NotificationService:
    @staticmethod
    def format_task_digest(tasks: list) -> str:
        if not tasks:
            return "На сегодня задач нет."

        lines = ["Список задач:"]
        for task in tasks:
            lines.append(f"- #{task.id} {task.title} [{task.status}]")
        return "\n".join(lines)

    @staticmethod
    def get_task_chat_id() -> int:
        return settings.tg_task_chat_id
