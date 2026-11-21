"""Unit tests for Haversine distance calculations."""
import unittest
import numpy as np

from data_engineering.spatial.haversine import haversine_distance, haversine_vectorized


class TestHaversine(unittest.TestCase):
    def test_zero_distance_same_point(self):
        dist = haversine_distance(40.7128, -74.0060, 40.7128, -74.0060)
        self.assertAlmostEqual(dist, 0.0, places=5)

    def test_known_distance_empire_to_times_square(self):
        # Empire State Building: (40.748817, -73.985428)
        # Times Square: (40.758896, -73.985130)
        # Real distance ~1.12 km
        dist = haversine_distance(40.748817, -73.985428, 40.758896, -73.985130)
        self.assertGreater(dist, 1.0)
        self.assertLess(dist, 1.3)

    def test_known_distance_london_to_paris(self):
        # London (51.5074, -0.1278) to Paris (48.8566, 2.3522)
        # Great-circle distance approx 343 km
        dist = haversine_distance(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertAlmostEqual(dist, 343.5, delta=3.0)

    def test_haversine_vectorized_broadcasting(self):
        lats1 = np.array([40.7580, 40.7500])[:, np.newaxis]  # (2, 1)
        lons1 = np.array([-73.9855, -73.9800])[:, np.newaxis]
        lats2 = np.array([40.7580, 40.7000])[np.newaxis, :]  # (1, 2)
        lons2 = np.array([-73.9855, -74.0000])[np.newaxis, :]

        matrix = haversine_vectorized(lats1, lons1, lats2, lons2)
        self.assertEqual(matrix.shape, (2, 2))
        self.assertAlmostEqual(matrix[0, 0], 0.0, places=5)
        self.assertGreater(matrix[0, 1], 5.0)

    def test_nan_handling(self):
        dist = haversine_distance(np.nan, -74.0, 40.7, -74.0)
        self.assertTrue(np.isnan(dist))


if __name__ == "__main__":
    unittest.main()
