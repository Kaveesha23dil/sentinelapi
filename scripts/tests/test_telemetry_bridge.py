"""Host bridge simulations: no Docker access and no live success claims."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bridge_api_logs as bridge
from traffic_collector.config import Config

CONFIG = Config('f0d23a14-460c-4441-9c76-0f39bfd2efb3', 'DemoCommerceAPI', '/democommerceapi', '1.0.0')
LINE = (b'[2026-10-22 10:00:00,000]  INFO {API_LOG} DemoCommerceAPI - '
        b'{"flow":"RESPONSE_OUT","verb":"GET","apiTo":"/democommerceapi/1.0.0/health",'
        b'"correlationId":"be73ac04-fae9-4f03-9534-9e1c55ee82d6","statusCode":200}\n')


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)/'checkpoint.json'
        self.files = {'api.log': ('1', LINE)}
        self.uploads = []
        self.accept = True
        self.calls = []

    def tearDown(self):
        self.directory.cleanup()

    def docker(self, *args):
        self.calls.append(args)
        command = args[2]
        if command == 'find':
            return ''.join(f'{inode} {len(data)} {name}\n' for name, (inode, data) in self.files.items()).encode()
        if command == 'head':
            return self.files[args[-1].split('/')[-1]][1][:64]
        if command == 'stat':
            inode, data = self.files[args[-1].split('/')[-1]]
            return f'{inode} {len(data)}'.encode()
        if command == 'dd':
            name = next(value[3:] for value in args if value.startswith('if=')).split('/')[-1]
            offset = int(next(value[5:] for value in args if value.startswith('skip=')))
            return self.files[name][1][offset:offset+65536]
        raise AssertionError('Unexpected Docker operation')

    def upload(self, *args, **kwargs):
        self.uploads.append(json.loads(kwargs['input']))
        class Result:
            returncode = 0 if self.accept else 1
        return Result()

    def poll(self):
        with patch.object(bridge, 'docker', self.docker), patch.object(bridge.subprocess, 'run', self.upload), contextlib.redirect_stdout(io.StringIO()):
            bridge.poll(CONFIG, self.path)

    def test_source_offset_only_after_durable_transport(self):
        self.accept = False
        with self.assertRaises(RuntimeError):
            self.poll()
        self.assertFalse(self.path.exists())
        self.accept = True
        self.poll()
        self.assertEqual(json.loads(self.path.read_text())['1']['offset'], len(LINE))

    def test_rename_rotation_drains_old_and_reads_new(self):
        self.poll()
        self.files = {'api-10-22-2026-1.log': ('1', LINE), 'api.log': ('2', LINE.replace(b'10:00:00', b'10:01:00'))}
        self.poll()
        self.assertEqual(len(self.uploads[-1]['flows']), 1)
        self.assertEqual(set(json.loads(self.path.read_text())), {'1', '2'})

    def test_truncated_final_record_is_retained(self):
        self.files = {'api.log': ('1', LINE[:-5])}
        self.poll()
        self.assertFalse(self.path.exists())
        self.files = {'api.log': ('1', LINE)}
        self.poll()
        self.assertEqual(len(self.uploads[-1]['flows']), 1)

    def test_copytruncate_fingerprint_starts_new_generation(self):
        self.poll()
        self.files = {'api.log': ('1', LINE.replace(b'10:00:00', b'10:02:00'))}
        self.poll()
        self.assertEqual(len(self.uploads[-1]['flows']), 1)

    def test_e2e_retries_a_busy_bridge_lock(self):
        import verify_telemetry_e2e as proof
        with patch.object(proof, 'poll', side_effect=[OSError('busy'), None]) as polling, patch.object(proof.time, 'sleep') as pause:
            proof.drain(CONFIG)
        self.assertEqual(polling.call_count, 2)
        pause.assert_called_once_with(1)
