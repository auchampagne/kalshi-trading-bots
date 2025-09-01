# test_updater.py
import unittest
from updater import ServeModel, ServePriors

class TestUpdater(unittest.TestCase):

    def setUp(self):
        """Set up a fresh model for each test."""
        priors = ServePriors(a_alpha=30.0, a_beta=20.0, b_alpha=40.0, b_beta=18.0)
        self.serve_model = ServeModel(priors)

    def test_adaptive_discount_logic(self):
        # --- Initial State ---
        self.assertEqual(self.serve_model.a_service_games_played, 0)
        initial_alpha = self.serve_model.a_alpha

        # --- First Update for Player A ---
        # Simulate A holding serve easily
        self.serve_model.update_after_service_game('A', points_won_by_server=4, total_points=4)
        
        # Check that the game counter was incremented
        self.assertEqual(self.serve_model.a_service_games_played, 1)
        # Check that the model parameter has changed
        self.assertNotEqual(self.serve_model.a_alpha, initial_alpha)

        # --- Second Update for Player A ---
        second_update_alpha = self.serve_model.a_alpha
        # Simulate A getting broken
        self.serve_model.update_after_service_game('A', points_won_by_server=0, total_points=4)
        
        self.assertEqual(self.serve_model.a_service_games_played, 2)
        self.assertNotEqual(self.serve_model.a_alpha, second_update_alpha)

if __name__ == '__main__':
    unittest.main()