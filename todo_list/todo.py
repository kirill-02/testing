class ToDoList:
    def __init__(self):
        self.tasks = []        
        self.next_id = 1        

    def add_task(self, description: str) -> int:
        "Добавляет новую задачу возвращает её id"
        if not description or not description.strip():
            raise ValueError("Описание задачи не может быть пустым")
        
        task = {
            'id': self.next_id,
            'description': description.strip(),
            'completed': False
        }
        self.tasks.append(task)
        self.next_id += 1
        return task['id']


    def get_tasks(self) -> list:
        "Возвращает копию списка всех задач"
        return self.tasks[:]

    def delete_task(self, task_id: int) -> bool:
        "Удаляет задачу по id возвращает True если удалено"
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                del self.tasks[i]
                return True
        return False

    def edit_task(self, task_id: int, new_description: str) -> bool:
        "Изменяет описание задачи возвращает True при успехе"
        if not new_description or not new_description.strip():
            raise ValueError("Новое описание не может быть пустым")
        
        for task in self.tasks:
            if task['id'] == task_id:
                task['description'] = new_description.strip()
                return True
        return False

    def mark_as_done(self, task_id: int) -> bool:
        "Помечает задачу как выполненную возвращает True при успехе"
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = True
                return True
        return False