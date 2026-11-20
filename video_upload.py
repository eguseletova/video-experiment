"""
Video storage: participant browser -> oTree server -> Box folder.

How it works
------------
1. When the participant clicks Next on Video A/B/C, the browser sends the
   final (blurred) recording to the oTree server in small chunks over oTree's
   live channel (`live_method` on the video pages). See blur_recorder.js.
2. The server writes the file to  video_uploads/pending/  and immediately
   tells the browser it is saved, so the participant can continue.
3. A background thread uploads pending files to the Box folder BOX_FOLDER_ID
   and deletes the local copy once Box confirms (set VIDEO_KEEP_LOCAL=1 to
   keep it). Files that still fail after several tries are moved to
   video_uploads/failed/ (re-send them with `python video_upload.py retry`).
   Every upload is logged in video_uploads/upload_log.csv.

If Box is not configured, videos are simply kept in video_uploads/pending/.

File names:  <session code>_<participant code>_video<A|B|C>_<prompt set>.webm
The participant code links each file to the oTree data export.

Configuration (environment variables, or a file `box.env` next to this file
with KEY=VALUE lines -- never commit that file):

    BOX_FOLDER_ID        id of the Box folder (the number at the end of the
                         folder's URL, e.g. https://app.box.com/folder/123456)
    BOX_CLIENT_ID        from the Box Developer Console (your custom app)
    BOX_CLIENT_SECRET    from the Box Developer Console
    BOX_AUTH             "oauth" (default) or "ccg"

  BOX_AUTH=oauth  (User Authentication / OAuth 2.0 app; uploads as you)
    Local machine:  python video_upload.py authorize
      tokens kept in BOX_TOKEN_FILE (default video_uploads/.box_tokens.json)
    Server (e.g. Render):  python video_upload.py authorize --print  (locally),
      paste the printed token as BOX_REFRESH_TOKEN on the server, and set
      BOX_TOKEN_DB_URL to a Postgres database where the server keeps the
      refreshed tokens (no persistent disk needed).

  BOX_AUTH=ccg    (Server Authentication / Client Credentials Grant app;
                   may need approval by your Box admins; best for Heroku)
    BOX_SUBJECT_TYPE   "enterprise" or "user"
    BOX_SUBJECT_ID     enterprise id or user id

  BOX_DEVELOPER_TOKEN  (optional, testing only: 60-minute token from the
                        Developer Console; overrides the above)

Command line:
    python video_upload.py authorize   # one-time OAuth login (BOX_AUTH=oauth)
    python video_upload.py authorize --print   # token for a server (BOX_REFRESH_TOKEN)
    python video_upload.py test        # upload a small test file to the folder
    python video_upload.py retry       # re-send everything in failed/ and pending/
    python video_upload.py status      # show configuration and queue
"""

import base64
import csv
import json
import os
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.environ.get('VIDEO_UPLOAD_DIR', ROOT / 'video_uploads'))
PARTS = UPLOAD_DIR / 'incoming'
PENDING = UPLOAD_DIR / 'pending'
FAILED = UPLOAD_DIR / 'failed'
DONE = UPLOAD_DIR / 'uploaded'
LOG = UPLOAD_DIR / 'upload_log.csv'

MAX_BYTES = 80 * 1024 * 1024  # generous cap for a 1-minute video
LETTERS = ('a', 'b', 'c')
EXTENSIONS = {'video/webm': 'webm', 'video/mp4': 'mp4'}
MAX_TRIES = 5

API = 'https://api.box.com'
UPLOAD_API = 'https://upload.box.com/api/2.0'


# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------

def _load_env_file():
    f = ROOT / 'box.env'
    if not f.exists():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file()


def cfg(name, default=''):
    return os.environ.get(name, default).strip()


def box_configured():
    if not cfg('BOX_FOLDER_ID'):
        return False
    if cfg('BOX_DEVELOPER_TOKEN'):
        return True
    if not (cfg('BOX_CLIENT_ID') and cfg('BOX_CLIENT_SECRET')):
        return False
    if cfg('BOX_AUTH', 'oauth') == 'ccg':
        return bool(cfg('BOX_SUBJECT_ID'))
    return bool(cfg('BOX_REFRESH_TOKEN')) or _load_tokens() is not None


def token_file():
    return Path(cfg('BOX_TOKEN_FILE') or (UPLOAD_DIR / '.box_tokens.json'))


# --------------------------------------------------------------------------
# OAuth token storage
#
# Box refresh tokens are single-use: every refresh returns a new one that must
# be stored durably. Storage:
#   - BOX_TOKEN_DB_URL set (e.g. a Render Postgres URL): a one-row table
#     `box_oauth_tokens` in that database (survives server restarts, so it
#     works on hosts without a persistent disk such as Render's free tier).
#     This is separate from oTree's own database.
#   - otherwise: the JSON file token_file().
# BOX_REFRESH_TOKEN (optional) seeds the storage once: on a server, run
#   python video_upload.py authorize --print
# locally and paste the printed token into the server's BOX_REFRESH_TOKEN.
# A new seed value replaces whatever is stored.
# --------------------------------------------------------------------------

_db_engine = None


def _db():
    global _db_engine
    if _db_engine is None:
        import sqlalchemy
        url = cfg('BOX_TOKEN_DB_URL')
        if url.startswith('postgres://'):
            url = 'postgresql://' + url[len('postgres://'):]
        _db_engine = sqlalchemy.create_engine(url, pool_pre_ping=True)
        with _db_engine.begin() as c:
            c.execute(sqlalchemy.text(
                'CREATE TABLE IF NOT EXISTS box_oauth_tokens (id VARCHAR(20) PRIMARY KEY, data TEXT NOT NULL)'))
    return _db_engine


def _seed_id():
    import hashlib
    seed = cfg('BOX_REFRESH_TOKEN')
    return hashlib.sha256(seed.encode()).hexdigest()[:16] if seed else ''


def _load_tokens():
    if cfg('BOX_TOKEN_DB_URL'):
        import sqlalchemy
        with _db().begin() as c:
            row = c.execute(sqlalchemy.text("SELECT data FROM box_oauth_tokens WHERE id='box'")).fetchone()
        tok = json.loads(row[0]) if row else None
    else:
        f = token_file()
        tok = json.loads(f.read_text()) if f.exists() else None
    seed = cfg('BOX_REFRESH_TOKEN')
    if seed and (tok is None or tok.get('seed_id') != _seed_id()):
        # new seed from the environment: start the token chain from it
        tok = {'refresh_token': seed, 'expires_at': 0, 'seed_id': _seed_id()}
    return tok


# --------------------------------------------------------------------------
# Box client (stdlib only)
# --------------------------------------------------------------------------

class BoxError(Exception):
    def __init__(self, status, body):
        super().__init__(f'Box HTTP {status}: {body[:500]}')
        self.status = status
        self.body = body


def _request(method, url, data=None, headers=None, timeout=300):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        raise BoxError(e.code, e.read().decode('utf-8', 'replace')) from None


def _token_request(fields):
    status, body = _request(
        'POST', API + '/oauth2/token',
        data=urllib.parse.urlencode(fields).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=60,
    )
    return json.loads(body)


_token_lock = threading.Lock()
_token_cache = {}


def _save_tokens(tok):
    if cfg('BOX_REFRESH_TOKEN'):
        tok['seed_id'] = _seed_id()
    if cfg('BOX_TOKEN_DB_URL'):
        import sqlalchemy
        with _db().begin() as c:
            c.execute(sqlalchemy.text("DELETE FROM box_oauth_tokens WHERE id='box'"))
            c.execute(sqlalchemy.text("INSERT INTO box_oauth_tokens (id, data) VALUES ('box', :d)"),
                      {'d': json.dumps(tok)})
        return
    f = token_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix('.tmp')
    tmp.write_text(json.dumps(tok))
    os.chmod(tmp, 0o600)
    tmp.replace(f)


def access_token(force_refresh=False):
    """Return a valid access token (refreshing / re-requesting as needed)."""
    if cfg('BOX_DEVELOPER_TOKEN'):
        return cfg('BOX_DEVELOPER_TOKEN')
    with _token_lock:
        now = time.time()
        if not force_refresh and _token_cache.get('expires_at', 0) > now + 120:
            return _token_cache['access_token']
        cid, secret = cfg('BOX_CLIENT_ID'), cfg('BOX_CLIENT_SECRET')
        if cfg('BOX_AUTH', 'oauth') == 'ccg':
            tok = _token_request(dict(
                grant_type='client_credentials', client_id=cid, client_secret=secret,
                box_subject_type=cfg('BOX_SUBJECT_TYPE', 'enterprise'),
                box_subject_id=cfg('BOX_SUBJECT_ID'),
            ))
        else:
            stored = _load_tokens()
            if stored is None:
                raise RuntimeError('No Box tokens: run  python video_upload.py authorize')
            if not force_refresh and stored.get('expires_at', 0) > now + 120:
                tok = stored
            else:
                # Box refresh tokens are single-use: save the new one right away.
                tok = _token_request(dict(
                    grant_type='refresh_token', refresh_token=stored['refresh_token'],
                    client_id=cid, client_secret=secret,
                ))
                tok['expires_at'] = now + tok.get('expires_in', 3600)
                _save_tokens(tok)
        tok.setdefault('expires_at', now + tok.get('expires_in', 3600))
        _token_cache.clear()
        _token_cache.update(tok)
        return tok['access_token']


def _multipart(attributes, filename, content, mime):
    boundary = uuid.uuid4().hex
    head = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="attributes"\r\n\r\n'
        f'{json.dumps(attributes)}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {mime}\r\n\r\n'
    ).encode()
    tail = f'\r\n--{boundary}--\r\n'.encode()
    return head + content + tail, f'multipart/form-data; boundary={boundary}'


def box_upload(path: Path, folder_id=None):
    """Upload a file to the Box folder; if the name exists, add a new version.
    Returns the Box file id."""
    folder_id = folder_id or cfg('BOX_FOLDER_ID')
    content = path.read_bytes()
    mime = 'video/mp4' if path.suffix == '.mp4' else ('text/plain' if path.suffix == '.txt' else 'video/webm')

    def send(url, attributes, retry_auth=True):
        body, ctype = _multipart(attributes, path.name, content, mime)
        try:
            _, resp = _request('POST', url, data=body, headers={
                'Authorization': 'Bearer ' + access_token(), 'Content-Type': ctype})
        except BoxError as e:
            if e.status == 401 and retry_auth and not cfg('BOX_DEVELOPER_TOKEN'):
                access_token(force_refresh=True)
                return send(url, attributes, retry_auth=False)
            raise
        return json.loads(resp)['entries'][0]['id']

    try:
        return send(UPLOAD_API + '/files/content',
                    {'name': path.name, 'parent': {'id': str(folder_id)}})
    except BoxError as e:
        if e.status != 409:
            raise
        existing = json.loads(e.body)['context_info']['conflicts']['id']
        return send(UPLOAD_API + f'/files/{existing}/content', {'name': path.name})


# --------------------------------------------------------------------------
# background uploader
# --------------------------------------------------------------------------

_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def _log(filename, status, detail=''):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with LOG.open('a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['time_utc', 'file', 'status', 'detail'])
        w.writerow([time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), filename, status, detail])


def _upload_one(path: Path):
    for attempt in range(1, MAX_TRIES + 1):
        try:
            file_id = box_upload(path)
            _log(path.name, 'uploaded', f'box_file_id={file_id}')
            if cfg('VIDEO_KEEP_LOCAL') == '1':
                DONE.mkdir(parents=True, exist_ok=True)
                path.replace(DONE / path.name)
            else:
                path.unlink(missing_ok=True)
            return True
        except Exception as e:  # network errors, Box errors
            _log(path.name, f'error (try {attempt})', str(e)[:300])
            time.sleep(min(60, 5 * attempt))
    FAILED.mkdir(parents=True, exist_ok=True)
    path.replace(FAILED / path.name)
    _log(path.name, 'failed', 'moved to failed/')
    return False


def _worker():
    while True:
        path = _queue.get()
        try:
            if path.exists() and box_configured():
                _upload_one(path)
        finally:
            _queue.task_done()


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(target=_worker, name='box-uploader', daemon=True).start()
        # files left over from a previous server run
        if PENDING.exists():
            for p in sorted(PENDING.iterdir()):
                if p.is_file():
                    _queue.put(p)


def _running_bot_tests():
    import sys
    return os.path.basename(sys.argv[0]) == 'otree' and sys.argv[1:2] == ['test']


def enqueue(path: Path):
    if _running_bot_tests():  # never send bot test data to Box
        _log(path.name, 'stored locally', 'bot test')
        return
    if box_configured():
        _ensure_worker()
        _queue.put(path)
    else:
        _log(path.name, 'stored locally', 'Box not configured')


# --------------------------------------------------------------------------
# oTree live_method for the video pages
# --------------------------------------------------------------------------

def _part_path(player, letter):
    return PARTS / f'{player.participant.code}_{letter}.part'


def _final_name(player, letter, mime):
    ext = EXTENSIONS.get((mime or '').split(';')[0].strip(), 'webm')
    prompt_set = player.field_maybe_none('prompt_set') or 'x'
    return f'{player.session.code}_{player.participant.code}_video{letter.upper()}_{prompt_set}.{ext}'


def live_method(player, data):
    """Messages from blur_recorder.js:
        {type:'start', letter, size, mime}          -> {type:'ready'}
        {type:'chunk', letter, offset, data(base64)} -> {type:'ack', offset}
        {type:'done', letter}                        -> {type:'stored'}
    Errors -> {type:'error', message}. Chunks are append-only and checked
    against the current file size, so a retry can resume."""
    pid = player.id_in_group

    def reply(**msg):
        return {pid: msg}

    try:
        kind = data.get('type')
        letter = data.get('letter')
        if letter not in LETTERS:
            return reply(type='error', message='bad letter')
        part = _part_path(player, letter)
        meta = part.with_suffix('.json')

        if kind == 'start':
            size = int(data.get('size', 0))
            if not (0 < size <= MAX_BYTES):
                return reply(type='error', message='bad size')
            PARTS.mkdir(parents=True, exist_ok=True)
            part.write_bytes(b'')
            meta.write_text(json.dumps({'size': size, 'mime': str(data.get('mime', ''))[:60]}))
            setattr(player, f'video_{letter}_uploaded', False)
            return reply(type='ready', letter=letter)

        if kind == 'chunk':
            if not meta.exists():
                return reply(type='error', message='not started')
            info = json.loads(meta.read_text())
            have = part.stat().st_size
            offset = int(data.get('offset', -1))
            if offset != have:
                return reply(type='ack', letter=letter, offset=have)  # client resyncs
            chunk = base64.b64decode(data.get('data', ''))
            if have + len(chunk) > info['size']:
                return reply(type='error', message='too much data')
            with part.open('ab') as f:
                f.write(chunk)
            return reply(type='ack', letter=letter, offset=have + len(chunk))

        if kind == 'done':
            if not meta.exists():
                return reply(type='error', message='not started')
            info = json.loads(meta.read_text())
            if part.stat().st_size != info['size']:
                return reply(type='error', message='incomplete')
            PENDING.mkdir(parents=True, exist_ok=True)
            final = PENDING / _final_name(player, letter, info['mime'])
            part.replace(final)
            meta.unlink(missing_ok=True)
            setattr(player, f'video_{letter}_uploaded', True)
            setattr(player, f'video_{letter}_file', final.name)
            enqueue(final)
            return reply(type='stored', letter=letter)

        return reply(type='error', message='unknown message')
    except Exception as e:
        return reply(type='error', message=str(e)[:200])


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def _cli_authorize(print_only=False):
    import http.server
    import secrets
    import webbrowser

    cid, secret = cfg('BOX_CLIENT_ID'), cfg('BOX_CLIENT_SECRET')
    if not (cid and secret):
        raise SystemExit('Set BOX_CLIENT_ID and BOX_CLIENT_SECRET (e.g. in box.env) first.')
    port = int(cfg('BOX_REDIRECT_PORT', '8765'))
    redirect = f'http://localhost:{port}/callback'
    state = secrets.token_urlsafe(16)
    url = 'https://account.box.com/api/oauth2/authorize?' + urllib.parse.urlencode(dict(
        response_type='code', client_id=cid, redirect_uri=redirect, state=state))
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            ok = q.get('state', [''])[0] == state and 'code' in q
            if ok:
                result['code'] = q['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            msg = 'Box connected. You can close this tab.' if ok else 'Authorization failed.'
            self.wfile.write(f'<p style="font:18px sans-serif">{msg}</p>'.encode())

        def log_message(self, *a):
            pass

    print('Opening Box in your browser. If nothing opens, visit:\n' + url)
    print(f'(The app\'s Redirect URI in the Box Developer Console must be {redirect})')
    webbrowser.open(url)
    server = http.server.HTTPServer(('localhost', port), Handler)
    while 'code' not in result:
        server.handle_request()
    tok = _token_request(dict(grant_type='authorization_code', code=result['code'],
                              client_id=cid, client_secret=secret, redirect_uri=redirect))
    if print_only:
        # A separate token chain for a server (do not also save it here: each
        # refresh token can only be used once, by one machine).
        print('\nPaste this as BOX_REFRESH_TOKEN in the server settings (use it within 60 days, only once):\n')
        print(tok['refresh_token'])
        return
    tok['expires_at'] = time.time() + tok.get('expires_in', 3600)
    _save_tokens(tok)
    where = 'the token database' if cfg('BOX_TOKEN_DB_URL') else str(token_file())
    print(f'Saved Box tokens to {where}. Now run:  python video_upload.py test')


def _cli_test():
    if not box_configured():
        raise SystemExit('Box is not fully configured. Run:  python video_upload.py status')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    p = UPLOAD_DIR / 'connection_test.txt'
    p.write_text('oTree video experiment: Box connection test, ' + time.ctime() + '\n')
    fid = box_upload(p)
    p.unlink()
    print(f'OK: uploaded connection_test.txt to folder {cfg("BOX_FOLDER_ID")} (Box file id {fid}).')


def _cli_retry():
    files = [p for d in (FAILED, PENDING) if d.exists() for p in sorted(d.iterdir()) if p.is_file()]
    if not box_configured():
        raise SystemExit('Box is not fully configured.')
    for p in files:
        print(p.name, '->', 'ok' if _upload_one(p) else 'FAILED')
    print(f'{len(files)} file(s) processed.')


def _cli_status():
    print('Box folder id :', cfg('BOX_FOLDER_ID') or '(not set)')
    print('Auth mode     :', 'developer token' if cfg('BOX_DEVELOPER_TOKEN') else cfg('BOX_AUTH', 'oauth'))
    print('Client id set :', bool(cfg('BOX_CLIENT_ID')))
    if cfg('BOX_AUTH', 'oauth') == 'oauth' and not cfg('BOX_DEVELOPER_TOKEN'):
        where = 'database (BOX_TOKEN_DB_URL)' if cfg('BOX_TOKEN_DB_URL') else str(token_file())
        print('Token storage :', where, '(ok)' if _load_tokens() else '(empty: run authorize)')
    print('Configured    :', box_configured())
    for d in (PENDING, FAILED):
        n = len([p for p in d.iterdir() if p.is_file()]) if d.exists() else 0
        print(f'{d.name:<14}:', n, 'file(s)')


if __name__ == '__main__':
    import sys
    cmds = dict(authorize=_cli_authorize, test=_cli_test, retry=_cli_retry, status=_cli_status)
    args = sys.argv[1:]
    if args == ['authorize', '--print']:
        _cli_authorize(print_only=True)
    elif len(args) == 1 and args[0] in cmds:
        cmds[args[0]]()
    else:
        raise SystemExit('usage: python video_upload.py [authorize [--print]|test|retry|status]')
