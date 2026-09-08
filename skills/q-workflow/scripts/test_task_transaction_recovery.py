"""Temp-only cancellation and abrupt-process recovery tests; no real profile access."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import q_workflow_manager as manager
from workflow_file_ops import acquire_lock, release_lock, transaction_journal_path, WorkflowFileLockError


def fixture(root):
    hub = root / 'hub'
    state = hub / 'personal-state'
    runtime = root / 'codex/q-personal-state'
    state.mkdir(parents=True)
    runtime.mkdir(parents=True)
    source = root / 'source'
    (source / 'skills').mkdir(parents=True)
    for folder in (state, runtime):
        (folder / 'ACTIVE_WORK.md').write_text('# Active Work\n\n## Current Focus\n\n- No active blocking focus.\n', encoding='utf-8')
        (folder / 'TODO.md').write_text('# TODO\n\n## Open\n\n## Closed\n', encoding='utf-8')
        (folder / 'TODO_DISPLAY.zh-CN.json').write_text('{}\n', encoding='utf-8')
    profile = root / 'profile.json'
    profile.write_text(json.dumps({'hub': str(hub), 'repositories': {'q-workflow-hub': {'path': str(source)}}}), encoding='utf-8')
    record = {
        'format_version': 1, 'schema': manager.TASK_SCHEMA, 'task_id': 'fixture-task',
        'trace_id': 'FIXTURE-TRANSACTION', 'execution_epoch': 1, 'state_revision': 'r1',
        'authority_event': 'fixture-register', 'work_state': 'briefing',
        'integrity_state': 'local-validated', 'release_state': 'local-only',
        'role_plan': {'id': 'fixture-role', 'primary': {'owner': 'main', 'status': 'planned'},
                      'reviewer': {'owner': 'reviewer', 'status': 'pending'},
                      'validator': {'owner': 'validator', 'status': 'pending'}},
        'remote': {'status': 'unproven', 'proven': False}, 'next_action': 'Review fixture.',
        'updated_at': '2026-09-08T10:00:00+00:00', 'focus': {'summary': 'Fixture only.'},
    }
    return profile, record


def snapshot(plan):
    return {name: Path(row['path']).read_bytes() if Path(row['path']).is_file() else None
            for name, row in plan['targets'].items()}


def crash_child(root, write_number, external_kill=False):
    os.environ['CODEX_HOME'] = str(root / 'codex')
    profile = root / 'profile.json'
    plan = json.loads((root / 'plan.json').read_text())
    target_paths = {Path(row['path']) for row in plan['targets'].values()}
    target_paths.add(manager._transaction_receipt_path(root / 'hub', plan['plan_id']))
    original = manager.atomic_replace_bytes
    count = 0
    def crash(path, value, *args, **kwargs):
        nonlocal count
        original(path, value, *args, **kwargs)
        if path in target_paths:
            count += 1
            if count == write_number:
                if external_kill:
                    (root / 'kill-ready').write_text('ready')
                    time.sleep(30)  # Parent kills this disposable process after the marker.
                os._exit(73)
    manager.atomic_replace_bytes = crash
    manager.apply_task_plan(profile, plan, yes=True)
    raise AssertionError('crash point was not reached')


class TransactionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='q-transaction-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'CODEX_HOME': str(self.root / 'codex'), 'Q_PROFILE_PATH': str(self.root / 'profile.json')})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.profile, record = fixture(self.root)
        self.plan = manager.build_task_plan(self.profile, record, focus_text='Fixture only.')
        self.before = snapshot(self.plan)
        self.lock = self.root / 'hub/personal-state/.q-workflow-manager.lock'
        self.journal = transaction_journal_path(self.lock)
        self.receipt = manager._transaction_receipt_path(self.root / 'hub', self.plan['plan_id'])
        (self.root / 'plan.json').write_text(json.dumps(self.plan), encoding='utf-8')

    def crash(self, count):
        result = subprocess.run([sys.executable, '-B', __file__, '--crash-child', str(self.root), str(count)],
                                capture_output=True, text=True, timeout=20, env=os.environ.copy())
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertTrue(self.journal.is_file())

    def test_normal_commit_and_replay(self):
        receipt = manager.apply_task_plan(self.profile, self.plan, yes=True)
        self.assertFalse(self.journal.exists())
        self.assertFalse(receipt['idempotent_replay'])
        self.assertTrue(manager.apply_task_plan(self.profile, self.plan, yes=True)['idempotent_replay'])

    def test_interrupting_commit_marker_cleanup_never_rolls_back_without_journal(self):
        for after in (False, True):
            original = Path.unlink
            def interrupt(path, *args, **kwargs):
                if path == self.journal:
                    if after:
                        original(path, *args, **kwargs)
                    raise KeyboardInterrupt('commit marker cleanup')
                return original(path, *args, **kwargs)
            with patch.object(Path, 'unlink', interrupt), self.assertRaises(KeyboardInterrupt):
                manager.apply_task_plan(self.profile, self.plan, yes=True)
            self.assertTrue(self.receipt.exists())
            self.assertTrue(manager._targets_already_applied(self.plan['targets']))
            if after:
                self.assertFalse(self.journal.exists())
                self.assertTrue(manager.apply_task_plan(self.profile, self.plan, yes=True)['idempotent_replay'])
            else:
                self.assertTrue(self.journal.exists())
                manager.recover_task_transaction(self.profile, yes=True)
                self.assertEqual(snapshot(self.plan), self.before)

    def test_crash_restores_preexisting_task_and_event_bytes(self):
        manager.apply_task_plan(self.profile, self.plan, yes=True)
        record = copy.deepcopy(self.plan['record'])
        record.update(state_revision='r2', authority_event='fixture-update', updated_at='2026-09-08T10:01:00+00:00')
        self.plan = manager.build_task_plan(self.profile, record, focus_text='Updated fixture.')
        self.before = snapshot(self.plan)
        (self.root / 'plan.json').write_text(json.dumps(self.plan), encoding='utf-8')
        self.crash(2)
        manager.recover_task_transaction(self.profile, yes=True)
        self.assertEqual(snapshot(self.plan), self.before)

    def test_interruptions_before_and_after_each_replacement(self):
        target_paths = {Path(row['path']) for row in self.plan['targets'].values()} | {self.receipt}
        for error in (KeyboardInterrupt, SystemExit, OSError):
            for after in (False, True):
                for fail_at in range(1, len(target_paths) + 1):
                    with self.subTest(error=error.__name__, after=after, fail_at=fail_at):
                        original = manager.atomic_replace_bytes
                        count = 0
                        fired = False
                        def interrupt(path, value, *args, **kwargs):
                            nonlocal count, fired
                            if path in target_paths and not fired:
                                count += 1
                                if count == fail_at:
                                    fired = True
                                    if after:
                                        original(path, value, *args, **kwargs)
                                    raise error('injected')
                            return original(path, value, *args, **kwargs)
                        with patch.object(manager, 'atomic_replace_bytes', interrupt), self.assertRaises(error):
                            manager.apply_task_plan(self.profile, self.plan, yes=True)
                        self.assertEqual(snapshot(self.plan), self.before)
                        self.assertFalse(self.receipt.exists())
                        self.assertFalse(self.journal.exists())

    def test_process_exit_after_each_replacement_and_shared_lock_block(self):
        for fail_at in range(1, len(self.plan['targets']) + 2):
            with self.subTest(fail_at=fail_at):
                self.crash(fail_at)
                with self.assertRaises(WorkflowFileLockError):
                    acquire_lock(self.lock)
                with self.assertRaises(WorkflowFileLockError):
                    manager.apply_task_plan(self.profile, self.plan, yes=True)
                self.assertEqual(manager.recover_task_transaction(self.profile, yes=True)['status'], 'recovered')
                self.assertEqual(snapshot(self.plan), self.before)
                self.assertFalse(self.receipt.exists())
                self.assertFalse(self.journal.exists())

    def test_corrupt_journal_blocks_without_writes(self):
        self.crash(1)
        before = snapshot(self.plan)
        self.journal.write_text('{bad json', encoding='utf-8')
        with self.assertRaises(manager.TaskStateError):
            manager.recover_task_transaction(self.profile, yes=True)
        self.assertEqual(snapshot(self.plan), before)
        self.assertTrue(self.journal.exists())

    def test_external_process_kill_after_each_replacement(self):
        for fail_at in range(1, len(self.plan['targets']) + 2):
            with self.subTest(fail_at=fail_at):
                ready = self.root / 'kill-ready'
                ready.unlink(missing_ok=True)
                child = subprocess.Popen([sys.executable, '-B', __file__, '--kill-child', str(self.root), str(fail_at)],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ.copy())
                try:
                    deadline = time.monotonic() + 10
                    while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                        time.sleep(.02)
                    self.assertTrue(ready.exists(), 'child did not reach kill point')
                    child.kill()
                    child.communicate(timeout=5)
                finally:
                    if child.poll() is None:
                        child.kill()
                    child.communicate(timeout=5)
                self.assertTrue(self.journal.exists())
                manager.recover_task_transaction(self.profile, yes=True)
                self.assertEqual(snapshot(self.plan), self.before)
                self.assertFalse(self.receipt.exists())

    def test_interrupted_recovery_retains_journal_and_can_retry(self):
        self.crash(6)
        original = manager.atomic_replace_bytes
        fired = False
        def interrupt(path, value, *args, **kwargs):
            nonlocal fired
            original(path, value, *args, **kwargs)
            if not fired:
                fired = True
                raise KeyboardInterrupt('recovery interrupted')
        with patch.object(manager, 'atomic_replace_bytes', interrupt), self.assertRaises(KeyboardInterrupt):
            manager.recover_task_transaction(self.profile, yes=True)
        self.assertTrue(self.journal.exists())
        with self.assertRaises(WorkflowFileLockError):
            acquire_lock(self.lock)
        manager.recover_task_transaction(self.profile, yes=True)
        self.assertEqual(snapshot(self.plan), self.before)
        self.assertFalse(self.journal.exists())

    def test_drift_blocks_all_restore_writes(self):
        self.crash(2)
        path = Path(next(iter(self.plan['targets'].values()))['path'])
        path.write_bytes(b'external edit')
        before = snapshot(self.plan)
        with self.assertRaises(manager.TaskStateError):
            manager.recover_task_transaction(self.profile, yes=True)
        self.assertEqual(snapshot(self.plan), before)
        self.assertTrue(self.journal.exists())

    def test_recovery_requires_yes_and_exclusive_lock(self):
        self.crash(1)
        with self.assertRaises(manager.TaskStateError):
            manager.recover_task_transaction(self.profile, yes=False)
        held = acquire_lock(self.lock, recovery=True)
        try:
            with self.assertRaises(WorkflowFileLockError):
                manager.recover_task_transaction(self.profile, yes=True)
        finally:
            release_lock(self.lock, held)

    def test_journal_path_escape_even_with_recomputed_hash_is_rejected(self):
        self.crash(1)
        journal = json.loads(self.journal.read_text())
        plan = journal['plan']
        first = next(iter(plan['targets'].values()))
        first['path'] = str(self.root / 'outside.txt')
        plan.pop('plan_id')
        plan['plan_id'] = manager.sha256_bytes(manager.canonical_json_bytes(plan))
        journal.pop('sha256')
        journal['sha256'] = manager.sha256_bytes(manager.canonical_json_bytes(journal))
        self.journal.write_text(json.dumps(journal), encoding='utf-8')
        before = snapshot(self.plan)
        with self.assertRaises(manager.TaskStateError):
            manager.recover_task_transaction(self.profile, yes=True)
        self.assertEqual(snapshot(self.plan), before)
        self.assertFalse((self.root / 'outside.txt').exists())


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--crash-child', '--kill-child'):
        crash_child(Path(sys.argv[2]), int(sys.argv[3]), sys.argv[1] == '--kill-child')
    else:
        unittest.main()
