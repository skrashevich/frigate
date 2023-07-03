import timeit
import numpy as np
import unittest
from frigate.track.norfair_tracker import distance


class DistanceTestCase(unittest.TestCase):
    def test_distance_calculation(self):
        detection = np.array([[3, 4], [5, 6]])
        estimate = np.array([[4, 5], [6, 7]])

        expected_distance = 0.7071067811865476

        start_time = timeit.default_timer()
        for _ in range(10000):
            result = distance(detection, estimate)

        end_time = timeit.default_timer()
        execution_time = end_time - start_time

        self.assertEqual(result, expected_distance)

        print(f"Execution time: {execution_time} seconds")


if __name__ == "__main__":
    unittest.main()
