"""Step 2d official, bounded-range HDF5 audit only; no detector or policy run.

Range blocks and full observation arrays stay in --raw-dir (ignored data/).
The tracked JSON is schema/metadata and smoke checks, never policy input.
"""
import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import requests

ARTICLE_API = 'https://api.figshare.com/v2/articles/13385936/versions/1'
BUDGET = 64 * 1024**2
PAGE = 65536


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


class OfficialRangeFile(io.RawIOBase):
    """Never accepts a whole-file 200 response, wrong range or oversized read."""
    def __init__(self, info, cache_dir, session=None, budget=BUDGET):
        if info['download_url'] != f"https://ndownloader.figshare.com/files/{info['id']}":
            raise ValueError('not the official API download URL')
        self.info, self.size, self.pos = info, info['size'], 0
        self.root = Path(cache_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.budget = budget
        self.transferred = 0
        self.blocks = {}
        self.ledger = self.root / 'hashes.json'
        self.hashes = json.loads(self.ledger.read_text()) if self.ledger.exists() else {}
        # First audit hashes prior exact-range probe files, without claiming full-file verification.
        for p in self.root.glob('*.bin'):
            a, b = map(int, p.stem.split('-'))
            if a % PAGE or b != min(a + PAGE, self.size) - 1:
                raise ValueError('invalid cached byte-range')
            data = p.read_bytes()
            if len(data) != b - a + 1:
                raise ValueError('truncated cache')
            h = sha256(data)
            if p.name in self.hashes and self.hashes[p.name] != h:
                raise ValueError('cache hash mismatch')
            self.hashes[p.name] = h
        if sum(p.stat().st_size for p in self.root.glob('*.bin')) > budget:
            raise ValueError('cache exceeds budget')
        write_json(self.ledger, self.hashes)

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        if whence not in (0, 1, 2):
            raise ValueError('invalid whence')
        p = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if p < 0:
            raise ValueError('negative seek')
        self.pos = p
        return p

    def _block(self, a, b):
        name = f'{a}-{b}.bin'
        p = self.root / name
        if p.exists():
            data = p.read_bytes()
            if len(data) != b - a + 1 or sha256(data) != self.hashes.get(name):
                raise ValueError('cached range changed')
            return data
        # Include rejected responses in the transfer budget; no silent whole-file fallback.
        if self.transferred + 3 * (b-a+1) > self.budget:
            raise ValueError('transfer budget exceeded')
        if sum(x.stat().st_size for x in self.root.glob('*.bin')) + b-a+1 > self.budget:
            raise ValueError('cache budget exceeded')
        for attempt in range(3):
            with self.session.get(self.info['download_url'],
                                  headers={'Range': f'bytes={a}-{b}'},
                                  stream=True, timeout=30) as response:
                if response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {a}-{b}/{self.size}':
                    if attempt == 2:
                        raise ValueError(f'exact range refused: HTTP {response.status_code}')
                    continue  # do not read response body
                data = response.raw.read(b-a+2)
                self.transferred += len(data)
                if len(data) != b-a+1:
                    raise ValueError('range length mismatch')
                p.write_bytes(data)
                self.hashes[name] = sha256(data)
                write_json(self.ledger, self.hashes)
                return data
        raise ValueError('unreachable')

    def read(self, n=-1):
        n = min(self.size-self.pos, n if n >= 0 else self.size-self.pos)
        if n <= 0:
            return b''
        if n > 16 * 1024**2:
            raise ValueError('oversized HDF5 read denied')
        out = bytearray()
        while n:
            a = self.pos // PAGE * PAGE
            b = min(a+PAGE, self.size)-1
            if a not in self.blocks:
                self.blocks[a] = self._block(a, b)
            data = self.blocks[a]
            offset = self.pos-a
            k = min(n, len(data)-offset)
            out.extend(data[offset:offset+k])
            self.pos += k
            n -= k
        return bytes(out)

    def readinto(self, b):
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)


def observations(processdata):
    """Policy-side adapter: values only. No attrs, path, mode, seed or labels."""
    data = np.asarray(processdata, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] != 54 or len(data) < 2:
        raise ValueError('unexpected original processdata schema')
    t, x = data[:, 0].copy(), data[:, 1:].copy()
    if not np.isfinite(data).all() or not np.all(np.diff(t) > 0):
        raise ValueError('non-finite data or non-increasing timestamps')
    if not np.allclose(np.diff(t), .05, atol=1e-8, rtol=0):
        raise ValueError('not 3-minute sampling')
    return t, x


def evaluator_states(t, *, start, duration, kind, warmup_end=None,
                     axes_verified=False, settled_at=None, stopped=False):
    """Half-open metadata intervals only. Unknown semantics never become normal."""
    t = np.asarray(t, dtype=float)
    states = np.full(len(t), 'UNKNOWN', dtype='<U24')
    if stopped or not axes_verified or warmup_end is None:
        return states
    if kind not in ('fault', 'transition') or not np.isfinite([start, duration, warmup_end]).all() or duration < 0 or warmup_end > start:
        raise ValueError('invalid event boundary')
    states[t < warmup_end] = 'WARMUP_EXCLUDED'
    states[(t >= warmup_end) & (t < start)] = 'NORMAL_A'
    if kind == 'fault':
        states[t >= start] = 'FAULT'
    else:
        end = start + duration
        states[(t >= start) & (t < end)] = 'TRANSITION'
        states[t >= end] = 'POST_RAMP_UNVERIFIED'
        if settled_at is not None:
            if not np.isfinite(settled_at) or settled_at < end:
                raise ValueError('settling precedes ramp completion')
            states[t >= settled_at] = 'NORMAL_B'
    return states


def inspect(raw_dir, selection_path, output):
    raw_dir = Path(raw_dir)
    meta = json.loads((raw_dir/'article_v1.json').read_text())
    sel = json.loads(Path(selection_path).read_text())
    info = next(x for x in meta['files'] if x['name'] == sel['file'])
    rf = OfficialRangeFile(info, raw_dir/'ranges_mode1')
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'selection_sha256': sha256(Path(selection_path).read_bytes()),
              'detector_runs': 0, 'scaler_fits': 0, 'policy_metadata_input': False, 'runs': []}
    with h5py.File(rf, 'r') as f:
        result['root_keys'] = list(f.keys())
        result['families'] = list(f['Mode1'].keys())
        result['process_channels'] = [v.decode() for v in f['Processdata_Labels'][()]]
        result['additional_channels'] = [v.decode() for v in f['Additional_Meas_Labels'][()]]
        result['mode_transition_inventory'] = {}
        for status in ('SimulationCompleted', 'SimulationStopped'):
            g = f['Mode1/ModeTransition/'+status]
            result['mode_transition_inventory'][status] = {k: list(g[k].keys()) for k in g}
        for idx, path in enumerate(sel['paths']):
            if path not in f:
                result['runs'].append({'path': path, 'status': 'MISSING_PRESELECTED_PATH', 'replacement': None})
                continue
            g = f[path]
            entry = {'path': path, 'status': 'INSPECTED', 'attrs': {k: np.asarray(v).tolist() for k, v in g.attrs.items()},
                     'datasets': {k: {'shape': list(g[k].shape), 'dtype': str(g[k].dtype)} for k in g},
                     'profiles': {k: g[k][()].tolist() for k in ('idv_init', 'setpoint_init', 'time_info')}}
            # Exactly one transition and one fault receive a full observation smoke read.
            if idx in (0, 3):
                t, x = observations(g['processdata'][()])
                np.savez(raw_dir/f'smoke_{idx}.npz', time=t, observations=x)
                entry['smoke'] = {'shape': list(x.shape), 'time_first': float(t[0]), 'time_last': float(t[-1]),
                                  'dt_hours': .05, 'finite': True, 'constant_channel_indices': np.flatnonzero(np.ptp(x, axis=0)==0).tolist(),
                                  'raw_extraction_sha256': sha256((raw_dir/f'smoke_{idx}.npz').read_bytes()),
                                  'array_values_sha256': sha256(x.astype('<f8').tobytes()),
                                  'timestamps_sha256': sha256(t.astype('<f8').tobytes()),
                                  'representation_if_authorized': {'channels': 53, 'window': 8, 'input_dim': 424, 'dk': 128, 'seeds': [11,22,33]},
                                  'states': 'UNKNOWN until profile-axis and warm-up semantics verified; no endpoint by scores'}
            result['runs'].append(entry)
    ranges = [{'start': int(p.stem.split('-')[0]), 'end_inclusive': int(p.stem.split('-')[1]),
               'bytes': p.stat().st_size, 'sha256': sha256(p.read_bytes())}
              for p in sorted(rf.root.glob('*.bin'), key=lambda p: int(p.stem.split('-')[0]))]
    result['acquisition'] = {'file': info['name'], 'canonical_download_url': info['download_url'], 'official_file_size': info['size'],
                             'official_md5': info['computed_md5'], 'official_sha256': None, 'whole_file_acquired': False,
                             'whole_file_hash_verified': False, 'ranges': ranges, 'cached_bytes': sum(x['bytes'] for x in ranges),
                             'new_transfer_bytes_this_invocation': rf.transferred, 'budget_bytes': BUDGET,
                             'metadata_sha256': sha256((raw_dir/'article_v1.json').read_bytes()),
                             'readme_sha256': sha256((raw_dir/'Readme.html').read_bytes()),
                             'readme_md5_verified': hashlib.md5((raw_dir/'Readme.html').read_bytes()).hexdigest() == next(x['computed_md5'] for x in meta['files'] if x['name']=='Readme.html')}
    write_json(Path(output), result)
    print(json.dumps({'output': str(output), 'runs': len(result['runs']), 'smoke_runs': sum('smoke' in x for x in result['runs']), 'cached_bytes': result['acquisition']['cached_bytes']}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--selection', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    inspect(args.raw_dir, args.selection, args.output)
