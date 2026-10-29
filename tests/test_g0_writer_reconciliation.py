"""Fake-only tests: no host collection, native calls, network or database."""

import importlib.util
import json
from pathlib import Path
import unittest


_path = Path(__file__).resolve().parents[1] / "scripts" / "g0_writer_reconciliation.py"
_spec = importlib.util.spec_from_file_location("g0_writer_reconciliation", _path)
module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(module)


def snapshot(processes=(), services=(), tasks=(), status="COMPLETE"):
    return {"processes": {"status": status, "rows": list(processes)},
            "services": {"status": status, "rows": list(services)},
            "tasks": {"status": status, "rows": list(tasks)}}


def process(pid, created, candidate=False):
    return {"pid": pid, "created_ns": created, "candidate": candidate}


def handle(pid, created, status, target=None, stable=True):
    return {"pid": pid, "created_ns": created, "identity_stable": stable,
            "status": status, "target": target}


def trigger(identity, pid, created, state="READY", candidate=True):
    return {"identity_sha256": identity, "state": state, "pid": pid,
            "created_ns": created, "candidate": candidate}


class ReconciliationTests(unittest.TestCase):
    def test_pid_reuse_does_not_inherit_candidate_or_handle(self):
        old = snapshot([process(42, 10, True)])
        new = snapshot([process(42, 20, False)])
        result = module.reconcile(old, new, [handle(42, 10, "POSITIVE", "WAL")])
        self.assertEqual(result["processes"][0]["observation"], "PID_REUSED_IF_ORDERED")
        self.assertIs(result["processes"][0]["before_candidate"], True)
        self.assertIs(result["processes"][0]["after_candidate"], False)
        self.assertEqual(result["handles"][0]["created_ns"], 10)
        self.assertEqual(result["handles"][0]["finding"], "POSSIBLE_WRITER")
        self.assertEqual(result["writer_closure"], "UNKNOWN")

    def test_absent_or_incomplete_identity_stays_unknown(self):
        old = snapshot([process(1, 10), process(2, None), process(3, 30)])
        new = snapshot([process(2, 20), process(4, 40)], status="INCOMPLETE")
        result = module.reconcile(old, new, [])
        self.assertEqual([row["observation"] for row in result["processes"]],
                         ["UNKNOWN"] * 4)
        self.assertEqual(result["snapshot_status"]["after"]["processes"], "INCOMPLETE")
        self.assertFalse(result["time_order_verified"])

    def test_complete_samples_distinguish_new_exited_and_both(self):
        result = module.reconcile(snapshot([process(1, 10), process(2, 20)]),
                                  snapshot([process(2, 20), process(3, 30)]), [])
        self.assertEqual([row["observation"] for row in result["processes"]],
                         ["EXITED_IF_ORDERED", "OBSERVED_BOTH", "NEW_IF_ORDERED"])
        self.assertEqual(result["writer_closure"], "UNKNOWN")

    def test_negative_failed_and_missing_handle_coverage_never_prove_absence(self):
        rows = [handle(i, i, status) for i, status in enumerate(
            ["EMPTY", "ACCESS_DENIED", "TIMEOUT", "NOT_PROBED", "ERROR"], 1)]
        result = module.reconcile(snapshot(), snapshot(), rows)
        self.assertEqual([r["finding"] for r in result["handles"]], ["UNKNOWN"] * 5)
        self.assertEqual(result["writer_closure"], "UNKNOWN")
        self.assertEqual(module.reconcile(snapshot(), snapshot(), [])["writer_closure"], "UNKNOWN")

    def test_positive_handle_with_unstable_or_missing_identity_is_not_attributed(self):
        result = module.reconcile(snapshot(), snapshot(), [
            handle(7, 70, "POSITIVE", "DB", stable=False),
            handle(8, None, "POSITIVE", "SHM")])
        self.assertEqual([r["finding"] for r in result["handles"]],
                         ["POSSIBLE_WRITER_IDENTITY_UNKNOWN"] * 2)

    def test_trigger_link_requires_pid_and_creation_and_ready_is_not_stopped(self):
        entries = [trigger("a" * 64, 42, 10), trigger("b" * 64, 42, 9)]
        result = module.reconcile(snapshot([process(42, 10)], tasks=entries), snapshot(), [])
        self.assertEqual([r["association"] for r in result["triggers"]],
                         ["EXACT_IDENTITY_IN_SAMPLE", "UNKNOWN"])
        self.assertEqual(result["triggers"][0]["state"], "READY")
        self.assertEqual(result["writer_closure"], "UNKNOWN")

    def test_rejects_private_fields_and_never_echoes_rejected_values(self):
        s = snapshot([process(1, 10)])
        s["processes"]["rows"][0]["command_line"] = r"C:\private\secret.db"
        with self.assertRaises(ValueError) as context:
            module.reconcile(s, snapshot(), [])
        self.assertNotIn("private", str(context.exception))
        self.assertNotIn("secret", str(context.exception))
        with self.assertRaises(ValueError):
            module.reconcile(snapshot(), snapshot(), [handle(1, 1, "POSITIVE", r"C:\private\state.db")])

    def test_bounds_and_duplicate_pid_fail_closed(self):
        with self.assertRaises(ValueError):
            module.reconcile(snapshot([process(i, i) for i in range(module.MAX_PROCESS_ROWS + 1)]), snapshot(), [])
        with self.assertRaises(ValueError):
            module.reconcile(snapshot([process(1, 1), process(1, 2)]), snapshot(), [])
        self.assertLessEqual(len(json.dumps(module.reconcile(snapshot(), snapshot(), []),
                                            separators=(",", ":")).encode("ascii")),
                             module.MAX_OUTPUT_BYTES)

    def test_documented_inventory_scale_fits_without_truncation(self):
        processes = [process(i, 10000 + i) for i in range(478)]
        services = [trigger(format(i, "064x"), i, 10000 + i, state="RUNNING")
                    for i in range(306)]
        tasks = [trigger(format(i + 1000, "064x"), i, 10000 + i)
                 for i in range(210)]
        sample = snapshot(processes, services, tasks)
        result = module.reconcile(sample, sample, [])
        self.assertEqual(len(result["processes"]), 478)
        self.assertEqual(len(result["triggers"]), 2 * (306 + 210))
        self.assertTrue(all(row["association"] == "EXACT_IDENTITY_IN_SAMPLE"
                            for row in result["triggers"]))
        self.assertEqual(result["writer_closure"], "UNKNOWN")
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=True,
                                            separators=(",", ":")).encode("ascii")),
                             module.MAX_OUTPUT_BYTES)

    def test_all_group_limits_and_output_limit_fail_closed(self):
        for kind, limit in (("services", module.MAX_SERVICE_ROWS),
                            ("tasks", module.MAX_TASK_ROWS)):
            entries = [trigger(format(i, "064x"), None, None) for i in range(limit + 1)]
            sample = snapshot()
            sample[kind]["rows"] = entries
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                module.reconcile(sample, snapshot(), [])
        with self.assertRaises(ValueError):
            module.reconcile(snapshot(), snapshot(),
                             [handle(1, 1, "EMPTY")] * (module.MAX_HANDLE_ROWS + 1))
        original = module.MAX_OUTPUT_BYTES
        try:
            module.MAX_OUTPUT_BYTES = 1
            with self.assertRaises(ValueError):
                module.reconcile(snapshot(), snapshot(), [])
        finally:
            module.MAX_OUTPUT_BYTES = original

    def test_all_maximum_groups_fit_output_limit_without_truncation(self):
        def full_sample(offset):
            return snapshot(
                [process(offset + i, 10000 + i) for i in range(module.MAX_PROCESS_ROWS)],
                [trigger(format(i, "064x"), None, None) for i in range(module.MAX_SERVICE_ROWS)],
                [trigger(format(i + 1000, "064x"), None, None) for i in range(module.MAX_TASK_ROWS)])
        rows = [handle(i, i, "EMPTY") for i in range(module.MAX_HANDLE_ROWS)]
        result = module.reconcile(full_sample(0), full_sample(module.MAX_PROCESS_ROWS), rows)
        self.assertEqual(len(result["processes"]), 2 * module.MAX_PROCESS_ROWS)
        self.assertEqual(len(result["triggers"]), 2 * (module.MAX_SERVICE_ROWS + module.MAX_TASK_ROWS))
        self.assertEqual(len(result["handles"]), module.MAX_HANDLE_ROWS)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=True,
                                            separators=(",", ":")).encode("ascii")),
                             module.MAX_OUTPUT_BYTES)

    def test_duplicate_positive_rows_remain_observations_not_writer_count(self):
        observation = handle(42, 10, "POSITIVE", "DB")
        result = module.reconcile(snapshot(), snapshot(), [observation, dict(observation)])
        self.assertEqual(result["handle_rows_semantics"],
                         "OBSERVATIONS_NOT_UNIQUE_HANDLES_OR_WRITERS")
        self.assertEqual(len(result["handles"]), 2)
        self.assertEqual(result["handles"][0], result["handles"][1])
        self.assertEqual(result["writer_closure"], "UNKNOWN")

    def test_public_output_contains_no_private_input_fields(self):
        sample = snapshot([process(1, 100)], [trigger("a" * 64, 1, 100)])
        output = json.dumps(module.reconcile(sample, sample, [handle(1, 100, "POSITIVE", "DB")]))
        self.assertNotIn("command_line", output)
        self.assertNotIn("private_path", output)
        self.assertNotIn("C:\\\\", output)
        self.assertNotIn("secret", output)
        sample["services"]["rows"][0]["private_path"] = r"C:\private\secret.db"
        with self.assertRaises(ValueError) as context:
            module.reconcile(sample, snapshot(), [])
        self.assertNotIn("secret", str(context.exception))


if __name__ == "__main__":
    unittest.main()
