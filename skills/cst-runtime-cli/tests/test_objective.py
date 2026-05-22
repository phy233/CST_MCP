from __future__ import annotations

import unittest

from cst_runtime.core.objective import compute_objective


class TestObjectiveFunction(unittest.TestCase):

    def _make_run_output(self, s11_metric=None, s11_path="", farfield=None):
        return {
            "s11_metric": s11_metric,
            "s11_export_path": s11_path,
            "farfield_exported": farfield or [],
            "exported": [],
        }

    def test_s11_min_db_from_metric(self):
        run = self._make_run_output(s11_metric={"min_db": -25.3, "best_freq": 2.45})
        result = compute_objective({"type": "s11_min_db"}, run)
        self.assertAlmostEqual(result["value"], -25.3)
        self.assertEqual(result["direction"], "minimize")

    def test_s11_at_freq(self):
        run = self._make_run_output(s11_metric={
            "min_db": -30.0, "best_freq": 2.4,
            "all_db": [-20, -25, -30, -28],
            "all_freq": [2.38, 2.39, 2.40, 2.41],
        })
        result = compute_objective({"type": "s11_at_freq", "freq": 2.39}, run)
        self.assertAlmostEqual(result["value"], -25.0)

    def test_gain_max_no_farfield(self):
        run = self._make_run_output(s11_metric={"min_db": -20})
        result = compute_objective({"type": "gain_max"}, run)
        self.assertEqual(result.get("error"), "no_farfield_data")

    def test_bandwidth_from_metric(self):
        run = self._make_run_output(s11_metric={
            "min_db": -30, "best_freq": 2.4,
            "all_db": [-5, -12, -20, -15, -8],
            "all_freq": [2.35, 2.38, 2.40, 2.42, 2.45],
        })
        result = compute_objective({"type": "bandwidth", "below_db": -10}, run)
        self.assertGreater(result["value"], 0.0)
        self.assertEqual(result["direction"], "maximize")

    def test_expression(self):
        run = self._make_run_output(s11_metric={
            "all_db": [-10, -20, -30],
            "all_freq": [2.3, 2.4, 2.5],
        })
        result = compute_objective({"type": "expression", "expr": "min(s11_db)"}, run)
        self.assertAlmostEqual(result["value"], -30.0)

    def test_direction_override(self):
        run = self._make_run_output(s11_metric={"min_db": -25})
        result = compute_objective({"type": "s11_min_db", "direction": "maximize"}, run)
        self.assertEqual(result["direction"], "maximize")

    def test_unknown_type_defaults(self):
        run = self._make_run_output(s11_metric={"min_db": -25})
        result = compute_objective({"type": "nonexistent"}, run)
        self.assertIn("error", result)

    def test_default_type(self):
        run = self._make_run_output(s11_metric={"min_db": -25.3})
        result = compute_objective({}, run)
        self.assertAlmostEqual(result["value"], -25.3)


class TestInferCategory(unittest.TestCase):

    def test_infer_category_geometry(self):
        from cst_runtime.core.project import _infer_category
        self.assertEqual(_infer_category("R"), "geometry")
        self.assertEqual(_infer_category("length"), "geometry")
        self.assertEqual(_infer_category("width"), "geometry")
        self.assertEqual(_infer_category("height"), "geometry")

    def test_infer_category_mesh(self):
        from cst_runtime.core.project import _infer_category
        self.assertEqual(_infer_category("mesh_accuracy"), "mesh")

    def test_infer_category_solver(self):
        from cst_runtime.core.project import _infer_category
        self.assertEqual(_infer_category("solver_tolerance"), "solver")

    def test_infer_category_material(self):
        from cst_runtime.core.project import _infer_category
        self.assertEqual(_infer_category("substrate_epsilon"), "material")

    def test_infer_category_frequency(self):
        from cst_runtime.core.project import _infer_category
        self.assertEqual(_infer_category("center_frequency"), "frequency")
