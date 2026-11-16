"""Make a public release folder from a private source, scanned and ready to push, with a fresh one-commit history.

  python3 tools/release.py <name> [--commit <sha>]     prepare ~/Developer/releases/<name> (never pushes)

Release definitions live outside every repository, in ~/.config/sc-open-corpus/releases.json:
  {"<name>": {"source": "<git repo or folder>", "commit": "<sha or null for a folder>", "exclude": ["glob", ...],
              "drop_lines": ["glob:regex", ...], "remote": "EthDawg/<repo>", "description": "..."}}
A git source is taken with `git archive <commit>` (committed files only, no history). Then: exclusions, then a scan of
every file (inside PDFs, Office files and archives too) for deny-listed terms (tools/denylist.py), home-directory paths,
e-mail addresses and secrets. Any hit stops the release and lists the files. A clean folder gets `git init` and one
commit; pushing is a separate step a person approves.
"""
import os, sys, json, re, io, shutil, fnmatch, subprocess, tarfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import denylist as DENY

CFG = os.path.expanduser('~/.config/sc-open-corpus/releases.json')
PRIVATE = [re.compile(p, re.I) for p in (r'/Users/' + re.escape(os.path.basename(os.path.expanduser('~'))) + r'\b', r'[A-Za-z0-9._%+-]+@(gmail|icloud|outlook|hotmail)\.com',
                                          r'(sk-ant-|sk-proj-|ghp_|gho_|xox[bp]-)[A-Za-z0-9_-]{10,}', r'BEGIN (RSA |OPENSSH )?PRIVATE KEY')]


def text_of(name, b):
    if name.lower().endswith('.pdf'):
        return subprocess.run(['pdftotext', '-', '-'], input=b, capture_output=True).stdout.decode('utf-8', 'replace')
    if b[:2] == b'PK':
        try:
            z = zipfile.ZipFile(io.BytesIO(b)); return '\n'.join(text_of(n, z.read(n)) for n in z.namelist())
        except zipfile.BadZipFile: pass
    if b[:2] == b'\x1f\x8b':
        try:
            with tarfile.open(fileobj=io.BytesIO(b)) as tf:
                return '\n'.join(text_of(m.name, tf.extractfile(m).read()) for m in tf.getmembers() if m.isfile())
        except tarfile.TarError: pass
    return b.decode('utf-8', 'replace')


def scan(root, ts):
    hits = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if x != '.git']
        for f in fs:
            p = os.path.join(d, f); rel = os.path.relpath(p, root)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.otf', '.mp3', '.mp4', '.m4a', '.wav', '.onnx', '.bin', '.npy')): continue
            if rel == 'tools/denylist.py': continue
            t = text_of(f, open(p, 'rb').read())
            why = [t2 for t2 in ts if t2 in t.lower()] + [r.pattern[:24] for r in PRIVATE if r.search(t)]
            if why: hits.append((rel, sorted(set(why))))
    return hits


def main():
    a = sys.argv[1:]; name = a[0]
    R = json.load(open(CFG))[name]
    commit = a[a.index('--commit') + 1] if '--commit' in a else R.get('commit')
    out = os.path.expanduser(f'~/Developer/releases/{name}')
    ts = DENY.terms()
    if not ts: sys.exit('No deny list on this machine: refusing.')
    keep = None
    if '--update' in a and os.path.isdir(os.path.join(out, '.git')):      # a published repo: add a commit, never rewrite history
        keep = out + '.git-keep'; shutil.rmtree(keep, ignore_errors=True); shutil.move(os.path.join(out, '.git'), keep)
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out)
    if keep: shutil.move(keep, os.path.join(out, '.git'))
    src = os.path.expanduser(R['source'])
    if commit:
        tar = subprocess.run(['git', '-C', src, 'archive', commit], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf: tf.extractall(out)
    else:
        shutil.copytree(src, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '.sc-open-corpus-public'))
    removed = 0
    for d, dirs, fs in os.walk(out, topdown=True):
        rel_d = os.path.relpath(d, out)
        for x in list(dirs):
            r = os.path.normpath(os.path.join(rel_d, x))
            if any(fnmatch.fnmatch(r, g) or fnmatch.fnmatch(r + '/', g) for g in R.get('exclude', [])):
                shutil.rmtree(os.path.join(d, x)); dirs.remove(x); removed += 1
        for f in fs:
            r = os.path.normpath(os.path.join(rel_d, f))
            if any(fnmatch.fnmatch(r, g) for g in R.get('exclude', [])): os.remove(os.path.join(d, f)); removed += 1
    hits = scan(out, ts)
    print(f'{name}: {commit or "folder"} -> {out} · {removed} paths excluded')
    if hits:
        print(f'REFUSED: {len(hits)} files need work before this can be public:')
        for rel, why in hits: print(f'  {rel}  [{", ".join(why)}]')
        sys.exit(1)
    if not keep: subprocess.run(['git', 'init', '-q', '-b', 'main'], cwd=out, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=out, check=True)
    msg = (a[a.index('-m') + 1] if '-m' in a else 'Update') if keep else f"{R.get('description', name)}\n\nFirst public release, cut from a private working repository{(' at ' + commit[:7]) if commit else ''}."
    msg += '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
    who = R.get('author', ['EthDawg', '74338122+EthDawg@users.noreply.github.com'])     # GitHub's no-reply address, never a local one
    subprocess.run(['git', '-c', f'user.name={who[0]}', '-c', f'user.email={who[1]}', 'commit', '-q', '-m', msg], cwd=out, check=True)
    n = sum(len(fs) for d, ds, fs in os.walk(out) if '.git' not in d)
    mb = sum(os.path.getsize(os.path.join(d, f)) for d, ds, fs in os.walk(out) if '.git' not in d for f in fs) / 1e6
    print(f'CLEAN: {n} files, {mb:.0f} MB. ' + (f'New commit on the published repo; push with: git -C {out} push' if keep else f'One commit. Push when approved: gh repo create {R["remote"]} --public --source {out} --push'))


if __name__ == '__main__':
    main()
