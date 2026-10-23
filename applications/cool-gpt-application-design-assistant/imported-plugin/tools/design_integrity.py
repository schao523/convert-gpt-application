"""Four bounded local design operations; JSON stdin/stdout; Python standard library."""
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_INPUT = 2 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def strings(value, name):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(name + ' must be a list of nonempty strings')
    return value

def text(value, name):
    if not isinstance(value, str) or not value:
        raise ValueError(name + ' must be nonempty text')
    return value

def sha(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('invalid sha256')
    return value

def alias_resolution(data):
    query = text(data.get('name'), 'name')
    inventory = data.get('inventory')
    if not isinstance(inventory, list):
        raise ValueError('inventory must be a list')
    seen = set()
    matches = []
    for record in inventory:
        if not isinstance(record, dict):
            raise ValueError('inventory entry must be an object')
        identifier = text(record.get('id'), 'id')
        if identifier in seen:
            raise ValueError('duplicate inventory id')
        seen.add(identifier)
        names = [identifier, text(record.get('path'), 'path'), *strings(record.get('aliases', []), 'aliases')]
        if query in names:
            matches.append(record)
    return {'status': 'missing' if not matches else 'unique' if len(matches) == 1 else 'ambiguous', 'name': query, 'matches': matches}

def link_integrity(data):
    groups = data.get('groups')
    links = data.get('links')
    if not isinstance(groups, dict) or set(groups) != {'requirements', 'modules', 'resources', 'workflows', 'tests'} or not isinstance(links, list):
        raise ValueError('provide five typed groups and links')
    nodes = set()
    duplicates = []
    for kind, identifiers in sorted(groups.items()):
        for identifier in strings(identifiers, kind):
            key = (kind, identifier)
            if key in nodes:
                duplicates.append({'kind': kind, 'id': identifier})
            nodes.add(key)
    edges = set()
    touched = set()
    dangling = []
    duplicate_links = []
    for link in links:
        if not isinstance(link, dict) or set(link) != {'from_kind', 'from_id', 'to_kind', 'to_id'}:
            raise ValueError('invalid link')
        edge = tuple(text(link[k], k) for k in ['from_kind', 'from_id', 'to_kind', 'to_id'])
        if edge in edges:
            duplicate_links.append(link)
        edges.add(edge)
        endpoints = [(edge[0], edge[1]), (edge[2], edge[3])]
        if any(node not in nodes for node in endpoints):
            dangling.append(link)
        else:
            touched.update(endpoints)
    uncovered = [{'kind': kind, 'id': identifier} for kind, identifier in sorted(nodes - touched)]
    return {'dangling': dangling, 'uncovered': uncovered, 'duplicate': {'nodes': duplicates, 'links': duplicate_links}}

def version_guard(data):
    artifact = text(data.get('artifact_id'), 'artifact_id')
    version = text(data.get('version'), 'version')
    content_hash = sha(data.get('sha256'))
    scope = text(data.get('scope'), 'scope')
    confirmation = data.get('confirmation')
    required = {'artifact_id': artifact, 'version': version, 'sha256': content_hash, 'scope': scope, 'explicit': True}
    valid = isinstance(confirmation, dict) and type(confirmation.get('explicit')) is bool and all(confirmation.get(k) == v for k, v in required.items())
    return {'status': 'allowed' if valid else 'needs-reconfirmation', 'artifact_id': artifact, 'version': version, 'sha256': content_hash, 'scope': scope}

def package_digest(data, root=None):
    # Reads only files explicitly selected under the current export workspace.
    root = Path.cwd().resolve() if root is None else Path(root).resolve()
    records = data.get('files')
    if not isinstance(records, list):
        raise ValueError('files must be a list')
    seen = set()
    members = []
    total = 0
    for record in records:
        if not isinstance(record, dict) or set(record) != {'path', 'redistribution_approved'} or record.get('redistribution_approved') is not True:
            raise ValueError('explicit redistribution approval required for every file')
        name = text(record.get('path'), 'path')
        if '\\' in name or ':' in name or name.startswith('/') or any(p in {'', '.', '..'} for p in name.split('/')):
            raise ValueError('unsafe path')
        if name.casefold() in seen:
            raise ValueError('duplicate logical path')
        seen.add(name.casefold())
        candidate = root
        for part in name.split('/'):
            candidate = candidate / part
            if candidate.is_symlink():
                raise ValueError('links forbidden')
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError('file outside export workspace')
        if resolved.stat().st_size > MAX_FILE:
            raise ValueError('file exceeds bound')
        payload = resolved.read_bytes()
        total += len(payload)
        if total > 64 * 1024 * 1024:
            raise ValueError('aggregate exceeds bound')
        members.append({'path': name, 'size_bytes': len(payload), 'sha256': digest(payload)})
    members.sort(key=lambda x: x['path'])
    return {'files': members, 'summary_sha256': digest(canonical(members)), 'ordering': 'path-unicode-codepoint', 'behavior_verified': False}

OPERATIONS = {'D01': alias_resolution, 'D02': link_integrity, 'D03': version_guard, 'D04': package_digest}

def execute(data):
    if not isinstance(data, dict) or set(data) != {'operation', 'input'} or not isinstance(data['input'], dict) or data.get('operation') not in OPERATIONS:
        raise ValueError('provide operation D01-D04 and input object')
    return {'operation': data['operation'], 'result': OPERATIONS[data['operation']](data['input'])}

def self_test():
    import tempfile
    count = 0
    def check(condition):
        nonlocal count
        assert condition
        count += 1
    def rejects(function):
        nonlocal count
        try:
            function()
        except (ValueError, OSError):
            count += 1
        else:
            raise AssertionError('expected rejection')
    inv = [{'id': 'a', 'path': 'a.md', 'aliases': ['method']}, {'id': 'b', 'path': 'b.md', 'aliases': ['method']}]
    for query, expected in [('a', 'unique'), ('absent', 'missing'), ('method', 'ambiguous')]:
        check(alias_resolution({'name': query, 'inventory': inv})['status'] == expected)
    rejects(lambda: alias_resolution({'name': 'a', 'inventory': inv + [inv[0]]}))
    groups = {'requirements': ['R1', 'R2', 'R1'], 'modules': ['IM1'], 'resources': [], 'workflows': [], 'tests': []}
    edge = {'from_kind': 'requirements', 'from_id': 'R1', 'to_kind': 'modules', 'to_id': 'IM1'}
    bad = dict(edge, to_id='absent')
    result = link_integrity({'groups': groups, 'links': [edge, edge, bad]})
    check(len(result['dangling']) == 1)
    check(result['uncovered'] == [{'kind': 'requirements', 'id': 'R2'}])
    check(len(result['duplicate']['nodes']) == len(result['duplicate']['links']) == 1)
    baseline = {'artifact_id': 'core', 'version': '1', 'sha256': '0' * 64, 'scope': 'core'}
    confirmation = dict(baseline, explicit=True)
    check(version_guard(dict(baseline, confirmation=confirmation))['status'] == 'allowed')
    for delta in [{'version': '2'}, {'sha256': '1' * 64}, {'scope': 'other'}, {'artifact_id': 'other'}, {'confirmation': dict(confirmation, explicit=1)}]:
        check(version_guard(dict(baseline, confirmation=confirmation) | delta)['status'] == 'needs-reconfirmation')
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / 'a.md').write_bytes(b'alpha')
        (root / 'b.md').write_bytes(b'beta')
        files = [{'path': name, 'redistribution_approved': True} for name in ['b.md', 'a.md']]
        a = package_digest({'files': files}, root)
        b = package_digest({'files': list(reversed(files))}, root)
        check(a == b)
        check(a['files'][0]['sha256'] == digest(b'alpha'))
        check(a['behavior_verified'] is False)
        rejects(lambda: package_digest({'files': [{'path': '../a.md', 'redistribution_approved': True}]}, root))
        rejects(lambda: package_digest({'files': [{'path': 'a.md', 'redistribution_approved': False}]}, root))
        rejects(lambda: package_digest({'files': files + [files[0]]}, root))
        rejects(lambda: package_digest({'files': [{'path': 'missing', 'redistribution_approved': True}]}, root))
        (root / 'link').symlink_to(root / 'a.md')
        rejects(lambda: package_digest({'files': [{'path': 'link', 'redistribution_approved': True}]}, root))
    rejects(lambda: execute({'operation': 'unknown', 'input': {}}))
    return {'self_test': 'PASS', 'checks': count}

def main():
    try:
        if sys.argv[1:] == ['--self-test']:
            print(json.dumps(self_test(), sort_keys=True))
            return 0
        if sys.argv[1:]:
            raise ValueError('unexpected arguments')
        payload = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(payload) > MAX_INPUT:
            raise ValueError('input exceeds bound')
        result = execute(json.loads(payload))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, OSError, TypeError, KeyError, AssertionError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
