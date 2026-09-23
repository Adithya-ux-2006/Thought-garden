import json
import os
import random
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAX_CHUNK = 2000
OVERLAP = 200


def _chunk_in_subprocess(texts, timeout=30):
    # A non-terminating chunker also grows its chunk list without bound, so it
    # runs in a child process that can be killed instead of a thread that can't.
    code = (
        'import json, sys\n'
        'from app.services.document_service import chunk_text\n'
        'texts = json.loads(sys.stdin.read())\n'
        'print(json.dumps([chunk_text(t) for t in texts]))\n'
    )
    try:
        proc = subprocess.run(
            [sys.executable, '-B', '-c', code],
            input=json.dumps(texts), capture_output=True, text=True,
            timeout=timeout, cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        pytest.fail('chunk_text did not terminate')
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _assert_valid_chunking(text, chunks):
    assert chunks, 'no chunks produced'
    assert all(0 < len(c) <= MAX_CHUNK for c in chunks)
    stripped = text.strip()
    assert stripped.startswith(chunks[0][:50])
    assert stripped.endswith(chunks[-1][-50:])
    assert len(chunks) <= len(text) // (MAX_CHUNK - OVERLAP) + 2


@pytest.mark.parametrize('text', [
    'a' * 2500,
    'A.' + 'x' * 3000,
    'Sentence number one. ' * 400,
    'line\n' * 1500,
    'x' * 1999 + '.' + 'y' * 5000,
], ids=['no-breaks', 'break-near-start', 'sentences', 'newlines', 'break-at-edge'])
def test_chunk_text_terminates_and_covers_text(text):
    [chunks] = _chunk_in_subprocess([text])
    _assert_valid_chunking(text, chunks)


def test_chunk_text_short_text_is_single_chunk():
    [chunks] = _chunk_in_subprocess(['Short note.'])
    assert chunks == ['Short note.']


def test_chunk_text_randomized_inputs_terminate():
    rng = random.Random(1234)
    alphabet = 'abcde  .\n'
    texts = [
        ''.join(rng.choice(alphabet) for _ in range(rng.randint(2001, 9000)))
        for _ in range(150)
    ]
    texts = [t for t in texts if t.strip()]
    results = _chunk_in_subprocess(texts, timeout=60)
    for text, chunks in zip(texts, results):
        _assert_valid_chunking(text, chunks)
