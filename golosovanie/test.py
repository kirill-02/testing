import unittest
from voting_system import VotingSystem, Poll


class TestVotingSystem(unittest.TestCase):
    def setUp(self):
        self.system = VotingSystem()

    def test_create_poll_success(self):
        "Создание опроса → проверяем id, вопрос, варианты, начальные голоса"
        poll_id = self.system.create_poll(
            " Какой ваш любимый сезон? ",
            ["Зима", " Весна ", "Лето", "Осень"]
        )
        self.assertEqual(poll_id, 1)
        self.assertEqual(self.system.next_poll_id, 2)

        results = self.system.get_poll_results(1)
        self.assertEqual(results, {"Зима": 0, "Весна": 0, "Лето": 0, "Осень": 0})
        self.assertEqual(self.system.list_polls()[0]["question"], "Какой ваш любимый сезон?")

    def test_create_poll_validation(self):
        "Проверяем все случаи некорректного создания опроса"
        with self.assertRaises(ValueError, msg="Пустой вопрос"):
            self.system.create_poll("", ["Да", "Нет"])

        with self.assertRaises(ValueError, msg="Меньше 2 вариантов"):
            self.system.create_poll("Вопрос?", ["Один"])

        with self.assertRaises(ValueError, msg="Дубликаты вариантов"):
            self.system.create_poll("Цвет?", ["Красный", "Красный", "Синий"])

    def test_single_user_votes_once(self):
        "Один пользователь голосует → повторно не может"
        pid = self.system.create_poll("Любите ли вы Python?", ["Да", "Нет", "Иногда"])

        self.assertTrue(self.system.vote(pid, "user:123", "Да"))
        self.assertFalse(self.system.vote(pid, "user:123", "Нет"))

        results = self.system.get_poll_results(pid)
        self.assertEqual(results["Да"], 1)
        self.assertEqual(results["Нет"], 0)
        self.assertEqual(results["Иногда"], 0)

    def test_multiple_users_different_choices(self):
        "Несколько пользователей голосуют по-разному → проверяем подсчёт"
        pid = self.system.create_poll("Лучший напиток?", ["Кофе", "Чай", "Вода"])

        votes = [
            ("alice", "Кофе"),
            ("bob", "Чай"),
            ("charlie", "Кофе"),
            ("dave", "Вода"),
            ("eve", "Кофе"),
        ]

        for uid, choice in votes:
            self.assertTrue(self.system.vote(pid, uid, choice))

        results = self.system.get_poll_results(pid)
        self.assertEqual(results, {"Кофе": 3, "Чай": 1, "Вода": 1})
        self.assertEqual(self.system.get_total_votes(pid), 5)

    def test_invalid_vote_cases(self):
        "Голосование за несуществующий опрос / вариант / повтор"
        pid = self.system.create_poll("Тест", ["A", "B"])

        self.assertFalse(self.system.vote(999, "user:x", "A"))

        self.assertFalse(self.system.vote(pid, "user:y", "Z"))

        self.system.vote(pid, "user:z", "A")
        self.assertFalse(self.system.vote(pid, "user:z", "B"))

        self.assertEqual(self.system.get_poll_results(pid), {"A": 1, "B": 0})

    def test_results_copy_protection(self):
        "get_poll_results возвращает копию, а не ссылку на внутренний словарь"
        pid = self.system.create_poll("Фрукты", ["Яблоко", "Груша"])
        self.system.vote(pid, "u1", "Яблоко")
        self.system.vote(pid, "u2", "Яблоко")

        results = self.system.get_poll_results(pid)
        results["Яблоко"] = 999
        results["Банан"] = 100

        original = self.system.get_poll_results(pid)
        self.assertEqual(original, {"Яблоко": 2, "Груша": 0})
        self.assertNotIn("Банан", original)


if __name__ == "__main__":
    unittest.main()