import unittest
from derive_cache_allocation import allocation

class AllocationTests(unittest.TestCase):
    def test_equal_budget_and_more_slots_for_higher_miss_pressure(self):
        result=allocation([1]*8+[100]*8)
        self.assertEqual(sum(result),512)
        self.assertTrue(all(8<=c<=64 for c in result))
        self.assertGreater(sum(result[8:]),sum(result[:8]))

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):allocation([1]*16,total=127)
