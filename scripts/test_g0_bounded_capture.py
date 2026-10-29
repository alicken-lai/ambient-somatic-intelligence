"""Fake-only regression tests for the G0 bounded-capture lifecycle barrier.

No OS child, subprocess, Git, filesystem evidence writer, or native API is used.
"""

import io
import json
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g0_bounded_capture as capture


class FakeChild:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code
        self.exited = threading.Event()
        self.terminate_calls = 0
        if exit_code is not None:
            self.exited.set()

    def wait(self, timeout):
        if self.exited.wait(timeout):
            return self.exit_code
        return None

    def terminate_once(self):
        self.terminate_calls += 1
        self.exit_code = -9
        self.exited.set()


class BlockingReader:
    def __init__(self):
        self.release = threading.Event()

    def read(self, _size):
        self.release.wait()
        return b""


class UnreapedFakeChild(FakeChild):
    def __init__(self):
        super().__init__()
        self.release_wait = threading.Event()

    def wait(self, _timeout):
        self.release_wait.wait()
        return None

    def terminate_once(self):
        self.terminate_calls += 1
        raise RuntimeError("PRIVATE_TERMINATION_DETAIL")


class DynamicTerminatePropertyChild(FakeChild):
    def __init__(self):
        super().__init__()
        self.terminate_property_reads = 0

    @property
    def terminate_once(self):
        self.terminate_property_reads += 1
        if self.terminate_property_reads > 1:
            raise RuntimeError("PRIVATE_TERMINATE_PROPERTY")
        return self._terminate_once

    def _terminate_once(self):
        self.terminate_calls += 1
        self.exit_code = -9
        self.exited.set()


class FailStreamThreadFactory:
    def __init__(self):
        self.calls = {}

    def __call__(self, *, target, name):
        self.calls[name] = self.calls.get(name, 0) + 1
        if name == "g0-stream-out":
            raise RuntimeError("PRIVATE_THREAD_SETUP_DETAIL")
        return threading.Thread(target=target, name=name)


class StartsWorkerThenRaisesFactory:
    """Untrusted factory starts a worker but withholds its thread handle."""

    def __init__(self):
        self.worker = None

    def __call__(self, *, target, name):
        if name == "g0-stream-out":
            self.worker = threading.Thread(target=target, name=name)
            self.worker.start()
            raise RuntimeError("PRIVATE_FACTORY_AFTER_START")
        return threading.Thread(target=target, name=name)


class StartThenRaiseThread:
    """Fake wrapper: the worker starts, then the adapter reports failure."""

    def __init__(self, target, name):
        self._thread = threading.Thread(target=target, name=name)

    @property
    def daemon(self):
        return self._thread.daemon

    @daemon.setter
    def daemon(self, value):
        self._thread.daemon = value

    @property
    def ident(self):
        return self._thread.ident

    def start(self):
        self._thread.start()
        raise RuntimeError("PRIVATE_PARTIAL_START_DETAIL")

    def is_alive(self):
        return self._thread.is_alive()

    def join(self, timeout=None):
        return self._thread.join(timeout)


class PartialStartStreamFactory:
    def __init__(self):
        self.names = []
        self.threads = []

    def __call__(self, *, target, name):
        self.names.append(name)
        if name == "g0-stream-out":
            thread = StartThenRaiseThread(target, name)
        else:
            thread = threading.Thread(target=target, name=name)
        self.threads.append(thread)
        return thread


class PartialStartWriterFactory:
    def __init__(self):
        self.threads = []

    def __call__(self, *, target, name):
        thread = (StartThenRaiseThread(target, name)
                  if name == "g0-writer-finalize-slow"
                  else threading.Thread(target=target, name=name))
        self.threads.append(thread)
        return thread


class FailChildWaitFactory:
    def __init__(self):
        self.names = []

    def __call__(self, *, target, name):
        self.names.append(name)
        if name == "g0-child-wait":
            raise RuntimeError("PRIVATE_CHILD_THREAD_SETUP")
        return threading.Thread(target=target, name=name)


def short_limits(execution=0.15, cleanup=0.08, stream=128, evidence=128):
    return capture.CaptureLimits(
        execution_seconds=execution,
        cleanup_seconds=cleanup,
        total_stream_bytes=stream,
        total_evidence_bytes=evidence,
        chunk_bytes=16,
    )


class BoundedCaptureTests(unittest.TestCase):
    def test_success_finalizes_only_after_child_and_consumers_stop(self):
        child = FakeChild(0)
        events = []
        stored = bytearray()
        inventory = bytearray()
        writers = [capture.EvidenceWriterSpec(
            "summary", 32,
            lambda data: (stored.extend(data), len(data))[1],
            lambda: events.append((
                "writer-finalized",
                child.exited.is_set(),
                not any(t.name in ("g0-stream-out", "g0-stream-err") and t.is_alive()
                        for t in threading.enumerate()),
            )),
        )]

        def consume(data, sinks):
            sinks["summary"].write(data)

        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[
                capture.StreamSpec("out", "stdout", io.BytesIO(b"safe-output"), 32, consume),
                capture.StreamSpec("err", "stderr", io.BytesIO(b"PRIVATE_STDERR_SENTINEL"), 32),
            ],
            writers=writers,
            inventory_writer=capture.EvidenceWriterSpec(
                "inventory", 32,
                lambda data: (inventory.extend(data), len(data))[1],
                lambda: events.append(("inventory-finalized", bytes(inventory))),
            ),
            finalize_evidence=lambda sink: (sink.write(b"manifest"), events.append(("inventory", bytes(stored)))),
            limits=short_limits(),
        )
        self.assertEqual(result["state"], "CAPTURED_REGISTERED_SCOPE_ONLY", result)
        self.assertFalse(result["unregistered_work_proven_stopped"])
        self.assertIn("UNREGISTERED_WORK_IS_NOT_PROVEN_STOPPED",
                      result["callback_completion_contract"])
        self.assertTrue(result["child_reaped"])
        self.assertTrue(result["evidence_inventory_finalized"])
        self.assertEqual(bytes(stored), b"safe-output")
        self.assertEqual(events, [("writer-finalized", True, True), ("inventory", b"safe-output"),
                                  ("inventory-finalized", b"manifest")])
        self.assertFalse(result["raw_stderr_retained"])
        self.assertNotIn("PRIVATE_STDERR_SENTINEL", json.dumps(result))
        self.assertEqual(child.terminate_calls, 0)

    def test_stream_limit_terminates_once_and_suppresses_finalization(self):
        child = FakeChild()
        finalized = []
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"0123456789"), 4)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: finalized.append(True),
            limits=short_limits(stream=16),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "stream_byte_limit")
        self.assertEqual(result["stream_records"][0]["bytes"], 4)
        self.assertEqual(child.terminate_calls, 1)
        self.assertEqual(result["termination_attempts"], 1)
        self.assertFalse(result["evidence_inventory_finalized"])
        self.assertEqual(finalized, [])

    def test_shared_stream_budget_is_not_exceeded(self):
        child = FakeChild(0)
        limits = capture.CaptureLimits(
            execution_seconds=0.15, cleanup_seconds=0.08,
            total_stream_bytes=3, total_evidence_bytes=128, chunk_bytes=2,
        )
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[
                capture.StreamSpec("out", "stdout", io.BytesIO(b"0123456789"), 3),
                capture.StreamSpec("err", "stderr", io.BytesIO(b"abcdefghij"), 3),
            ],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: self.fail("inventory must not finalize at shared byte cap"),
            limits=limits,
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertIn(result["reason_code"], ("stream_budget_exhausted", "stream_byte_limit"))
        self.assertLessEqual(sum(row["bytes"] for row in result["stream_records"]), 3)

    def test_failed_termination_is_not_retried_and_child_remains_pending(self):
        child = UnreapedFakeChild()
        try:
            result = capture.bounded_capture(
                child,
                child_identity="fake-child",
                streams=[],
                writers=[],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: self.fail("inventory must not finalize for unreaped child"),
                limits=short_limits(execution=0.03, cleanup=0.03),
            )
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertEqual(result["reason_code"], "child_terminate_error")
            self.assertEqual(result["termination_attempts"], 1)
            self.assertEqual(child.terminate_calls, 1)
            self.assertIn("child:fake-child", result["pending_identities"])
            self.assertNotIn("PRIVATE_TERMINATION_DETAIL", json.dumps(result))
        finally:
            child.release_wait.set()

    def test_worker_start_failure_has_no_fallback_or_retry(self):
        child = FakeChild()
        factory = FailStreamThreadFactory()
        finalized = []
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"unused"), 16)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: finalized.append(True),
            limits=short_limits(),
            thread_factory=factory,
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "task_start_error")
        self.assertEqual(factory.calls["g0-stream-out"], 1)
        self.assertEqual(child.terminate_calls, 1)
        self.assertEqual(result["launch_retries"], 0)
        self.assertEqual(finalized, [])
        self.assertNotIn("PRIVATE_THREAD_SETUP_DETAIL", json.dumps(result))

    def test_factory_side_effect_then_raise_is_unaccounted_pending(self):
        child = FakeChild()
        reader = BlockingReader()
        factory = StartsWorkerThenRaisesFactory()
        finalized = []
        try:
            result = capture.bounded_capture(
                child,
                child_identity="fake-child",
                streams=[capture.StreamSpec("out", "stdout", reader, 16)],
                writers=[],
                inventory_writer=capture.EvidenceWriterSpec(
                    "inventory", 16, lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: finalized.append(True),
                limits=short_limits(execution=0.04, cleanup=0.04),
                thread_factory=factory,
            )
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertEqual(result["reason_code"], "task_start_error")
            self.assertIn("stream:out", result["pending_identities"])
            self.assertTrue(factory.worker.is_alive())
            self.assertEqual(finalized, [])
            self.assertNotIn("PRIVATE_FACTORY_AFTER_START", json.dumps(result))
        finally:
            reader.release.set()
            if factory.worker is not None:
                factory.worker.join(1)

    def test_dynamic_terminate_callback_is_bound_once_and_exceptions_are_hidden(self):
        child = DynamicTerminatePropertyChild()
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec(
                "inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None,
            limits=short_limits(execution=0.04, cleanup=0.08),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(child.terminate_property_reads, 1)
        self.assertEqual(child.terminate_calls, 1)
        self.assertTrue(result["child_reaped"])
        self.assertNotIn("PRIVATE_TERMINATE_PROPERTY", json.dumps(result))

    def test_unstopped_consumer_returns_pending_identity_without_finalizing(self):
        child = FakeChild()
        reader = BlockingReader()
        finalized = []
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec("blocked", "stdout", reader, 16, cancel=lambda: None)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: finalized.append(True),
            limits=short_limits(execution=0.04, cleanup=0.04),
        )
        try:
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertIn("stream:blocked", result["pending_identities"])
            self.assertFalse(result["evidence_inventory_finalized"])
            self.assertEqual(finalized, [])
            self.assertEqual(child.terminate_calls, 1)
        finally:
            reader.release.set()

    def test_writer_exception_text_is_not_returned_and_blocks_inventory(self):
        child = FakeChild(0)
        marker = "PRIVATE_WRITER_EXCEPTION"

        def bad_write(_data):
            raise RuntimeError(marker)

        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec(
                "out", "stdout", io.BytesIO(b"payload"), 16,
                lambda data, sinks: sinks["writer"].write(data),
            )],
            writers=[capture.EvidenceWriterSpec("writer", 16, bad_write, lambda: None)],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: self.fail("inventory must not finalize after writer failure"),
            limits=short_limits(),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertIn(result["reason_code"], ("stream_consumer_error", "evidence_write_error"))
        self.assertNotIn(marker, json.dumps(result))
        self.assertFalse(result["evidence_inventory_finalized"])

    def test_evidence_writer_byte_cap_blocks_finalization(self):
        child = FakeChild(0)
        finalized = []
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec(
                "out", "stdout", io.BytesIO(b"payload"), 16,
                lambda data, sinks: sinks["writer"].write(data),
            )],
            writers=[capture.EvidenceWriterSpec("writer", 2, lambda data: len(data),
                                                 lambda: finalized.append("writer"))],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data),
                                                         lambda: finalized.append("inventory-writer")),
            finalize_evidence=lambda _sink: finalized.append("inventory-callback"),
            limits=short_limits(evidence=16),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "evidence_byte_limit")
        self.assertEqual(finalized, [])
        self.assertFalse(result["evidence_inventory_finalized"])

    def test_blocked_evidence_write_is_pending_and_never_finalized(self):
        child = FakeChild()
        release = threading.Event()
        inventory = []

        def blocked_write(data):
            release.wait()
            return len(data)

        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec(
                "out", "stdout", io.BytesIO(b"payload"), 16,
                lambda data, sinks: sinks["writer"].write(data),
                cancel=lambda: None,
            )],
            writers=[capture.EvidenceWriterSpec("writer", 16, blocked_write, lambda: None)],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: inventory.append(True),
            limits=short_limits(execution=0.04, cleanup=0.04),
        )
        try:
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertIn("stream:out", result["pending_identities"])
            self.assertIn("writer:writer", result["pending_identities"])
            writer_record = next(row for row in result["evidence_writers"]
                                 if row["identity"] == "writer")
            self.assertFalse(writer_record["sealed"])
            self.assertEqual(writer_record["state"], "UNKNOWN_PENDING_WRITER_LOCK")
            self.assertEqual(inventory, [])
            self.assertFalse(result["evidence_inventory_finalized"])
        finally:
            release.set()

    def test_hung_writer_finalizer_is_pending_and_inventory_is_not_started(self):
        child = FakeChild(0)
        release = threading.Event()
        inventory = []
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[],
            writers=[capture.EvidenceWriterSpec("slow", 16, lambda data: len(data),
                                                 lambda: release.wait())],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: inventory.append(True),
            limits=short_limits(execution=0.05, cleanup=0.04),
        )
        try:
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertIn("writer:slow", result["pending_identities"])
            self.assertFalse(result["evidence_inventory_finalized"])
            self.assertEqual(inventory, [])
        finally:
            release.set()

    def test_invalid_stderr_consumer_is_rejected_before_child_wait(self):
        child = FakeChild()
        result = capture.bounded_capture(
            child,
            child_identity="fake-child",
            streams=[capture.StreamSpec("err", "stderr", io.BytesIO(b"secret"), 16,
                                        consume=lambda *_: None)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16, lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None,
            limits=short_limits(),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "invalid_input")
        self.assertFalse(child.exited.is_set())
        self.assertEqual(child.terminate_calls, 0)

    def test_invalid_limits_and_byte_caps_fail_closed_with_unaccounted_child(self):
        invalid_limits = [
            capture.CaptureLimits(execution_seconds=float("nan")),
            capture.CaptureLimits(total_stream_bytes=True),
            capture.CaptureLimits(total_evidence_bytes=None),
        ]
        for limits in invalid_limits:
            child = FakeChild()
            result = capture.bounded_capture(
                child, child_identity="fake-child", streams=[], writers=[],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                            lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: None, limits=limits,
            )
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertEqual(result["reason_code"], "invalid_input")
            self.assertEqual(result["pending_identities"], ["child:fake-child"])
            self.assertEqual(result["child_accounting"], "UNCONFIRMED_RECEIVED_CHILD")
            self.assertFalse(child.exited.is_set())
            self.assertEqual(child.terminate_calls, 0)

        child = FakeChild()
        bad_clock = capture.bounded_capture(
            child, child_identity="fake-child", streams=[], writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None, limits=short_limits(),
            clock=lambda: float("nan"),
        )
        self.assertEqual(bad_clock["reason_code"], "clock_error")
        self.assertEqual(bad_clock["pending_identities"], ["child:fake-child"])
        self.assertEqual(child.terminate_calls, 0)

        for cap in (None, float("nan"), True):
            child = FakeChild()
            result = capture.bounded_capture(
                child, child_identity="fake-child",
                streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"x"), cap)],
                writers=[],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                            lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: None, limits=short_limits(),
            )
            self.assertEqual(result["reason_code"], "invalid_input")
            self.assertEqual(result["pending_identities"], ["child:fake-child"])

        for cap in (None, float("nan"), True):
            child = FakeChild()
            result = capture.bounded_capture(
                child, child_identity="fake-child", streams=[],
                writers=[capture.EvidenceWriterSpec("writer", cap, lambda data: len(data), lambda: None)],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                            lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: None, limits=short_limits(),
            )
            self.assertEqual(result["reason_code"], "invalid_input")
            self.assertEqual(result["pending_identities"], ["child:fake-child"])

    def test_clock_injection_is_shared_by_stream_worker_and_controller(self):
        child = FakeChild(0)
        result = capture.bounded_capture(
            child, child_identity="fake-child",
            streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"x"), 8)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None, limits=short_limits(), clock=lambda: 0.0,
        )
        self.assertEqual(result["state"], "CAPTURED_REGISTERED_SCOPE_ONLY", result)
        self.assertEqual(result["stream_records"][0]["bytes"], 1)

    def test_exact_stream_and_shared_caps_allow_eof_with_counted_probe(self):
        child = FakeChild(0)
        result = capture.bounded_capture(
            child, child_identity="fake-child",
            streams=[
                capture.StreamSpec("out", "stdout", io.BytesIO(b"ab"), 2),
                capture.StreamSpec("err", "stderr", io.BytesIO(b"cd"), 2),
            ],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None,
            limits=capture.CaptureLimits(total_stream_bytes=4, chunk_bytes=2),
        )
        self.assertEqual(result["state"], "CAPTURED_REGISTERED_SCOPE_ONLY", result)
        self.assertEqual(sum(row["bytes"] for row in result["stream_records"]), 4)
        self.assertEqual(result["limit_probe_bytes_total"], 0)
        self.assertTrue(all(row["limit_probe_bytes"] == 0 for row in result["stream_records"]))

    def test_one_byte_over_stream_cap_is_probed_but_never_retained(self):
        marker = "PRIVATE_OVER_CAP_SENTINEL"
        child = FakeChild(0)
        result = capture.bounded_capture(
            child, child_identity="fake-child",
            streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"four" + marker.encode()), 4)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: None, limits=short_limits(stream=16),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "stream_byte_limit")
        self.assertEqual(result["stream_records"][0]["bytes"], 4)
        self.assertEqual(result["stream_records"][0]["limit_probe_bytes"], 1)
        self.assertEqual(result["limit_probe_bytes_total"], 1)
        self.assertNotIn(marker, json.dumps(result))

    def test_boolean_writer_return_is_not_an_integer_byte_count(self):
        child = FakeChild(0)
        result = capture.bounded_capture(
            child, child_identity="fake-child",
            streams=[capture.StreamSpec(
                "out", "stdout", io.BytesIO(b"x"), 8,
                lambda data, sinks: sinks["writer"].write(data),
            )],
            writers=[capture.EvidenceWriterSpec("writer", 8, lambda _data: True, lambda: None)],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: self.fail("inventory must not finalize"),
            limits=short_limits(),
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "evidence_write_error")
        writer = next(row for row in result["evidence_writers"] if row["identity"] == "writer")
        self.assertEqual(writer["bytes_attempted"], 1)
        self.assertEqual(writer["accepted_bytes"], 0)
        self.assertFalse(result["evidence_inventory_finalized"])

    def test_partial_stream_start_failure_is_joined_or_reported_pending(self):
        child = FakeChild()
        reader = BlockingReader()
        factory = PartialStartStreamFactory()
        finalized = []
        try:
            result = capture.bounded_capture(
                child, child_identity="fake-child",
                streams=[capture.StreamSpec("out", "stdout", reader, 16)],
                writers=[],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                            lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: finalized.append(True),
                limits=short_limits(execution=0.04, cleanup=0.04), thread_factory=factory,
            )
            self.assertEqual(factory.names[:2], ["g0-child-wait", "g0-stream-out"])
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertEqual(result["reason_code"], "task_start_error")
            self.assertIn("stream:out", result["pending_identities"])
            self.assertEqual(child.terminate_calls, 1)
            self.assertEqual(finalized, [])
            self.assertNotIn("PRIVATE_PARTIAL_START_DETAIL", json.dumps(result))
        finally:
            reader.release.set()
            for thread in factory.threads:
                thread.join(1)

    def test_child_wait_start_failure_stops_before_stream_workers(self):
        child = FakeChild()
        factory = FailChildWaitFactory()
        result = capture.bounded_capture(
            child, child_identity="fake-child",
            streams=[capture.StreamSpec("out", "stdout", io.BytesIO(b"unused"), 16)],
            writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=lambda _sink: self.fail("must not finalize"),
            limits=short_limits(), thread_factory=factory,
        )
        self.assertEqual(result["state"], "UNKNOWN")
        self.assertEqual(result["reason_code"], "task_start_error")
        self.assertEqual(factory.names[0], "g0-child-wait")
        self.assertNotIn("g0-stream-out", factory.names)
        self.assertIn("child:fake-child", result["pending_identities"])
        self.assertEqual(result["launch_retries"], 0)
        self.assertNotIn("PRIVATE_CHILD_THREAD_SETUP", json.dumps(result))

    def test_partial_writer_finalizer_start_is_pending_and_blocks_inventory(self):
        child = FakeChild(0)
        release = threading.Event()
        factory = PartialStartWriterFactory()
        finalized = []
        try:
            result = capture.bounded_capture(
                child, child_identity="fake-child", streams=[],
                writers=[capture.EvidenceWriterSpec("slow", 16, lambda data: len(data),
                                                   lambda: release.wait())],
                inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                            lambda data: len(data), lambda: None),
                finalize_evidence=lambda _sink: finalized.append(True),
                limits=short_limits(execution=0.04, cleanup=0.03), thread_factory=factory,
            )
            self.assertEqual(result["state"], "UNKNOWN")
            self.assertEqual(result["reason_code"], "writer_finalize_error")
            self.assertIn("writer:slow", result["pending_identities"])
            self.assertEqual(finalized, [])
            self.assertNotIn("PRIVATE_PARTIAL_START_DETAIL", json.dumps(result))
        finally:
            release.set()
            for thread in factory.threads:
                thread.join(1)

    def test_success_does_not_claim_detached_callback_work_was_stopped(self):
        release = threading.Event()
        finished = threading.Event()
        detached = []

        def finalize(_sink):
            worker = threading.Thread(target=lambda: (release.wait(), finished.set()), daemon=True)
            detached.append(worker)
            worker.start()

        result = capture.bounded_capture(
            FakeChild(0), child_identity="fake-child", streams=[], writers=[],
            inventory_writer=capture.EvidenceWriterSpec("inventory", 16,
                                                        lambda data: len(data), lambda: None),
            finalize_evidence=finalize, limits=short_limits(),
        )
        try:
            self.assertEqual(result["state"], "CAPTURED_REGISTERED_SCOPE_ONLY")
            self.assertFalse(result["unregistered_work_proven_stopped"])
            self.assertIn("UNREGISTERED_WORK_IS_NOT_PROVEN_STOPPED",
                          result["callback_completion_contract"])
            self.assertFalse(finished.is_set())
        finally:
            release.set()
            for worker in detached:
                worker.join(1)

    def test_operational_entrypoint_is_hard_disabled(self):
        self.assertFalse(capture.OS_EXECUTION_ENABLED)
        self.assertEqual(capture.operational_main()["reason_code"], "os_execution_disabled")


if __name__ == "__main__":
    unittest.main(verbosity=2)

