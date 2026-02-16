import unittest
from todo import ToDoList


class TestToDoList(unittest.TestCase):
    def setUp(self):
        self.todo = ToDoList()

    def test_add_task(self):
        task_id = self.todo.add_task("Купить хлеб")
        tasks = self.todo.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['id'], task_id)
        self.assertEqual(tasks[0]['description'], "Купить хлеб")
        self.assertFalse(tasks[0]['completed'])
        self.assertEqual(self.todo.next_id, 2)

    def test_add_task_empty_description_raises_error(self):
        with self.assertRaises(ValueError):
            self.todo.add_task("")
        with self.assertRaises(ValueError):
            self.todo.add_task("   ")
        self.assertEqual(len(self.todo.get_tasks()), 0)

    def test_delete_task(self):
        id1 = self.todo.add_task("Задача 1")
        id2 = self.todo.add_task("Задача 2")
        
        self.assertTrue(self.todo.delete_task(id1))
        self.assertEqual(len(self.todo.get_tasks()), 1)
        self.assertEqual(self.todo.get_tasks()[0]['id'], id2)
        
        self.assertFalse(self.todo.delete_task(999))

    def test_edit_task(self):
        task_id = self.todo.add_task("Старое описание")
        
        self.assertTrue(self.todo.edit_task(task_id, "Новое важное дело"))
        tasks = self.todo.get_tasks()
        self.assertEqual(tasks[0]['description'], "Новое важное дело")
        self.assertFalse(tasks[0]['completed'])
        
        with self.assertRaises(ValueError):
            self.todo.edit_task(task_id, "  ")
        
        self.assertFalse(self.todo.edit_task(999, "Что угодно"))

    def test_mark_as_done(self):
        task_id = self.todo.add_task("Сделать уборку")
        
        self.assertTrue(self.todo.mark_as_done(task_id))
        self.assertTrue(self.todo.get_tasks()[0]['completed'])
        
        self.assertFalse(self.todo.mark_as_done(999))

    def test_get_tasks_returns_shallow_copy(self):
        self.todo.add_task("A")
        self.todo.add_task("B")
        self.todo.add_task("C")
        
        tasks = self.todo.get_tasks()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0]['description'], "A")
        self.assertEqual(tasks[1]['description'], "B")
        
        tasks[1]['description'] = "изменено"
        
        original = self.todo.get_tasks()
        self.assertEqual(original[1]['description'], "изменено")
        
        self.assertIsNot(tasks, self.todo.tasks)


if __name__ == '__main__':
    unittest.main()