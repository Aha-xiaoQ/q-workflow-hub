from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_semantic_annotation.py"
spec = importlib.util.spec_from_file_location("semantic_validator", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def base_sample() -> dict:
    return {
        "id": "T-01",
        "screen_left_eye_box": [4, 5, 6, 4],
        "screen_right_eye_box": [15, 6, 5, 4],
        "merged_eye_box": [4, 5, 16, 5],
        "visible_eye_count": 2,
        "visible_eye_complete": {"left": True, "right": True},
        "upper_lid_complete": {"left": True, "right": True},
        "status": "annotated",
        "face_size": [32, 24],
    }


def payload(samples: list[dict] | None = None) -> dict:
    return {
        "schema": "eye-semantic-manual-v1",
        "coordinate_space": "face-crop-native-pixels",
        "eye_side_convention": "screen-left/screen-right",
        "box_semantics": "xywh-half-open",
        "samples": [base_sample()] if samples is None else samples,
    }


class SemanticValidatorTests(unittest.TestCase):
    def check_invalid(self, data: object, phrase: str, *, final: bool = False, expected: int | None = None) -> None:
        errors = module.validate_payload(data, final_gate=final, expected_count=expected)
        self.assertTrue(any(phrase in error for error in errors), errors)

    def test_valid_double_eye_final(self) -> None:
        self.assertEqual(module.validate_payload(payload(), final_gate=True), [])

    def test_root_array(self) -> None:
        self.check_invalid([], "root JSON")

    def test_empty_samples(self) -> None:
        self.check_invalid(payload([]), "at least one")

    def test_blank_and_duplicate_ids(self) -> None:
        a, b, c = base_sample(), base_sample(), base_sample()
        a["id"] = " "
        b["id"] = c["id"] = "dup"
        errors = module.validate_payload(payload([a, b, c]))
        self.assertTrue(any("non-blank" in e for e in errors))
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_trimmed_duplicate_and_path_id(self) -> None:
        a, b = base_sample(), base_sample()
        a["id"] = "dup"
        b["id"] = " dup "
        errors = module.validate_payload(payload([a, b]))
        self.assertTrue(any("safe basename" in e or "duplicate" in e for e in errors), errors)
        a["id"] = "../escape"
        self.check_invalid(payload([a]), "safe basename")

    def test_bool_float_negative_and_zero_box(self) -> None:
        for box in ([True, 2, 3, 4], [1.0, 2, 3, 4], [-1, 2, 3, 4], [1, 2, 0, 4]):
            sample = base_sample()
            sample["screen_left_eye_box"] = box
            self.check_invalid(payload([sample]), "non-boolean")

    def test_out_of_bounds(self) -> None:
        sample = base_sample()
        sample["screen_right_eye_box"] = [30, 6, 5, 4]
        sample["merged_eye_box"] = [4, 5, 31, 5]
        self.check_invalid(payload([sample]), "exceeds face bounds")

    def test_double_null(self) -> None:
        sample = base_sample()
        sample["screen_left_eye_box"] = None
        sample["screen_right_eye_box"] = None
        sample["merged_eye_box"] = [0, 0, 1, 1]
        sample["visible_eye_count"] = 0
        self.check_invalid(payload([sample]), "at least one visible")

    def test_valid_single_eye_final(self) -> None:
        sample = base_sample()
        sample["screen_right_eye_box"] = None
        sample["merged_eye_box"] = sample["screen_left_eye_box"]
        sample["visible_eye_count"] = 1
        sample["not_visible_reason"] = "hair fully hides far eye"
        sample["visible_eye_complete"] = {"left": True, "right": None}
        sample["upper_lid_complete"] = {"left": True, "right": "not-applicable"}
        self.assertEqual(module.validate_payload(payload([sample]), final_gate=True), [])

    def test_single_eye_blank_or_wrong_reason_fails(self) -> None:
        for reason in ("   ", [], {"why": "hair"}):
            sample = base_sample()
            sample["screen_right_eye_box"] = None
            sample["merged_eye_box"] = sample["screen_left_eye_box"]
            sample["visible_eye_count"] = 1
            sample["not_visible_reason"] = reason
            sample["visible_eye_complete"] = {"left": True, "right": None}
            sample["upper_lid_complete"] = {"left": True, "right": None}
            self.check_invalid(payload([sample]), "requires a not-visible", final=True)

    def test_swapped_sides(self) -> None:
        sample = base_sample()
        sample["screen_left_eye_box"], sample["screen_right_eye_box"] = sample["screen_right_eye_box"], sample["screen_left_eye_box"]
        self.check_invalid(payload([sample]), "screen-left eye center")

    def test_merged_too_small_and_large(self) -> None:
        for merged in ([5, 5, 14, 5], [3, 4, 18, 7]):
            sample = base_sample()
            sample["merged_eye_box"] = merged
            self.check_invalid(payload([sample]), "exact union")

    def test_complete_unknown_missing_false(self) -> None:
        for value in ({"foo": True}, {"left": True}, {"left": True, "right": False}):
            sample = base_sample()
            sample["visible_eye_complete"] = value
            errors = module.validate_payload(payload([sample]))
            self.assertTrue(any("visible_eye_complete" in error for error in errors), errors)

    def test_invisible_side_unhashable_is_contract_error(self) -> None:
        for value in ([], {"bad": True}):
            sample = base_sample()
            sample["screen_right_eye_box"] = None
            sample["merged_eye_box"] = sample["screen_left_eye_box"]
            sample["visible_eye_count"] = 1
            sample["visible_eye_complete"] = {"left": True, "right": value}
            errors = module.validate_payload(payload([sample]))
            self.assertTrue(any("invisible side right" in error for error in errors), errors)

    def test_needs_review_final_gate(self) -> None:
        sample = base_sample()
        sample["status"] = "needs-review"
        self.check_invalid(payload([sample]), "must be annotated", final=True)

    def test_expected_count(self) -> None:
        self.check_invalid(payload(), "sample count", expected=2)

    def test_missing_box_semantics(self) -> None:
        data = payload()
        del data["box_semantics"]
        self.check_invalid(data, "half-open")

    def test_false_half_open_substring_is_rejected(self) -> None:
        data = payload()
        del data["box_semantics"]
        data["box_format"] = "not-half-open"
        self.check_invalid(data, "half-open")

    def test_invalid_truthy_face_size_fails_final(self) -> None:
        sample = base_sample()
        sample["face_size"] = ["x", "y"]
        errors = module.validate_payload(payload([sample]), final_gate=True)
        self.assertTrue(any("face_size" in error for error in errors), errors)
        self.assertTrue(any("final gate requires" in error for error in errors), errors)

    def test_cli_missing_and_corrupt_are_exit_2(self) -> None:
        missing = subprocess.run([sys.executable, str(SCRIPT), str(Path(tempfile.gettempdir()) / "semantic-validator-missing.json")], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2, missing.stdout + missing.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            corrupt = Path(tmp) / "corrupt.json"
            corrupt.write_text("{not json", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(corrupt)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_cli_root_array_is_contract_fail_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root_array = Path(tmp) / "array.json"
            root_array.write_text("[]", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(root_array)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('"semantic_authority": false', result.stdout)

    def test_cli_missing_face_image_is_environment_error_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            annotation = Path(tmp) / "annotation.json"
            face_dir = Path(tmp) / "faces"
            face_dir.mkdir()
            data = payload()
            del data["samples"][0]["face_size"]
            annotation.write_text(__import__("json").dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(annotation), "--faces-dir", str(face_dir), "--final-gate"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('"status": "ERROR"', result.stdout)


if __name__ == "__main__":
    unittest.main()
