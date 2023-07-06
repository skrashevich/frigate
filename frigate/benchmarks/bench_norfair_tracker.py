import numpy as np
from frigate.track.norfair_tracker import distance


def bench_distance_calculation(self):
    detection = np.array([[3, 4], [5, 6]])
    estimate = np.array([[4, 5], [6, 7]])

    expected_distance = 0.7071067811865476

    for _ in range(10_000):
        distance(detection, estimate)


__benchmarks__ = [bench_distance_calculation]
