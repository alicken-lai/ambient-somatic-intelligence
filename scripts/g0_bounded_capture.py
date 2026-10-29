"""Fakeable lifecycle barrier for bounded G0 capture.

This module deliberately does not launch a process and is not imported by an
operational collector. A separately reviewed adapter may supply a child handle
and stream objects later. Stderr is always drained into a digest/count only.
Evidence finalization is withheld until the child is reaped and all registered
stream consumers have stopped. The helper cannot prove arbitrary callbacks
did not start detached work; success is explicitly limited to the caller's
registered synchronous-callback contract. Incomplete cleanup returns UNKNOWN
with safe pending identities and never retries launch or termination.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import queue
import re
import threading
import time
from typing import Callable, Mapping, Optional, Sequence


OS_EXECUTION_ENABLED = False
SCHEMA = "asi-g0-bounded-capture/v2"
CALLBACK_COMPLETION_CONTRACT = (
    "CALLER_ASSERTED_SYNCHRONOUS_REGISTERED_CALLBACKS_ONLY; "
    "UNREGISTERED_WORK_IS_NOT_PROVEN_STOPPED"
)
_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_MAX_STREAMS = 8
_MAX_WRITERS = 16
_MAX_ITEMS = _MAX_STREAMS + _MAX_WRITERS + 3
_MAX_SECONDS = 300.0
_MAX_CLEANUP_SECONDS = 10.0
_MAX_STREAM_BYTES = 256 * 1024 * 1024
_MAX_EVIDENCE_BYTES = 1024 * 1024 * 1024
_MAX_CHUNK_BYTES = 64 * 1024
_SAFE_FAILURES = {
    "evidence_write_error", "writer_lock_timeout", "writer_sealed",
    "evidence_byte_limit", "evidence_budget_exhausted", "writer_state_invalid",
    "writer_finalize_error", "stream_byte_limit", "stream_budget_exhausted",
    "stream_read_error", "stream_consumer_error", "capture_deadline", "clock_error",
}


class _CaptureFault(Exception):
    """Internal, fixed-vocabulary failure; exception text is never reported."""

    def __init__(self, code: str):
        self.code = code


@dataclass(frozen=True)
class CaptureLimits:
    execution_seconds: float = 30.0
    cleanup_seconds: float = 2.0
    total_stream_bytes: int = 16 * 1024 * 1024
    total_evidence_bytes: int = 64 * 1024 * 1024
    chunk_bytes: int = 64 * 1024

    def valid(self) -> bool:
        try:
            return (
                type(self.execution_seconds) in (int, float)
                and math.isfinite(self.execution_seconds)
                and 0 < self.execution_seconds <= _MAX_SECONDS
                and type(self.cleanup_seconds) in (int, float)
                and math.isfinite(self.cleanup_seconds)
                and 0 < self.cleanup_seconds <= _MAX_CLEANUP_SECONDS
                and type(self.total_stream_bytes) is int
                and 0 < self.total_stream_bytes <= _MAX_STREAM_BYTES
                and type(self.total_evidence_bytes) is int
                and 0 < self.total_evidence_bytes <= _MAX_EVIDENCE_BYTES
                and type(self.chunk_bytes) is int
                and 0 < self.chunk_bytes <= _MAX_CHUNK_BYTES
            )
        except BaseException:
            return False


@dataclass(frozen=True)
class StreamSpec:
    identity: str
    role: str  # "stdout" may be consumed; "stderr" is hash/count only.
    stream: object
    max_bytes: int
    consume: Optional[Callable[[bytes, Mapping[str, "EvidenceSink"]], None]] = None
    cancel: Optional[Callable[[], None]] = None


@dataclass(frozen=True)
class EvidenceWriterSpec:
    identity: str
    max_bytes: int
    write: Callable[[bytes], object]
    finalize: Callable[[], None]


class _ByteBudget:
    def __init__(self, maximum: int):
        self.maximum = maximum
        self.used = 0
        self._lock = threading.Lock()

    def reserve(self, maximum: int) -> int:
        with self._lock:
            amount = min(maximum, self.maximum - self.used)
            if amount <= 0:
                return 0
            self.used += amount
            return amount

    def release(self, amount: int) -> None:
        with self._lock:
            self.used = max(0, self.used - amount)


class EvidenceSink:
    """Synchronous, finite writer facade; raw writer handles stay private."""

    def __init__(self, spec: EvidenceWriterSpec, budget: _ByteBudget,
                 deadline: Callable[[], float], clock: Callable[[], float]):
        self.identity = spec.identity
        self._spec = spec
        self._budget = budget
        self._deadline = deadline
        self._clock = clock
        self._lock = threading.Lock()
        self._accepting = True
        self._attempted = False
        self._finalized = False
        self._bytes = 0
        self._accepted_bytes = 0
        self._digest = hashlib.sha256()

    def write(self, data: bytes) -> int:
        if not isinstance(data, bytes):
            raise _CaptureFault("evidence_write_error")
        remaining = self._deadline() - self._clock()
        if remaining <= 0:
            raise _CaptureFault("capture_deadline")
        if not self._lock.acquire(timeout=remaining):
            raise _CaptureFault("writer_lock_timeout")
        try:
            if not self._accepting:
                raise _CaptureFault("writer_sealed")
            if self._bytes + len(data) > self._spec.max_bytes:
                raise _CaptureFault("evidence_byte_limit")
            if self._budget.reserve(len(data)) != len(data):
                raise _CaptureFault("evidence_budget_exhausted")
            # Count before handing data to an opaque sink: a partial write or
            # exception is an UNKNOWN outcome, never a reason to retry.
            self._bytes += len(data)
            result = self._spec.write(data)
            if self._clock() >= self._deadline():
                # The underlying write may have completed late; it is UNKNOWN
                # and the facade is sealed against any subsequent write.
                self._accepting = False
                raise _CaptureFault("capture_deadline")
            if result is not None:
                if type(result) is not int or result != len(data):
                    raise _CaptureFault("evidence_write_error")
            self._accepted_bytes += len(data)
            self._digest.update(data)
            return len(data)
        except _CaptureFault:
            raise
        except BaseException:
            raise _CaptureFault("evidence_write_error") from None
        finally:
            self._lock.release()

    def _seal(self, timeout: float) -> bool:
        if not self._lock.acquire(timeout=max(0.0, timeout)):
            return False
        try:
            self._accepting = False
            return True
        finally:
            self._lock.release()

    def _finalize_once(self) -> None:
        remaining = self._deadline() - self._clock()
        if remaining <= 0 or not self._lock.acquire(timeout=remaining):
            raise _CaptureFault("writer_lock_timeout")
        try:
            if self._accepting or self._attempted:
                raise _CaptureFault("writer_state_invalid")
            self._attempted = True
        finally:
            self._lock.release()
        try:
            self._spec.finalize()
        except BaseException:
            raise _CaptureFault("writer_finalize_error") from None
        remaining = self._deadline() - self._clock()
        if remaining <= 0 or not self._lock.acquire(timeout=remaining):
            raise _CaptureFault("writer_lock_timeout")
        try:
            self._finalized = True
        finally:
            self._lock.release()

    def record(self) -> dict:
        if not self._lock.acquire(timeout=0):
            return {
                "identity": self.identity,
                "state": "UNKNOWN_PENDING_WRITER_LOCK",
                "bytes_attempted": None,
                "accepted_bytes": None,
                "sha256": None,
                "sealed": False,
                "finalize_attempted": self._attempted,
                "finalized": False,
            }
        try:
            return {
                "identity": self.identity,
                "state": "RECORDED",
                "bytes_attempted": self._bytes,
                "accepted_bytes": self._accepted_bytes,
                "sha256": self._digest.hexdigest(),
                "sealed": not self._accepting,
                "finalize_attempted": self._attempted,
                "finalized": self._finalized,
            }
        finally:
            self._lock.release()


@dataclass
class _Task:
    identity: str
    target: Callable[[], object]
    events: "queue.Queue[str]"
    thread_factory: Callable[..., object]
    thread: object = None
    value: object = None
    error_code: Optional[str] = None
    started: bool = False
    start_attempted: bool = False
    completed: bool = False
    factory_invoked: bool = False

    def start(self) -> bool:
        def entry():
            try:
                self.value = self.target()
            except _CaptureFault as exc:
                self.error_code = exc.code if exc.code in _SAFE_FAILURES else "callback_error"
            except BaseException:
                self.error_code = "callback_error"
            finally:
                self.completed = True
                self.events.put(self.identity)

        try:
            # An injected factory is not assumed side-effect-free: it could
            # start a worker and then raise before returning its handle.
            # From this point onward, lack of a returned handle is unknown,
            # never evidence that no worker exists.
            self.factory_invoked = True
            self.thread = self.thread_factory(target=entry, name="g0-" + self.identity)
            self.thread.daemon = True
            self.start_attempted = True
            self.thread.start()
            self.started = True
            return True
        except BaseException:
            self.error_code = "task_start_error"
            return False

    def may_have_started(self) -> bool:
        if self.started:
            return True
        if not self.factory_invoked:
            return False
        if self.thread is None:
            return True
        try:
            if self.thread.is_alive():
                return True
            return getattr(self.thread, "ident", None) is not None
        except BaseException:
            # An uninspectable thread state is conservatively treated as
            # possibly started; callers must keep its identity pending.
            return True

    def alive(self) -> bool:
        if not self.may_have_started():
            return False
        if self.thread is None:
            return True
        try:
            return bool(self.thread.is_alive())
        except BaseException:
            return True

    def join_if_started(self, timeout: float) -> bool:
        if not self.may_have_started():
            return True
        if self.thread is None:
            return False
        try:
            self.thread.join(timeout=max(0.0, timeout))
        except BaseException:
            return False
        return not self.alive()


def _safe_identity(value: object) -> bool:
    return isinstance(value, str) and _IDENTITY.fullmatch(value) is not None


def _stream_task(spec: StreamSpec, sinks: Mapping[str, EvidenceSink],
                 stream_budget: _ByteBudget, limits: CaptureLimits,
                 records: dict, record_lock: threading.Lock,
                 deadline: Callable[[], float],
                 clock: Callable[[], float]) -> Callable[[], None]:
    def run() -> None:
        digest = hashlib.sha256()
        count = 0
        probe_bytes = 0
        status = "READING"
        try:
            while True:
                remaining = spec.max_bytes - count
                if remaining <= 0:
                    # One non-retained sentinel distinguishes exact-cap EOF
                    # from overflow. Probe bytes have a separate <=1/stream
                    # bound and never reach consumers, sinks, or digests.
                    probe_bytes = None
                    try:
                        probe = spec.stream.read(1)
                    except BaseException:
                        raise _CaptureFault("stream_read_error") from None
                    if not isinstance(probe, bytes) or len(probe) > 1:
                        raise _CaptureFault("stream_read_error")
                    probe_bytes = len(probe)
                    if not probe:
                        probe_bytes = 0
                        status = "EOF"
                        break
                    probe_bytes = len(probe)
                    status = "LIMIT"
                    raise _CaptureFault("stream_byte_limit")
                request = stream_budget.reserve(min(limits.chunk_bytes, remaining))
                if not request:
                    # The shared retained-byte budget is exhausted. As above,
                    # one non-retained byte can only distinguish EOF from an
                    # aggregate overflow; it does not extend the budget.
                    probe_bytes = None
                    try:
                        probe = spec.stream.read(1)
                    except BaseException:
                        raise _CaptureFault("stream_read_error") from None
                    if not isinstance(probe, bytes) or len(probe) > 1:
                        raise _CaptureFault("stream_read_error")
                    probe_bytes = len(probe)
                    if not probe:
                        probe_bytes = 0
                        status = "EOF"
                        break
                    probe_bytes = len(probe)
                    status = "LIMIT"
                    raise _CaptureFault("stream_budget_exhausted")
                try:
                    data = spec.stream.read(request)
                except BaseException:
                    raise _CaptureFault("stream_read_error") from None
                if not isinstance(data, bytes) or len(data) > request:
                    raise _CaptureFault("stream_read_error")
                # Return unused reservation on short reads / EOF.
                stream_budget.release(request - len(data))
                if not data:
                    status = "EOF"
                    break
                count += len(data)
                digest.update(data)
                if spec.role == "stdout" and spec.consume is not None:
                    try:
                        spec.consume(data, sinks)
                    except _CaptureFault:
                        raise
                    except BaseException:
                        raise _CaptureFault("stream_consumer_error") from None
                if clock() >= deadline():
                    status = "LIMIT"
                    raise _CaptureFault("capture_deadline")
        except _CaptureFault:
            if status == "READING":
                status = "ERROR"
            raise
        except BaseException:
            status = "ERROR"
            raise _CaptureFault("stream_read_error") from None
        finally:
            with record_lock:
                records[spec.identity] = {
                    "identity": spec.identity,
                    "role": spec.role,
                    "bytes": count,
                    "sha256": digest.hexdigest(),
                    "state": status,
                    "limit_probe_bytes": probe_bytes,
                }

    return run


def _wait_for(tasks: Sequence[_Task], events: "queue.Queue[str]", deadline: float,
              clock: Callable[[], float]) -> Optional[str]:
    pending = {task.identity: task for task in tasks if task.alive()}
    reason = None
    # A task can finish just before the snapshot and already be represented in
    # the event queue. _Task.alive() plus the bounded join pass handles both
    # ordinary starts and wrappers that started a worker before raising.
    while pending:
        try:
            remaining = deadline - clock()
        except _CaptureFault as exc:
            reason = exc.code
            break
        if remaining <= 0:
            reason = "capture_deadline"
            break
        try:
            identity = events.get(timeout=remaining)
        except queue.Empty:
            reason = "capture_deadline"
            break
        pending.pop(identity, None)
        task = next((item for item in tasks if item.identity == identity), None)
        if task is not None and task.error_code:
            reason = task.error_code
            break
        # Drain duplicate/stale notifications without widening the deadline.
        pending = {item.identity: item for item in pending.values() if item.alive()}
    for task in tasks:
        if not task.may_have_started():
            continue
        try:
            remaining = deadline - clock()
        except _CaptureFault as exc:
            reason = reason or exc.code
            remaining = 0.0
        if remaining <= 0 or reason is not None:
            remaining = 0.0
        if not task.join_if_started(remaining):
            reason = reason or "capture_deadline"
    for task in tasks:
        if task.may_have_started() and task.error_code:
            reason = reason or task.error_code
    return reason


def _checked_clock(clock: Callable[[], float]) -> Callable[[], float]:
    lock = threading.Lock()
    previous = [None]

    def read() -> float:
        with lock:
            try:
                value = clock()
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise _CaptureFault("clock_error")
                if previous[0] is not None and value < previous[0]:
                    raise _CaptureFault("clock_error")
                previous[0] = value
                return float(value)
            except _CaptureFault:
                raise
            except BaseException:
                raise _CaptureFault("clock_error") from None

    return read


def _valid_byte_cap(value: object, maximum: int) -> bool:
    return type(value) is int and 0 < value <= maximum


def _bounded_remaining(deadline: float, clock: Callable[[], float]) -> Optional[float]:
    try:
        return max(0.0, deadline - clock())
    except _CaptureFault:
        return None


def bounded_capture(child: object, *, child_identity: str,
                    streams: Sequence[StreamSpec],
                    writers: Sequence[EvidenceWriterSpec],
                    inventory_writer: EvidenceWriterSpec,
                    finalize_evidence: Callable[[EvidenceSink], None],
                    limits: CaptureLimits = CaptureLimits(),
                    clock: Callable[[], float] = time.monotonic,
                    thread_factory: Callable[..., object] = threading.Thread) -> dict:
    """Coordinate an already-provided fakeable child and bounded stream workers.

    The adapter contract is intentionally narrow: ``child.wait(timeout)`` must
    return an integer exit code only once the direct child is reaped, and
    ``child.terminate_once()`` may affect only that direct child. This function
    never launches/retries a process. It observes only registered tasks. It
    cannot prove that arbitrary callbacks did not start detached/unregistered
    work, so a captured result is limited to a caller-asserted synchronous,
    registered-callback contract and is not a full-G0 or Gate result.
    """
    base = {
        "schema": SCHEMA,
        "state": "UNKNOWN",
        "reason_code": "invalid_input",
        "child_identity": child_identity if _safe_identity(child_identity) else "unknown-child",
        "child_accounting": "UNCONFIRMED_RECEIVED_CHILD",
        "child_exit_code": None,
        "child_reaped": False,
        "pending_identities": [],
        "termination_attempts": 0,
        "launch_retries": 0,
        "raw_stderr_retained": False,
        "stream_records": [],
        "stream_byte_semantics": "retained_bytes_only; at_most_one_nonretained_eof_or_overflow_probe_byte_per_stream",
        "limit_probe_bytes_total": 0,
        "evidence_writers": [],
        "evidence_inventory_finalized": False,
        "callback_completion_contract": CALLBACK_COMPLETION_CONTRACT,
        "unregistered_work_proven_stopped": False,
    }
    def invalid_result(reason: str = "invalid_input") -> dict:
        base["reason_code"] = reason
        base["pending_identities"] = ["child:" + base["child_identity"]]
        return base

    wait_callback = None
    terminate_callback = None
    try:
        wait_callback = getattr(child, "wait", None)
    except BaseException:
        pass
    try:
        # Bind this property once. A dynamic property must not be re-read at
        # failure time, where an exception could escape the bounded path.
        terminate_callback = getattr(child, "terminate_once", None)
    except BaseException:
        pass
    try:
        invalid = (
            type(limits) is not CaptureLimits or not isinstance(streams, (tuple, list))
            or not isinstance(writers, (tuple, list))
            or type(inventory_writer) is not EvidenceWriterSpec
            or any(type(s) is not StreamSpec for s in streams)
            or any(type(w) is not EvidenceWriterSpec for w in writers)
            or not _safe_identity(child_identity) or not limits.valid()
            or not callable(clock) or not callable(thread_factory)
            or not callable(wait_callback)
            or len(streams) > _MAX_STREAMS or len(writers) > _MAX_WRITERS
            or len(streams) + len(writers) > _MAX_ITEMS
        )
    except BaseException:
        invalid = True
    if invalid:
        return invalid_result()
    identities = [child_identity] + [s.identity for s in streams] + [w.identity for w in writers]
    identities.append(inventory_writer.identity)
    try:
        invalid = (
            any(not _safe_identity(item) for item in identities)
            or len(identities) != len(set(identities))
            or any(s.role not in ("stdout", "stderr") for s in streams)
            or len([s for s in streams if s.role == "stderr"]) > 1
            or len([s for s in streams if s.role == "stdout"]) > 1
            or any(not _valid_byte_cap(s.max_bytes, limits.total_stream_bytes) for s in streams)
            or any((s.role == "stderr" and s.consume is not None) for s in streams)
            or any(not _valid_byte_cap(w.max_bytes, limits.total_evidence_bytes) for w in writers)
            or not _valid_byte_cap(inventory_writer.max_bytes, limits.total_evidence_bytes)
            or not callable(finalize_evidence)
        )
    except BaseException:
        invalid = True
    if invalid:
        return invalid_result()

    clock = _checked_clock(clock)
    try:
        started_at = clock()
    except _CaptureFault as exc:
        return invalid_result(exc.code)
    deadline = lambda: started_at + limits.execution_seconds
    cleanup_deadline = lambda: deadline() + limits.cleanup_seconds
    events: "queue.Queue[str]" = queue.Queue()
    stream_budget = _ByteBudget(limits.total_stream_bytes)
    evidence_budget = _ByteBudget(limits.total_evidence_bytes)
    all_writer_specs = list(writers) + [inventory_writer]
    sinks = {spec.identity: EvidenceSink(spec, evidence_budget, deadline, clock)
             for spec in all_writer_specs}
    stream_records: dict = {}
    record_lock = threading.Lock()
    tasks: list[_Task] = []
    child_task = _Task("child-wait", lambda: wait_callback(
                           timeout=limits.execution_seconds + limits.cleanup_seconds),
                       events, thread_factory)
    tasks.append(child_task)
    for spec in streams:
        tasks.append(_Task("stream-" + spec.identity,
                           _stream_task(spec, sinks, stream_budget, limits, stream_records,
                                        record_lock, deadline, clock), events, thread_factory))
    reason = None
    started_tasks: list[_Task] = []
    child_reaped = False
    exit_code = None

    # Child wait and all stream consumers are observed in one finite phase.
    for task in tasks:
        started_tasks.append(task)
        if not task.start():
            reason = "task_start_error"
            break
    if reason is None:
        reason = _wait_for(started_tasks, events, deadline(), clock)
    if child_task.completed and type(child_task.value) is int:
        exit_code = child_task.value
        child_reaped = True
        if child_task.error_code and reason is None:
            reason = child_task.error_code
    elif child_task.completed and child_task.error_code is None:
        reason = reason or "child_wait_timeout"
    elif child_task.error_code:
        reason = reason or "child_wait_error"
    for task in started_tasks:
        if task.error_code and task.identity != "child-wait":
            reason = reason or task.error_code
    if child_reaped and exit_code != 0:
        reason = reason or "child_nonzero_exit"

    termination_attempts = 0
    pending: set[str] = set()
    if reason is not None:
        # Exactly one direct-child termination attempt; never kill a tree and
        # never retry a failed termination. The wait worker already owns the
        # single bounded reap observation.
        if not child_reaped and callable(terminate_callback):
            terminate_task = _Task("child-terminate", terminate_callback, events, thread_factory)
            terminate_started = terminate_task.start()
            if terminate_task.may_have_started():
                termination_attempts = 1
                _wait_for([terminate_task], events, cleanup_deadline(), clock)
            if not terminate_started:
                reason = "child_terminate_error"
                pending.add("child-terminate:" + child_identity)
            elif terminate_task.error_code:
                reason = "child_terminate_error"
            if terminate_task.alive():
                pending.add("child-terminate:" + child_identity)
        # A caller-provided cancel callback may close only its associated stream.
        # It runs once in a bounded helper; a live helper/consumer is reported.
        cancel_tasks = []
        for spec in streams:
            worker = next((t for t in started_tasks if t.identity == "stream-" + spec.identity), None)
            if worker and worker.alive() and spec.cancel is not None:
                cancel_tasks.append(_Task("cancel-" + spec.identity, spec.cancel, events, thread_factory))
        for task in cancel_tasks:
            if not task.start():
                pending.add("cancel:" + task.identity.removeprefix("cancel-"))
        if cancel_tasks:
            _wait_for([task for task in cancel_tasks if task.may_have_started()],
                      events, cleanup_deadline(), clock)
            for task in cancel_tasks:
                if task.alive():
                    pending.add("cancel:" + task.identity.removeprefix("cancel-"))
        _wait_for(started_tasks, events, cleanup_deadline(), clock)
        if child_task.alive() or not child_reaped:
            # A completed child-wait result is the only proof of reap.
            if child_task.alive() or child_task.error_code or child_task.value is None:
                pending.add("child:" + child_identity)
        for task in started_tasks:
            if task.alive() and task.identity.startswith("stream-"):
                pending.add("stream:" + task.identity[len("stream-"):])
        # Seal writer facades only after bounded worker cleanup. If a write is
        # still in flight, the lock timeout leaves a pending writer identity.
        for sink in sinks.values():
            remaining = _bounded_remaining(cleanup_deadline(), clock)
            if remaining is None:
                reason = reason or "clock_error"
                pending.add("writer:" + sink.identity)
            elif not sink._seal(remaining):
                pending.add("writer:" + sink.identity)
    else:
        # Successful capture barrier: child has been reaped and every managed
        # stream consumer has stopped before any evidence finalization begins.
        for spec in writers:
            sink = sinks[spec.identity]
            remaining = _bounded_remaining(deadline(), clock)
            if remaining is None:
                reason = "clock_error"
                pending.add("writer:" + sink.identity)
            elif not sink._seal(remaining):
                reason = "writer_seal_incomplete"
                pending.add("writer:" + sink.identity)
        if reason is None:
            finalize_tasks = [
                _Task("writer-finalize-" + spec.identity, sinks[spec.identity]._finalize_once,
                      events, thread_factory)
                for spec in writers
            ]
            for task in finalize_tasks:
                if not task.start():
                    reason = "writer_finalize_error"
                    pending.add("writer:" + task.identity[len("writer-finalize-"):])
                    break
            if reason is None:
                reason = _wait_for(finalize_tasks, events, deadline(), clock)
                if reason:
                    reason = "writer_finalize_error" if reason != "capture_deadline" else reason
                elif any(task.error_code for task in finalize_tasks):
                    reason = "writer_finalize_error"
            if reason is not None:
                _wait_for(finalize_tasks, events, cleanup_deadline(), clock)
                for task in finalize_tasks:
                    if task.alive():
                        pending.add("writer:" + task.identity[len("writer-finalize-"):])
            if reason is None:
                inventory_sink = sinks[inventory_writer.identity]
                inventory_task = _Task("evidence-inventory",
                                       lambda: finalize_evidence(inventory_sink),
                                       events, thread_factory)
                if not inventory_task.start():
                    reason = "evidence_finalize_error"
                    pending.add("evidence-inventory")
                    if inventory_task.may_have_started():
                        _wait_for([inventory_task], events, cleanup_deadline(), clock)
                    if inventory_task.alive():
                        pending.add("evidence-inventory")
                else:
                    reason = _wait_for([inventory_task], events, deadline(), clock)
                    if inventory_task.alive():
                        pending.add("evidence-inventory")
                    if inventory_task.error_code:
                        reason = "evidence_finalize_error"
                    if reason == "capture_deadline":
                        reason = "evidence_finalize_timeout"
                    if reason is not None and inventory_task.alive():
                        _wait_for([inventory_task], events, cleanup_deadline(), clock)
                        if inventory_task.alive():
                            pending.add("evidence-inventory")
                    if reason is None:
                        remaining = _bounded_remaining(deadline(), clock)
                        if remaining is None:
                            reason = "clock_error"
                            pending.add("writer:" + inventory_writer.identity)
                        elif not inventory_sink._seal(remaining):
                            reason = "writer_seal_incomplete"
                            pending.add("writer:" + inventory_writer.identity)
                        if reason is None:
                            inventory_finalize = _Task(
                                "writer-finalize-" + inventory_writer.identity,
                                inventory_sink._finalize_once, events, thread_factory)
                            if not inventory_finalize.start():
                                reason = "writer_finalize_error"
                                pending.add("writer:" + inventory_writer.identity)
                                if inventory_finalize.may_have_started():
                                    _wait_for([inventory_finalize], events,
                                              cleanup_deadline(), clock)
                                if inventory_finalize.alive():
                                    pending.add("writer:" + inventory_writer.identity)
                            else:
                                reason = _wait_for([inventory_finalize], events, deadline(), clock)
                                if inventory_finalize.alive():
                                    pending.add("writer:" + inventory_writer.identity)
                                if inventory_finalize.error_code:
                                    reason = "writer_finalize_error"
                                elif reason == "capture_deadline":
                                    reason = "evidence_finalize_timeout"
                                if reason is not None and inventory_finalize.alive():
                                    _wait_for([inventory_finalize], events,
                                              cleanup_deadline(), clock)
                                    if inventory_finalize.alive():
                                        pending.add("writer:" + inventory_writer.identity)
                                if reason is None:
                                    base["evidence_inventory_finalized"] = True
                    if reason is not None:
                        # A timed-out inventory producer may still hold its
                        # sink. Seal once with the bounded cleanup allowance;
                        # never finalize or re-enter the callback afterward.
                        remaining = _bounded_remaining(cleanup_deadline(), clock)
                        if remaining is None or not inventory_sink._seal(remaining):
                            pending.add("writer:" + inventory_writer.identity)

    if reason is None and child_reaped and exit_code == 0 and not pending:
        base["state"] = "CAPTURED_REGISTERED_SCOPE_ONLY"
        base["reason_code"] = "capture_complete_registered_scope_only"
    else:
        base["state"] = "UNKNOWN"
        base["reason_code"] = reason or "cleanup_incomplete"
    if child_task.completed and type(child_task.value) is int:
        exit_code = child_task.value
        child_reaped = True
    base.update({
        "child_exit_code": exit_code,
        "child_reaped": child_reaped,
        "child_accounting": "REAPED" if child_reaped else "PENDING_OR_UNCONFIRMED",
        "pending_identities": sorted(pending),
        "termination_attempts": termination_attempts,
        "stream_records": [stream_records[k] for k in sorted(stream_records)],
        "evidence_writers": [sinks[k].record() for k in sorted(sinks)],
    })
    probes = [row["limit_probe_bytes"] for row in base["stream_records"]]
    base["limit_probe_bytes_total"] = (
        None if any(type(value) is not int for value in probes) else sum(probes)
    )
    return base


def operational_main(*_args, **_kwargs) -> dict:
    """Hard block until a separate reviewed adapter and authorization exist."""
    return {
        "schema": SCHEMA,
        "state": "UNKNOWN",
        "reason_code": "os_execution_disabled",
        "os_execution_enabled": False,
        "launch_retries": 0,
    }

