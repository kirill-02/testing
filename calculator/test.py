import unittest
from calculator import add, subtract, multiply, divide, calculate

class TestCalculatorOperations(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(add(3, 7), 10)
    def test_add_negative(self):
        self.assertEqual(add(-5, 12), 7)

    def test_subtract(self):
        self.assertEqual(subtract(10, 4), 6)
        self.assertEqual(subtract(4, 10), -6)

    def test_multiply(self):
        self.assertEqual(multiply(6, 7), 42)
        self.assertEqual(multiply(2.5, 4), 10.0)

    def test_divide(self):
        self.assertEqual(divide(20, 5), 4)
        self.assertAlmostEqual(divide(7, 2), 3.5)

    def test_divide_by_zero_raises_error(self):
        with self.assertRaises(ValueError) as cm:
            divide(10, 0)
        self.assertEqual(str(cm.exception), "Деление на ноль запрещено")

    def test_calculate_valid_expressions(self):
        self.assertEqual(calculate("15 + 9"), 24)
        self.assertEqual(calculate("48/6"), 8)
        self.assertAlmostEqual(calculate("10.5 * 2"), 21.0)

    def test_calculate_invalid_format_raises_error(self):
        with self.assertRaises(ValueError):
            calculate("5 +")
        with self.assertRaises(ValueError):
            calculate("2 + 3 + 4")
        with self.assertRaises(ValueError):
            calculate("abc * 5")
        with self.assertRaises(ValueError):
            calculate("")


if __name__ == '__main__':
    unittest.main()