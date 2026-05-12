# ════════════════════════════════════════════════════════════════════════════
# SHV LICENSE GATE — Universal Convertor by SHV
# ════════════════════════════════════════════════════════════════════════════
import base64 as _b64, hashlib as _hs, json as _js, os as _os, threading
import zlib as _zl

from datetime import datetime as _dt
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

# ---------- Converter‑specific imports ----------
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp

from kivy.uix.anchorlayout import AnchorLayout

from datetime import datetime as _dt
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.core.clipboard import Clipboard

from kivymd.uix.spinner import MDSpinner   # ← add this line

from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard

from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.network.urlrequest import UrlRequest
import math

try:
    import rsa as _rsa
    _SHV_RSA_AVAILABLE = True
except ImportError:
    _SHV_RSA_AVAILABLE = False

_SHV_PUBLIC_KEY_PEM = b'''-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEAscQ2xe0PuXsYi6SNgY+9SmLwDBurVqtyviQWVgbkidT27g98/7g8
6VRDNer944yOVfM+wCS7Bq7PufcXADqBRywKYlMxigU3cVcUTcuBlpcWDH6gCBEp
PNb/+cmwacpO1ZdkTxEMWKE/GC3ZAo7on7KOzxus2jPI4iZRYunCYpeMT9PlurAB
hL3BsJNOmMIepIIAe9dlqfw2XW3k+I9O68Z0PEwQRr+6Ce5fp/K0BblMQMpNs5pO
hmii3Tq27Zkk8m1RoXR7f8IKP8mlvvWy1LFCUD8YsZnlMhS/St6ipqtPH4RhyMSy
HeaxQ93B+AnmRy7QNTvuo+1saoCeVkQSJwIDAQAB
-----END RSA PUBLIC KEY-----
'''
_SHV_ACT_PREFIX   = 'UNICONV6A'
_SHV_BUNDLE_APP   = 'universal_convertor_by_shv'
_SHV_LICENSE_FILE = "shv_license_universal_convertor_by_shv.json"

def _shv_data_dir():
    try:
        app = MDApp.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            return app.user_data_dir
    except Exception:
        pass
    return _os.path.join(_os.path.expanduser("~"), ".shv_app_data")

def _shv_get_device_code():
    raw = ""
    try:
        from jnius import autoclass
        S = autoclass("android.provider.Settings$Secure")
        PA = autoclass("org.kivy.android.PythonActivity")
        raw = str(S.getString(PA.mActivity.getContentResolver(), S.ANDROID_ID) or "")
    except Exception:
        pass
    if not raw:
        try:
            import uuid
            raw = str(uuid.getnode())
        except Exception:
            raw = "fallback"
    return _hs.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()

def _shv_decode_code(code):
    prefix = _SHV_ACT_PREFIX + "-"
    cleaned = code.strip().replace("\n","").replace(" ","")
    if cleaned.startswith(prefix):
        cleaned = cleaned[len(prefix):]
    cleaned = cleaned.replace(".","")
    cleaned += "=" * ((4 - len(cleaned) % 4) % 4)
    raw = _b64.urlsafe_b64decode(cleaned.encode("ascii"))
    data = _js.loads(_zl.decompress(raw).decode("utf-8"))
    return data["p"], data["s"]

def _shv_verify(payload, sig_b64):
    if not _SHV_RSA_AVAILABLE:
        return False
    try:
        pub = _rsa.PublicKey.load_pkcs1(_SHV_PUBLIC_KEY_PEM)
        canon = _js.dumps(payload, sort_keys=True, separators=(",",":")).encode("utf-8")
        sig = _b64.urlsafe_b64decode(sig_b64.encode("ascii"))
        _rsa.verify(canon, sig, pub)
        return True
    except Exception:
        return False

def _shv_load_license():
    try:
        path = _os.path.join(_shv_data_dir(), _SHV_LICENSE_FILE)
        with open(path, "r", encoding="utf-8") as f:
            return _js.load(f)
    except Exception:
        return None

def _shv_save_license(code, payload):
    _os.makedirs(_shv_data_dir(), exist_ok=True)
    path = _os.path.join(_shv_data_dir(), _SHV_LICENSE_FILE)
    with open(path, "w", encoding="utf-8") as f:
        _js.dump({
            "activation_code": code,
            "license_id": payload.get("license_id", ""),
            "tier": payload.get("tier", "pro"),
            "payload": payload,
            "saved_at": _dt.utcnow().isoformat() + "Z"
        }, f)

def _shv_delete_license():
    try:
        path = _os.path.join(_shv_data_dir(), _SHV_LICENSE_FILE)
        if _os.path.exists(path):
            _os.remove(path)
    except Exception:
        pass

def _shv_check_license(code, device_code=None):
    if not code or not code.strip():
        return False, "", "No activation code.", ""
    if device_code is None:
        device_code = _shv_get_device_code()
    try:
        payload, sig_b64 = _shv_decode_code(code.strip())
    except Exception as e:
        return False, "", f"Could not decode: {e}", ""
    if not _shv_verify(payload, sig_b64):
        return False, "", "Invalid signature.", ""
    if str(payload.get("app", "")).lower() != _SHV_BUNDLE_APP.lower():
        return False, "", "Wrong product.", ""
    bound = str(payload.get("device_code", "")).strip().upper()
    if bound and bound != device_code.upper():
        return False, "", f"Device mismatch. Yours: {device_code.upper()} Bound: {bound}", ""
    expiry = str(payload.get("expires_at", "") or payload.get("expiry", "")).strip()
    if expiry:
        try:
            from datetime import timezone
            exp = _dt.fromisoformat(expiry.replace("Z", "+00:00"))
            if _dt.now(timezone.utc) > exp:
                return False, "", f"Expired {expiry[:10]}.", ""
        except Exception:
            pass
    return True, str(payload.get("tier", "pro")).lower(), "License verified.", payload.get("license_id", "")

# ========== SH VERTEX ACCOUNT & DEMO SYSTEM (shv-demo-v2) ==========
import json as _dj, os as _dos, hashlib as _dhs, threading as _dth
from datetime import datetime as _ddt, timedelta as _dtd
from urllib.request import urlopen as _dulopen, Request as _dReq
from urllib.error import HTTPError as _dHTTPError

_SHV_SUPABASE_URL       = 'https://ovdxetyadfsxehwnbyuz.supabase.co'
_SHV_PUBLISHABLE_KEY    = 'sb_publishable_3J-H60daCgWdhSvpdXi0zw_QpPax3Dz'
_SHV_DEMO_FUNCTION_URL  = 'https://ovdxetyadfsxehwnbyuz.supabase.co/functions/v1/shv-demo-v2'
_SHV_APP_CODE           = 'universal_convertor_by_shv'
_SHV_DEMO_HOURS         = 48
_SHV_OFFLINE_GRACE_MINS = 60
_SHV_SESSION_FILE       = 'shv_cloud_session_' + _SHV_APP_CODE + '.json'
_SHV_DEMO_CACHE_FILE    = 'shv_demo_cache_'    + _SHV_APP_CODE + '.json'

# ---------- File helpers ----------
def _shv_read_json(fname, default=None):
    try:
        path = _dos.path.join(_shv_data_dir(), fname)
        with open(path, 'r', encoding='utf-8') as f:
            return _dj.load(f)
    except Exception:
        return default if default is not None else {}

def _shv_write_json(fname, data):
    try:
        _dos.makedirs(_shv_data_dir(), exist_ok=True)
        path = _dos.path.join(_shv_data_dir(), fname)
        with open(path, 'w', encoding='utf-8') as f:
            _dj.dump(data, f)
    except Exception:
        pass

def _shv_delete_json(fname):
    try:
        path = _dos.path.join(_shv_data_dir(), fname)
        if _dos.path.exists(path):
            _dos.remove(path)
    except Exception:
        pass

# ---------- Network helpers ----------
def _shv_ssl_ctx():
    try:
        import certifi, ssl
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            import ssl
            return ssl.create_default_context()
        except Exception:
            return None

def _shv_http(method, url, json_body=None, headers=None, timeout=14):
    data = None
    if json_body is not None:
        data = _dj.dumps(json_body).encode('utf-8')
        headers = headers or {}
        headers['Content-Type'] = 'application/json'
    req = _dReq(url, data=data, headers=headers or {}, method=method)
    ctx = _shv_ssl_ctx()
    with _dulopen(req, timeout=timeout, context=ctx) as resp:
        body = resp.read()
    return _dj.loads(body.decode('utf-8')) if body else {}

def _shv_error_msg(exc):
    if isinstance(exc, _dHTTPError):
        try:
            body = exc.read().decode('utf-8', 'ignore')
            pl = _dj.loads(body)
            return pl.get('message') or pl.get('error_description') or pl.get('error') or body
        except Exception:
            return f'HTTP {exc.code}: {exc.reason}'
    return str(exc)

# ---------- Time helpers ----------
def _shv_utc_now():
    return _ddt.utcnow().replace(microsecond=0)

def _shv_parse_date(s):
    if not s:
        return None
    try:
        return _ddt.fromisoformat(str(s).replace('Z', '').replace('+00:00', ''))
    except Exception:
        return None

def _shv_format_remaining(seconds):
    if seconds <= 0:
        return '0m'
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    if d > 0: return f'{d}d {h}h'
    if h > 0: return f'{h}h {m}m'
    return f'{m}m'

def _shv_device_fingerprint():
    base = _shv_get_device_code() + '|' + _SHV_APP_CODE
    return _dhs.sha256(base.encode('utf-8')).hexdigest()

# ---------- Session management ----------
def _shv_load_session():
    return _shv_read_json(_SHV_SESSION_FILE, {})

def _shv_save_session(s):
    _shv_write_json(_SHV_SESSION_FILE, s)

def _shv_clear_session():
    _shv_delete_json(_SHV_SESSION_FILE)

def _shv_headers(token=None):
    h = {'apikey': _SHV_PUBLISHABLE_KEY}
    if token:
        h['Authorization'] = f'Bearer {token}'
    h['Content-Type'] = 'application/json'
    return h

def _shv_ensure_session(silent=True):
    session = _shv_load_session()
    token = session.get('access_token', '')
    if not token:
        return {}
    try:
        expires_at = int(session.get('expires_at', 0) or 0)
        now_ts = int(_ddt.utcnow().timestamp())
        if now_ts >= expires_at - 60:
            refresh = session.get('refresh_token', '')
            if refresh:
                url = _SHV_SUPABASE_URL + '/auth/v1/token?grant_type=refresh_token'
                result = _shv_http('POST', url,
                                   json_body={"refresh_token": refresh},
                                   headers=_shv_headers())
                if result.get('access_token'):
                    _shv_save_session(result)
                    return result
    except Exception:
        pass
    return session

def _shv_sign_in(email, password):
    url = _SHV_SUPABASE_URL + '/auth/v1/token?grant_type=password'
    result = _shv_http('POST', url,
                       json_body={"email": email.strip(), "password": password},
                       headers=_shv_headers())
    _shv_save_session(result)
    _shv_register_device(result)
    return result

def _shv_sign_up(email, password, display_name=''):
    url = _SHV_SUPABASE_URL + '/auth/v1/signup'
    result = _shv_http('POST', url,
                       json_body={
                           "email": email.strip(),
                           "password": password,
                           "data": {"display_name": display_name.strip() or email.split('@')[0]},
                       },
                       headers=_shv_headers())
    needs_confirmation = not bool(result.get('access_token'))
    if not needs_confirmation:
        _shv_save_session(result)
        _shv_register_device(result)
    return result, needs_confirmation

def _shv_register_device(session=None):
    session = session or _shv_ensure_session()
    token = (session or {}).get('access_token', '')
    if not token:
        return
    try:
        user      = (session or {}).get('user', {}) or {}
        user_id   = user.get('id', '')
        fp        = _shv_device_fingerprint()
        now_iso   = _shv_utc_now().isoformat() + 'Z'
        url_check = (
            _SHV_SUPABASE_URL + '/rest/v1/devices'
            + f'?app_code=eq.{_SHV_APP_CODE}'
            + f'&device_fingerprint_hash=eq.{fp}'
            + '&select=id'
        )
        rows = _shv_http('GET', url_check, headers=_shv_headers(token))
        if isinstance(rows, list) and rows:
            dev_id = rows[0].get('id', '')
            _shv_http('PATCH',
                      _SHV_SUPABASE_URL + f'/rest/v1/devices?id=eq.{dev_id}',
                      json_body={"last_seen_at": now_iso},
                      headers={**_shv_headers(token), 'Prefer': 'return=minimal'})
            return
        _shv_http('POST',
                  _SHV_SUPABASE_URL + '/rest/v1/devices',
                  json_body={
                      "user_id": user_id,
                      "app_code": _SHV_APP_CODE,
                      "device_fingerprint_hash": fp,
                      "device_code": _shv_get_device_code(),
                      "device_name": "Android Device",
                      "platform": "Android",
                      "last_seen_at": now_iso,
                  },
                  headers={**_shv_headers(token), 'Prefer': 'return=minimal'})
    except Exception:
        pass

# ---------- Demo cache ----------
def _shv_load_demo_cache():
    d = _shv_read_json(_SHV_DEMO_CACHE_FILE, {})
    return d if isinstance(d, dict) else {}

def _shv_save_demo_cache(data):
    _shv_write_json(_SHV_DEMO_CACHE_FILE, data or {})

def _shv_clear_demo_cache():
    _shv_delete_json(_SHV_DEMO_CACHE_FILE)

def _shv_cache_demo_resp(resp):
    cache = {
        'schema': 'shv_demo_v2',
        'status': str(resp.get('status', 'none') or 'none'),
        'demo_allowed': bool(resp.get('demo_allowed')),
        'start_allowed': bool(resp.get('start_allowed')),
        'server_now': str(resp.get('server_now', '') or ''),
        'demo_started_at': str(resp.get('demo_started_at', '') or ''),
        'demo_expires_at': str(resp.get('demo_expires_at', '') or ''),
        'offline_grace_minutes': int(resp.get('offline_grace_minutes') or _SHV_OFFLINE_GRACE_MINS),
        'verified_local_at': _shv_utc_now().isoformat() + 'Z',
        'message': str(resp.get('message', '') or ''),
    }
    _shv_save_demo_cache(cache)
    return cache

# ---------- Demo API ----------
def _shv_demo_call(action, extra=None):
    session = _shv_ensure_session(silent=False)
    token = (session or {}).get('access_token', '')
    if not token:
        raise RuntimeError('Sign in to your SH Vertex Account first.')
    payload = {
        'action': action,
        'app_code': _SHV_APP_CODE,
        'demo_hours': _SHV_DEMO_HOURS,
        'device_code': _shv_get_device_code(),
        'device_fingerprint_hash': _shv_device_fingerprint(),
    }
    if extra:
        payload.update(extra)
    result = _shv_http('POST', _SHV_DEMO_FUNCTION_URL,
                       json_body=payload,
                       headers=_shv_headers(token))
    if not isinstance(result, dict):
        raise RuntimeError('Demo service returned an unexpected response.')
    return result

def _shv_demo_state_from_resp(resp, signed_in=True):
    status = str(resp.get('status', 'none') or 'none').strip().lower()
    server_now = _shv_parse_date(resp.get('server_now')) or _shv_utc_now()
    expires_at = _shv_parse_date(resp.get('demo_expires_at'))
    active = (bool(resp.get('demo_allowed')) and status == 'active'
              and expires_at is not None and expires_at > server_now)
    remaining_seconds = (max(0, int((expires_at - server_now).total_seconds()))
                         if expires_at else 0)
    if active:
        remain_text = _shv_format_remaining(remaining_seconds)
        message = resp.get('message') or f'Demo active: {remain_text} remaining.'
    else:
        remain_text = '0m'
        msgs = {
            'none':      'No demo started yet. Sign in and tap Start Demo.',
            'expired':   'Your demo has expired. Activate Pro to continue.',
            'converted': 'Demo converted to Pro. Thank you!',
            'blocked':   'Demo blocked. Activate Pro to continue.',
        }
        message = resp.get('message') or msgs.get(status, 'Demo not available right now.')
    return {
        'valid': active, 'signed_in': bool(signed_in),
        'status': status, 'start_allowed': bool(resp.get('start_allowed')),
        'message': message, 'remaining_text': remain_text,
        'remaining_seconds': remaining_seconds, 'hours': int(_SHV_DEMO_HOURS),
        'expires_at': expires_at, 'offline': False,
        'offline_grace_minutes': int(resp.get('offline_grace_minutes') or _SHV_OFFLINE_GRACE_MINS),
        'server_now': server_now,
    }

def _shv_demo_state_from_cache(cache, signed_in=True, error_msg=''):
    if not isinstance(cache, dict) or not cache:
        return None
    if str(cache.get('status', '')).lower() != 'active':
        return None
    expires_at = _shv_parse_date(cache.get('demo_expires_at'))
    verified_local = _shv_parse_date(cache.get('verified_local_at'))
    if expires_at is None or verified_local is None:
        return None
    now_dt = _shv_utc_now()
    grace_mins = int(cache.get('offline_grace_minutes') or _SHV_OFFLINE_GRACE_MINS)
    offline_deadline = min(
        verified_local + _dtd(minutes=grace_mins),
        expires_at    + _dtd(minutes=grace_mins)
    )
    if now_dt > offline_deadline:
        return None
    if now_dt <= expires_at:
        remaining_seconds = max(0, int((expires_at - now_dt).total_seconds()))
        remain_text = _shv_format_remaining(remaining_seconds)
        message = 'Demo active (cached). Reconnect within 1 hour to refresh.'
    else:
        remaining_seconds = max(0, int((offline_deadline - now_dt).total_seconds()))
        remain_text = _shv_format_remaining(remaining_seconds)
        message = f'Offline grace active. Reconnect within {remain_text} to verify.'
    if error_msg:
        message = f'{message}\nLast error: {error_msg}'
    return {
        'valid': True, 'signed_in': bool(signed_in),
        'status': 'active', 'start_allowed': False,
        'message': message, 'remaining_text': remain_text,
        'remaining_seconds': remaining_seconds, 'hours': int(_SHV_DEMO_HOURS),
        'expires_at': expires_at, 'offline': True,
        'offline_grace_minutes': grace_mins, 'server_now': now_dt,
    }

def _shv_get_demo_status():
    session = _shv_ensure_session(silent=True)
    signed_in = bool((session or {}).get('access_token'))
    if not signed_in:
        return {
            'valid': False, 'signed_in': False, 'status': 'none',
            'start_allowed': False,
            'message': 'Please sign in to your SH Vertex account.',
            'remaining_text': '0m', 'remaining_seconds': 0,
            'hours': int(_SHV_DEMO_HOURS), 'expires_at': None,
            'offline': False, 'server_now': _shv_utc_now(),
        }
    try:
        resp = _shv_demo_call('status')
        _shv_cache_demo_resp(resp)
        return _shv_demo_state_from_resp(resp, signed_in=True)
    except Exception as e:
        cache = _shv_load_demo_cache()
        cached = _shv_demo_state_from_cache(cache, signed_in=True, error_msg=str(e))
        if cached:
            return cached
        return {
            'valid': False, 'signed_in': True, 'status': 'error',
            'start_allowed': False,
            'message': 'Cannot verify demo. Check your internet connection.',
            'remaining_text': '0m', 'remaining_seconds': 0,
            'hours': int(_SHV_DEMO_HOURS), 'expires_at': None,
            'offline': False, 'server_now': _shv_utc_now(),
        }

def _shv_start_demo():
    session = _shv_ensure_session(silent=False)
    _shv_register_device(session)
    resp = _shv_demo_call('start')
    _shv_cache_demo_resp(resp)
    return _shv_demo_state_from_resp(resp, signed_in=True)

def _shv_mark_pro(license_id='', tier='pro'):
    try:
        session = _shv_ensure_session(silent=True)
        if not (session or {}).get('access_token'):
            return False
        resp = _shv_demo_call('mark_pro',
                              extra={"license_id": str(license_id or ''), "tier": tier})
        _shv_cache_demo_resp(resp)
        return True
    except Exception:
        return False

def _shv_cloud_account_label(session):
    if not session:
        return 'Not signed in', '', 'Standard'
    user    = session.get('user', {}) or {}
    profile = session.get('profile', {}) or {}
    email   = user.get('email', '') or profile.get('email', '') or 'Signed in'
    name    = profile.get('display_name', '') or user.get('email', '')
    plan    = profile.get('plan', 'Standard')
    return name, email, plan

def _shv_get_access_status():
    lic = _shv_load_license()
    if lic:
        ok, tier, msg, lid = _shv_check_license(lic.get('activation_code', ''))
        if ok:
            return {
                'valid': True, 'mode': 'licensed',
                'message': msg, 'tier': tier, 'license_id': lid, 'trial': None,
            }
    trial = _shv_get_demo_status()
    return {
        'valid': bool(trial.get('valid')),
        'mode': 'trial' if trial.get('valid') else 'none',
        'message': trial.get('message', 'License or demo required.'),
        'tier': None, 'license_id': None, 'trial': trial,
    }

# ---- UI helpers ----
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField

# AMOLED‑optimised colour palette
_C = {
    'bg':      '#000000',
    'card':    '#121212',
    'accent':  '#1f6feb',
    'accent2': '#1a1a1a',
    'border':  '#2a2a2a',
    'text':    '#e6edf3',
    'subtext': '#8b949e',
    'green':   '#1b9e46',
    'warning': '#d29922',
    'danger':  '#d93838',
    'purple':  '#7c3aed',
}

def c(key):
    return get_color_from_hex(_C.get(key, '#ffffff'))

# Helper: safe snackbar with forced dark background
def _snack(msg):
    from kivy.uix.label import Label
    from kivy.clock import Clock

    lbl = Label(
        text=msg,
        font_size=dp(14),
        color=(0.9, 0.9, 0.9, 1),   # light grey text
        halign="center",
        valign="middle",
        size_hint_y=None,
        padding=(dp(10), dp(10)),
    )
    # Make text fill the available width → horizontal
    lbl.bind(
        size=lambda s, *a: setattr(s, 'text_size', (s.width, None))
    )
    lbl.bind(texture_size=lambda s, ts: setattr(s, 'height', ts[1]))

    box = BoxLayout(orientation='vertical', padding=dp(8))
    box.add_widget(lbl)

    popup = Popup(
        title="",
        content=box,
        size_hint=(None, None),
        size=(dp(300), dp(60)),
        auto_dismiss=False,
        background_color=(0.1, 0.1, 0.1, 0.95),
        separator_color=(0,0,0,0),
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

def _bind_bg(w, key='bg'):
    from kivy.graphics import Color, Rectangle
    with w.canvas.before:
        Color(*c(key))
        r = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda ww, v: setattr(r, 'pos', v),
           size=lambda ww, v: setattr(r, 'size', v))

def _bind_rr(w, key='card', rad=14):
    from kivy.graphics import Color, RoundedRectangle
    with w.canvas.before:
        Color(*c(key))
        rr = RoundedRectangle(pos=w.pos, size=w.size, radius=[rad])
    w.bind(pos=lambda ww, v: setattr(rr, 'pos', v),
           size=lambda ww, v: setattr(rr, 'size', v))

def _bind_tinted(w, hex_col):
    from kivy.graphics import Color, RoundedRectangle
    col = list(get_color_from_hex(hex_col))
    col[3] = 0.18
    with w.canvas.before:
        Color(*col)
        rr = RoundedRectangle(pos=w.pos, size=w.size, radius=[12])
    w.bind(pos=lambda ww, v: setattr(rr, 'pos', v),
           size=lambda ww, v: setattr(rr, 'size', v))

def make_lbl(text, col='text', size=13, bold=False, halign='left', height=None):
    lbl = Label(text=text, font_size=dp(size), bold=bold, halign=halign,
                color=c(col), size_hint_y=None)
    if height:
        lbl.height = dp(height)
    else:
        lbl.bind(texture_size=lambda w, v: setattr(w, 'height', max(v[1], dp(20))))
    lbl.bind(size=lambda w, v: setattr(w, 'text_size', (v[0], None)))
    return lbl

def make_btn(text, col='accent', on_press=None):
    btn = MDRaisedButton(
        text=text,
        md_bg_color=c(col),
        size_hint=(1, None), height=dp(46),
        theme_text_color='Custom',
        text_color=c('text'),
    )
    if on_press:
        btn.bind(on_release=on_press)
    return btn

def make_input(hint, password=False, height=56):
    inp = MDTextField(
        hint_text=hint, password=password,
        mode='rectangle', size_hint_y=None, height=dp(height),
        fill_color_normal=get_color_from_hex('#1e1e1e'),
        fill_color_focus=get_color_from_hex('#2a2a2a'),
        line_color_normal=get_color_from_hex('#444444'),
        line_color_focus=get_color_from_hex(_C['accent']),
        hint_text_color_normal=get_color_from_hex(_C['subtext'])
    )
    return inp

def simple_popup(title, content, size_hint=(0.88, 0.52)):
    return Popup(title=title, content=content, size_hint=size_hint,
                 background_color=c('card'), separator_color=c('accent'))

def _show_message_popup(title, msg, size_hint=(0.82, 0.32)):
    box = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
    box.add_widget(make_lbl(msg, 'subtext', 13, halign='center'))
    pr = [None]
    box.add_widget(make_btn('OK', 'accent', on_press=lambda *_: pr[0].dismiss()))
    p = simple_popup(title, box, size_hint=size_hint)
    pr[0] = p
    p.open()


class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _bind_bg(self, 'bg')                     # black background

        # Container centering everything vertically
        root = BoxLayout(orientation='vertical', padding=dp(40))

        root.add_widget(BoxLayout())             # top spacer

        # Simple centered text (no KivyMD widgets needed)
        lbl = Label(
            text="Loading converter…",
            font_size=dp(20),
            color=c('text'),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(50),
        )
        lbl.bind(size=lbl.setter('text_size'))

        root.add_widget(lbl)

        # Small note below
        note = Label(
            text="Please wait",
            font_size=dp(14),
            color=c('subtext'),
            halign='center',
            size_hint_y=None,
            height=dp(30),
        )
        note.bind(size=note.setter('text_size'))

        root.add_widget(note)
        root.add_widget(BoxLayout())             # bottom spacer

        self.add_widget(root)


# ---- LicenseGateScreen (unchanged except for small fixes) ----
class LicenseGateScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ui_built = False

    def on_enter(self):
        if not self._ui_built:
            Clock.schedule_once(lambda dt: self.build_ui(), 0.05)
            self._ui_built = True

    def build_ui(self):
        self.clear_widgets()
        access    = _shv_get_access_status()
        trial     = access.get('trial') or {}
        is_licensed  = access.get('mode') == 'licensed'
        can_continue = bool(access.get('valid'))
        session   = _shv_ensure_session(silent=True)
        signed_in = bool((session or {}).get('access_token'))
        name, email, plan = _shv_cloud_account_label(session)

        root = BoxLayout(orientation='vertical')
        _bind_bg(root, 'bg')
        root.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))

        sv = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(12),
                            padding=[dp(14), dp(6), dp(14), dp(22)],
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        card = BoxLayout(orientation='vertical', spacing=dp(10),
                         padding=[dp(16), dp(14), dp(16), dp(16)],
                         size_hint_y=None)
        card.bind(minimum_height=card.setter('height'))
        _bind_rr(card, 'card', rad=18)

        # Title
        card.add_widget(make_lbl(
            'Universal Convertor by SHV Pro Access',
            'text', 22, bold=True, halign='center', height=36))
        card.add_widget(make_lbl(
            'Use a SH Vertex Account to start the one-time demo, or activate Pro on this device.',
            'subtext', 12, halign='center', height=40))

        # Device code box
        dev_code = _shv_get_device_code()
        dbox = BoxLayout(orientation='vertical', spacing=dp(4),
                         size_hint_y=None, height=dp(90),
                         padding=[dp(12), dp(10), dp(12), dp(10)])
        _bind_tinted(dbox, _C['accent2'])
        dbox.add_widget(make_lbl('DEVICE CODE', 'subtext', 11, bold=True, height=16))
        dbox.add_widget(make_lbl(dev_code, 'text', 16, bold=True, height=24))
        status_col = 'green' if can_continue else 'warning'
        dbox.add_widget(make_lbl(access.get('message', ''), status_col, 11, height=24))
        card.add_widget(dbox)

        # SH Vertex account box
        abox = BoxLayout(orientation='vertical', spacing=dp(4),
                         size_hint_y=None, height=dp(94),
                         padding=[dp(12), dp(10), dp(12), dp(10)])
        _bind_tinted(abox, _C['accent'] if signed_in else _C['border'])
        abox.add_widget(make_lbl('SH VERTEX ACCOUNT', 'subtext', 11, bold=True, height=16))
        abox.add_widget(make_lbl(
            'CONNECTED' if signed_in else 'NOT CONNECTED',
            'green' if signed_in else 'warning', 14, bold=True, height=20))
        abox.add_widget(make_lbl(name if signed_in else 'SH Vertex Account', 'subtext', 10, height=16))
        abox.add_widget(make_lbl(f'Plan: {plan}', 'subtext', 10, height=14))
        card.add_widget(abox)

        if is_licensed:
            lic = _shv_load_license() or {}
            payload = lic.get('payload') or {}
            lbox = BoxLayout(orientation='vertical', spacing=dp(4),
                             size_hint_y=None, height=dp(108),
                             padding=[dp(12), dp(10), dp(12), dp(10)])
            _bind_tinted(lbox, _C['green'])
            lbox.add_widget(make_lbl('ACTIVE PRO LICENSE', 'text', 11, bold=True, height=16))
            lbox.add_widget(make_lbl(f"ID: {access.get('license_id', '--')}", 'subtext', 10, height=16))
            tier_disp = (access.get('tier') or 'pro').upper()
            lbox.add_widget(make_lbl(f'Tier: {tier_disp}', 'subtext', 10, height=16))
            expiry = payload.get('expires_at') or payload.get('expiry') or 'Lifetime'
            lbox.add_widget(make_lbl(f'Expiry: {expiry}', 'subtext', 10, height=16))
            card.add_widget(lbox)
        else:
            demo_active = trial.get('status') == 'active'
            demobox = BoxLayout(orientation='vertical', spacing=dp(4),
                                size_hint_y=None, height=dp(110),
                                padding=[dp(12), dp(10), dp(12), dp(10)])
            _bind_tinted(demobox, _C['green'] if demo_active else _C['border'])
            demo_title = 'DEMO ACTIVE' if demo_active else 'DEMO LOCKED / EXPIRED'
            demobox.add_widget(make_lbl(demo_title, 'text', 11, bold=True, height=16))
            demobox.add_widget(make_lbl(
                f'Demo duration: {_SHV_DEMO_HOURS}h  •  Offline grace: {_SHV_OFFLINE_GRACE_MINS} min',
                'subtext', 10, height=16))
            demobox.add_widget(make_lbl(
                f"Remaining: {trial.get('remaining_text', '0m')}",
                'subtext', 10, height=16))
            demobox.add_widget(make_lbl(
                trial.get('message', 'Please sign in to your SH Vertex account.'),
                'subtext', 10, height=24))
            card.add_widget(demobox)

        # Account buttons row
        r1 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        if signed_in:
            r1.add_widget(make_btn('Sign Out', 'danger', on_press=lambda *_: self._sign_out()))
            r1.add_widget(make_btn('Refresh',  'purple', on_press=lambda *_: self.build_ui()))
        else:
            r1.add_widget(make_btn('Sign In',        'accent',  on_press=lambda *_: self._open_sign_in()))
            r1.add_widget(make_btn('Create Account', 'accent2', on_press=lambda *_: self._open_sign_up()))
        card.add_widget(r1)

        if not is_licensed:
            r2 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
            can_start  = signed_in and bool(trial.get('start_allowed', False))
            start_col  = 'green' if can_start else 'border'
            start_btn  = make_btn('Start Demo', start_col,
                                  on_press=lambda *_: self._start_demo())
            start_btn.disabled = not can_start
            r2.add_widget(start_btn)
            r2.add_widget(make_btn('Copy Device Code', 'border',
                                   on_press=lambda *_: self._copy_code()))
            card.add_widget(r2)

        # Activation code input
        self._code_input = make_input('Paste activation code here', height=110)
        card.add_widget(self._code_input)

        r3 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        r3.add_widget(make_btn('Copy Device Code', 'accent2',
                               on_press=lambda *_: self._copy_code()))
        r3.add_widget(make_btn('Paste Code', 'border',
                               on_press=lambda *_: setattr(
                                   self._code_input, 'text', Clipboard.paste() or '')))
        card.add_widget(r3)

        r4 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        r4.add_widget(make_btn('Activate Pro',  'accent',  on_press=lambda *_: self._activate()))
        r4.add_widget(make_btn('Check Status',  'purple',  on_press=lambda *_: self._check_status()))
        r4.add_widget(make_btn('Clear License', 'danger',  on_press=lambda *_: self._clear_license()))
        card.add_widget(r4)

        if can_continue:
            tier = access.get('tier', 'pro') if is_licensed else 'demo'
            card.add_widget(make_btn('Continue to App', 'green',
                                     on_press=lambda *_: self._continue_to_app(tier)))

        content.add_widget(card)
        sv.add_widget(content)
        root.add_widget(sv)
        self.add_widget(root)

    def _copy_code(self):
        Clipboard.copy(_shv_get_device_code())
        _show_message_popup('Copied', 'Device code copied to clipboard.', (0.62, 0.25))

    def _sign_out(self):
        _shv_clear_session()
        _shv_clear_demo_cache()
        self.build_ui()
        _show_message_popup('Signed Out', 'Disconnected from SH Vertex account.')

    def _open_sign_in(self):
        content_box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        content_box.bind(minimum_height=content_box.setter('height'))
        content_box.add_widget(make_lbl(
            'Sign in with your SH Vertex Account to unlock the one-time demo on this device.',
            'subtext', 11, height=42))
        email_f = make_input('Email address')
        pw_f    = make_input('Password', password=True)
        content_box.add_widget(email_f)
        content_box.add_widget(pw_f)
        br = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        cancel_btn = make_btn('Cancel', 'border')
        signin_btn = make_btn('Sign In', 'accent')
        br.add_widget(cancel_btn)
        br.add_widget(signin_btn)
        content_box.add_widget(br)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll.add_widget(content_box)

        p = Popup(title='SH Vertex Sign In', content=scroll,
                  size_hint=(0.9, 0.7), auto_dismiss=False,
                  background_color=c('card'), separator_color=c('accent'))
        p.open()

        def do_sign_in(*_):
            email = email_f.text.strip()
            pw = pw_f.text
            if not email or not pw:
                _show_message_popup('Missing Details', 'Enter your email and password.')
                return
            try:
                _shv_sign_in(email, pw)
                p.dismiss()
                self.build_ui()
                _show_message_popup('Signed In', 'SH Vertex account connected successfully.')
            except Exception as e:
                _show_message_popup('Sign In Failed', _shv_error_msg(e), (0.88, 0.36))

        cancel_btn.bind(on_release=p.dismiss)
        signin_btn.bind(on_release=do_sign_in)

    def _open_sign_up(self):
        content_box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        content_box.bind(minimum_height=content_box.setter('height'))
        content_box.add_widget(make_lbl(
            'Create a SH Vertex Account to start the one-time demo.',
            'subtext', 11, height=36))
        name_f  = make_input('Display name')
        email_f = make_input('Email address')
        pw_f    = make_input('Password (min 6 characters)', password=True)
        content_box.add_widget(name_f)
        content_box.add_widget(email_f)
        content_box.add_widget(pw_f)
        br = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        cancel_btn = make_btn('Cancel', 'border')
        create_btn = make_btn('Create', 'accent')
        br.add_widget(cancel_btn)
        br.add_widget(create_btn)
        content_box.add_widget(br)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll.add_widget(content_box)

        p = Popup(title='Create SH Vertex Account', content=scroll,
                  size_hint=(0.9, 0.7), auto_dismiss=False,
                  background_color=c('card'), separator_color=c('accent'))
        p.open()

        def do_sign_up(*_):
            name  = name_f.text.strip()
            email = email_f.text.strip()
            pw    = pw_f.text
            if not email or not pw:
                _show_message_popup('Missing Details', 'Enter at least your email and password.')
                return
            if len(pw) < 6:
                _show_message_popup('Weak Password', 'Use a password with at least 6 characters.')
                return
            try:
                _, needs_conf = _shv_sign_up(email, pw, name)
                p.dismiss()
                if needs_conf:
                    _show_message_popup('Check Your Email',
                                        'Account created. Confirm your email, then sign in here.')
                else:
                    self.build_ui()
                    _show_message_popup('Account Ready', 'SH Vertex account created and connected.')
            except Exception as e:
                _show_message_popup('Sign Up Failed', _shv_error_msg(e), (0.88, 0.36))

        cancel_btn.bind(on_release=p.dismiss)
        create_btn.bind(on_release=do_sign_up)

    def _start_demo(self):
        def _do():
            try:
                st = _shv_start_demo()
                Clock.schedule_once(lambda dt: self.build_ui(), 0)
                if st.get('valid'):
                    Clock.schedule_once(lambda dt: _show_message_popup(
                        'Demo Started',
                        f"Your {_SHV_DEMO_HOURS}-hour demo is now active!\n"
                        f"Remaining: {st.get('remaining_text', '?')}"), 0.1)
                else:
                    Clock.schedule_once(lambda dt: _show_message_popup(
                        'Demo Status', st.get('message', 'Demo unavailable.')), 0.1)
            except Exception as e:
                Clock.schedule_once(lambda dt: _show_message_popup(
                    'Demo Start Failed', _shv_error_msg(e), (0.88, 0.36)), 0)
        _dth.Thread(target=_do, daemon=True).start()

    def _activate(self):
        code = (self._code_input.text or '').strip()
        if not code:
            _show_message_popup('No Code', 'Paste your activation code first.')
            return
        try:
            payload, sig = _shv_decode_code(code)
        except Exception as e:
            _show_message_popup('Invalid Code', f'Could not decode: {e}')
            return
        if not _shv_verify(payload, sig):
            _show_message_popup('Invalid Code', 'Signature verification failed.')
            return
        if payload.get('app', '').lower() != _SHV_BUNDLE_APP.lower():
            _show_message_popup('Wrong Product', 'This code is for a different app.')
            return
        device = _shv_get_device_code()
        bound  = str(payload.get('device_code', '') or '').upper()
        if bound and bound != device.upper():
            _show_message_popup('Device Mismatch',
                                f'This code is bound to a different device.\nYour device code: {device}')
            return
        tier = str(payload.get('tier', 'pro')).lower()
        lid  = str(payload.get('license_id', '') or '')
        _shv_save_license(code, payload)
        def _record():
            _shv_mark_pro(license_id=lid, tier=tier)
        _dth.Thread(target=_record, daemon=True).start()
        _show_message_popup('License Activated',
                            f'{tier.upper()} license activated.\nID: {lid}\nTap Continue to App.')
        self.build_ui()

    def _check_status(self):
        lic = _shv_load_license()
        if not lic:
            _show_message_popup('License Status', 'No license activated on this device.')
            return
        ok, tier, msg, lid = _shv_check_license(lic.get('activation_code', ''))
        _show_message_popup('License Status',
                            f"Valid: {'Yes' if ok else 'No'}\nTier: {tier}\nID: {lid}\n{msg}")

    def _clear_license(self):
        _shv_delete_license()
        _shv_clear_demo_cache()
        self.build_ui()
        _show_message_popup('Cleared', 'License removed from this device.')

    def _continue_to_app(self, tier):
        # 1. Show loading screen immediately
        if not self.manager.has_screen('loading'):
            self.manager.add_widget(LoadingScreen(name='loading'))
        self.manager.current = 'loading'
    
        # 2. Schedule the heavy work and final switch
        def _do_switch(dt):
            for name, cls in SCREEN_MAP:
                if not self.manager.has_screen(name):
                    self.manager.add_widget(cls(name=name))
            apply_app_theme(_current_theme)
            self.manager.current = 'home'
    
        Clock.schedule_once(_do_switch, 0.1)

class SHVLicenseGateApp(MDApp):
    def build(self):
        sm = ScreenManager(transition=NoTransition())
        from kivy.graphics import Color, Rectangle
        with sm.canvas.before:
            Color(0, 0, 0, 1)
            sm._bg_rect = Rectangle(pos=sm.pos, size=sm.size)
        sm.bind(pos=lambda i, v: setattr(sm._bg_rect, 'pos', v),
                size=lambda i, v: setattr(sm._bg_rect, 'size', v))
        sm.add_widget(LicenseGateScreen(name='gate'))
        Window.bind(on_keyboard=self._on_keyboard)
        return sm

    def _on_keyboard(self, window, key, *args):
        if key == 27:  # BACK key
            curr = self.root.current
            if curr == 'gate':
                self.root.get_screen('gate')._confirm_exit()
                return True
            if curr != 'home':
                self.root.transition.direction = 'right'
                self.root.current = 'home'
                return True
            else:
                self.root.get_screen('home')._confirm_exit()
                return True
        return False

# ════════════════════════════════════════════════════════════════════════════
# UNIVERSAL CONVERTER APP (fixed & extended)
# ════════════════════════════════════════════════════════════════════════════

from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.network.urlrequest import UrlRequest
import math

KV = """
#:import dp kivy.metrics.dp

<RoundBox>:
    canvas.before:
        Color:
            rgba: root.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: root.box_radius
<FlatIconBtn>:
    size_hint: None, None
    size: dp(44), dp(44)
    canvas.before:
        Color:
            rgba: root.btn_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [root.btn_radius]*4
    MDIcon:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.icon_color
        font_size: dp(20)
        halign: "center"
        valign: "middle"
        pos_hint: {"center_x": .5, "center_y": .5}
<BaseChip>:
    size_hint: 1, None
    height: dp(42)
    canvas.before:
        Color:
            rgba: (root.accent[0]*0.22, root.accent[1]*0.22, root.accent[2]*0.22, 1) if root.is_active else (0.11, 0.11, 0.11, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]*4
    MDLabel:
        text: root.chip_text
        halign: "center"
        font_style: "Button"
        theme_text_color: "Custom"
        text_color: root.accent if root.is_active else (0.42, 0.42, 0.42, 1)
        bold: root.is_active
<UnitChip>:
    size_hint: None, None
    height: dp(36)
    width: self.width
    padding: [dp(14), 0]
    canvas.before:
        Color:
            rgba: (root.accent[0]*0.22, root.accent[1]*0.22, root.accent[2]*0.22, 1) if root.is_active else (0.10, 0.10, 0.10, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [18]*4
    MDLabel:
        text: root.chip_text
        halign: "center"
        font_style: "Button"
        theme_text_color: "Custom"
        text_color: root.accent if root.is_active else (0.40, 0.40, 0.40, 1)
        bold: root.is_active
<BaseRow>:
    size_hint_y: None
    height: dp(34)
    spacing: dp(10)
    RoundBox:
        bg_color: root.base_color[0]*0.14, root.base_color[1]*0.14, root.base_color[2]*0.14, 1
        box_radius: [7]*4
        size_hint_x: None
        width: dp(52)
        MDLabel:
            text: root.base_label
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: root.base_color
            halign: "center"
            bold: True
    MDLabel:
        id: value_lbl
        text: "—"
        font_style: "Body2"
        theme_text_color: "Custom"
        text_color: root.text_color
        valign: "center"
        shorten: True
        shorten_from: "right"
    FlatIconBtn:
        icon: "content-copy"
        btn_bg: root.base_color[0]*0.1, root.base_color[1]*0.1, root.base_color[2]*0.1, 1
        icon_color: root.base_color
        btn_radius: 8
        size: dp(32), dp(32)
        on_release: root.copy_value()
<ModuleCard>:
    size_hint_y: None
    height: dp(88)
    canvas.before:
        Color:
            rgba: root.card_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [18]*4
    BoxLayout:
        padding: [dp(16), dp(10)]
        spacing: dp(14)
        RoundBox:
            bg_color: root.accent[0]*0.15, root.accent[1]*0.15, root.accent[2]*0.15, 1
            box_radius: [24]*4
            size_hint: None, None
            size: dp(50), dp(50)
            pos_hint: {"center_y": .5}
            MDIcon:
                icon: root.mod_icon
                theme_text_color: "Custom"
                text_color: root.accent
                halign: "center"
                font_size: dp(24)
        BoxLayout:
            orientation: "vertical"
            spacing: dp(2)
            pos_hint: {"center_y": .5}
            MDLabel:
                text: root.title
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: root.card_title_color
                bold: True
            MDLabel:
                text: root.subtitle
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: root.card_subtitle_color
        MDIcon:
            size_hint_x: None
            width: dp(28)
            icon: "chevron-right"
            theme_text_color: "Custom"
            text_color: root.accent
            font_size: dp(22)
            halign: "center"
            pos_hint: {"center_y": .5}
<BottomNavBar>:
    size_hint_y: None
    height: dp(58)
    spacing: 0
    canvas.before:
        Color:
            rgba: root.bar_bg
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: root.bar_border
        Rectangle:
            pos: self.x, self.top
            size: self.width, dp(1)
    MDRaisedButton:
        text: root.btn_text
        font_size: dp(28)          # ← bigger
        bold: True                 # ← bold
        md_bg_color: root.active_color[:3] + [0.2]
        theme_text_color: "Custom"
        text_color: root.active_color
        size_hint: (1, 1)
        on_release: root.btn_callback()
<HomeScreen>:
    canvas.before:
        Color:
            rgba: root.screen_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: [dp(20), dp(14), dp(10), dp(14)]
            MDLabel:
                text: "Universal Convertor by SHV"
                font_style: "H5"
                theme_text_color: "Custom"
                text_color: root.header_color
                bold: True
            MDIconButton:
                icon: "cog"
                theme_text_color: "Custom"
                text_color: root.header_color
                size_hint_x: None
                width: dp(44)
                on_release: root.open_settings()
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            padding: [dp(20), 0]
            MDLabel:
                text: "Select a conversion module"
                font_style: "Body1"
                theme_text_color: "Custom"
                text_color: root.subtitle_color
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: [dp(14), dp(8)]
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                ModuleCard:
                    mod_icon: "numeric"
                    title: "Numeral Systems"
                    subtitle: "DEC · BIN · HEX · OCT · ASCII"
                    accent: 0.0, 0.85, 0.72, 1
                    on_release: root.go("numeral")
                ModuleCard:
                    mod_icon: "ruler"
                    title: "Length & Distance"
                    subtitle: "km · mi · ft · in · cm · m · yd"
                    accent: 0.4, 0.6, 1.0, 1
                    on_release: root.go("length")
                ModuleCard:
                    mod_icon: "weight"
                    title: "Weight & Mass"
                    subtitle: "kg · lb · oz · g · mg · t · st"
                    accent: 1.0, 0.6, 0.2, 1
                    on_release: root.go("weight")
                ModuleCard:
                    mod_icon: "thermometer"
                    title: "Temperature"
                    subtitle: "°C · °F · K · °R"
                    accent: 1.0, 0.35, 0.35, 1
                    on_release: root.go("temperature")
                ModuleCard:
                    mod_icon: "database"
                    title: "Data Storage"
                    subtitle: "B · KB · MB · GB · TB · PB"
                    accent: 0.8, 0.4, 1.0, 1
                    on_release: root.go("datastorage")
                ModuleCard:
                    mod_icon: "speedometer"
                    title: "Speed"
                    subtitle: "km/h · mph · m/s · knot · mach"
                    accent: 0.2, 0.85, 0.4, 1
                    on_release: root.go("speed")
                ModuleCard:
                    mod_icon: "vector-square"
                    title: "Area"
                    subtitle: "m² · km² · ft² · ac · ha · mi²"
                    accent: 1.0, 0.75, 0.2, 1
                    on_release: root.go("area")
                ModuleCard:
                    mod_icon: "cup"
                    title: "Volume"
                    subtitle: "L · mL · gal · fl oz · m³"
                    accent: 0.3, 0.75, 1.0, 1
                    on_release: root.go("volume")
                ModuleCard:
                    mod_icon: "clock-outline"
                    title: "Time"
                    subtitle: "ns · s · min · h · day · yr · cent"
                    accent: 0.6, 0.5, 1.0, 1
                    on_release: root.go("time")
                ModuleCard:
                    mod_icon: "gauge"
                    title: "Pressure"
                    subtitle: "Pa · bar · psi · atm · mmHg"
                    accent: 1.0, 0.45, 0.7, 1
                    on_release: root.go("pressure")
                ModuleCard:
                    mod_icon: "lightning-bolt"
                    title: "Energy"
                    subtitle: "J · kJ · cal · kcal · kWh · BTU"
                    accent: 1.0, 0.8, 0.0, 1
                    on_release: root.go("energy")
                ModuleCard:
                    mod_icon: "flash"
                    title: "Power"
                    subtitle: "W · kW · MW · hp · BTU/h"
                    accent: 0.0, 0.9, 0.6, 1
                    on_release: root.go("power")
                ModuleCard:
                    mod_icon: "rotate-right"
                    title: "Angle"
                    subtitle: "° · rad · grad · arcmin · rev"
                    accent: 0.9, 0.5, 0.2, 1
                    on_release: root.go("angle")
                ModuleCard:
                    mod_icon: "sine-wave"
                    title: "Frequency"
                    subtitle: "Hz · kHz · MHz · GHz · rpm"
                    accent: 0.5, 0.85, 0.5, 1
                    on_release: root.go("frequency")
                ModuleCard:
                    mod_icon: "gas-station"
                    title: "Fuel Economy"
                    subtitle: "km/L · L/100km · mpg US · mpg UK"
                    accent: 0.85, 0.4, 0.4, 1
                    on_release: root.go("fuel")
                ModuleCard:
                    mod_icon: "currency-usd"
                    title: "Currency (Live)"
                    subtitle: "USD · EUR · GBP · JPY · CNY + more"
                    accent: 0.3, 0.85, 0.55, 1
                    on_release: root.go("currency")
                ModuleCard:
                    mod_icon: "car-brake-abs"
                    title: "Acceleration"
                    subtitle: "m/s² · ft/s² · g"
                    accent: 0.6, 0.4, 1.0, 1
                    on_release: root.go("acceleration")
                ModuleCard:
                    mod_icon: "engine"
                    title: "Torque"
                    subtitle: "Nm · lb·ft · kg·m"
                    accent: 1.0, 0.55, 0.0, 1
                    on_release: root.go("torque")
                Widget:
                    size_hint_y: None
                    height: dp(16)
<NumeralScreen>:
    canvas.before:
        Color:
            rgba: root.screen_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: [dp(2), dp(8), dp(14), dp(8)]
            spacing: dp(2)
            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: root.header_color
                on_release: root.go_back()
            MDLabel:
                text: root.screen_title
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: root.header_color
                bold: True
                valign: "center"
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: [dp(14), dp(4)]
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDLabel:
                    text: "CONVERSION TYPE"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    BaseChip:
                        id: chip_dec
                        chip_text: "DEC"
                        is_active: True
                        accent: 0.0, 0.85, 0.72, 1
                        on_release: root.select_base("dec")
                    BaseChip:
                        id: chip_bin
                        chip_text: "BIN"
                        accent: 0.0, 0.85, 0.72, 1
                        on_release: root.select_base("bin")
                    BaseChip:
                        id: chip_hex
                        chip_text: "HEX"
                        accent: 0.0, 0.85, 0.72, 1
                        on_release: root.select_base("hex")
                    BaseChip:
                        id: chip_oct
                        chip_text: "OCT"
                        accent: 0.0, 0.85, 0.72, 1
                        on_release: root.select_base("oct")
                    BaseChip:
                        id: chip_txt
                        chip_text: "TXT"
                        accent: 1.0, 0.6, 0.9, 1
                        on_release: root.select_base("txt")
                RoundBox:
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: dp(306)
                    padding: dp(14)
                    BoxLayout:
                        orientation: "vertical"
                        spacing: dp(8)
                        BoxLayout:
                            size_hint_y: None
                            height: dp(26)
                            spacing: dp(6)
                            MDIcon:
                                icon: "arrow-up-circle"
                                theme_text_color: "Custom"
                                text_color: 0.0, 0.85, 0.72, 1
                                size_hint_x: None
                                width: dp(22)
                                font_size: dp(18)
                            MDLabel:
                                id: from_label
                                text: "From: DECIMAL"
                                font_style: "Subtitle2"
                                theme_text_color: "Custom"
                                text_color: root.header_color
                                bold: True
                        BoxLayout:
                            size_hint_y: None
                            height: dp(52)
                            spacing: dp(8)
                            MDTextField:
                                id: input_field
                                hint_text: "Enter decimal number..."
                                mode: "rectangle"
                                line_color_focus: 0.0, 0.85, 0.72, 1
                                line_color_normal: 0.2, 0.2, 0.2, 1
                                text_color_normal: root.text_color
                                text_color_focus: root.text_color
                                hint_text_color_normal: root.subtitle_color
                                fill_color_normal: root.card_bg
                                fill_color_focus: root.card_bg
                                font_size: dp(15)
                                on_text: root.do_convert(self.text)
                            FlatIconBtn:
                                icon: "content-paste"
                                btn_bg: root.header_color[:3] + [0.13]
                                icon_color: root.header_color
                                btn_radius: 10
                                size: dp(46), dp(46)
                                on_release: root.paste_input()
                        BoxLayout:
                            size_hint_y: None
                            height: dp(38)
                            Widget:
                            FlatIconBtn:
                                icon: "swap-vertical"
                                btn_bg: root.header_color[:3] + [0.13]
                                icon_color: root.header_color
                                btn_radius: 18
                                size: dp(50), dp(36)
                                on_release: root.swap_conversion()
                            Widget:
                        BoxLayout:
                            size_hint_y: None
                            height: dp(26)
                            spacing: dp(6)
                            MDIcon:
                                icon: "arrow-down-circle"
                                theme_text_color: "Custom"
                                text_color: 0.55, 0.55, 1.0, 1
                                size_hint_x: None
                                width: dp(22)
                                font_size: dp(18)
                            MDLabel:
                                id: to_label
                                text: "To: ALL"
                                font_style: "Subtitle2"
                                theme_text_color: "Custom"
                                text_color: 0.55, 0.55, 1.0, 1
                                bold: True
                        BoxLayout:
                            size_hint_y: None
                            height: dp(52)
                            spacing: dp(8)
                            MDTextField:
                                id: output_field
                                hint_text: "Result..."
                                mode: "rectangle"
                                readonly: True
                                line_color_focus: 0.55, 0.55, 1.0, 1
                                line_color_normal: 0.2, 0.2, 0.2, 1
                                text_color_normal: 0.82, 0.82, 1.0, 1
                                hint_text_color_normal: 0.28, 0.28, 0.28, 1
                                fill_color_normal: 0.07, 0.07, 0.13, 1
                                fill_color_focus: 0.09, 0.09, 0.16, 1
                                font_size: dp(13)
                            FlatIconBtn:
                                icon: "content-copy"
                                btn_bg: 0.55, 0.55, 1.0, 0.13
                                icon_color: 0.55, 0.55, 1.0, 1
                                btn_radius: 10
                                size: dp(46), dp(46)
                                on_release: root.copy_output()
                MDLabel:
                    text: "ALL REPRESENTATIONS"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                RoundBox:
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: dp(218)
                    padding: [dp(14), dp(10)]
                    BoxLayout:
                        orientation: "vertical"
                        spacing: dp(8)
                        BaseRow:
                            id: row_dec
                            base_label: "DEC"
                            base_color: 0.0, 0.85, 0.72, 1
                            text_color: root.text_color
                        BaseRow:
                            id: row_bin
                            base_label: "BIN"
                            base_color: 1.0, 0.75, 0.2, 1
                            text_color: root.text_color
                        BaseRow:
                            id: row_hex
                            base_label: "HEX"
                            base_color: 0.55, 0.55, 1.0, 1
                            text_color: root.text_color
                        BaseRow:
                            id: row_oct
                            base_label: "OCT"
                            base_color: 1.0, 0.45, 0.45, 1
                            text_color: root.text_color
                        BaseRow:
                            id: row_txt
                            base_label: "TXT"
                            base_color: 1.0, 0.6, 0.9, 1
                            text_color: root.text_color
                MDLabel:
                    id: tip_label
                    text: "💡 Tap any chip to set it as input"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(26)
                    halign: "center"
                Widget:
                    size_hint_y: None
                    height: dp(80)
<GenericUnitScreen>:
    canvas.before:
        Color:
            rgba: root.screen_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: [dp(2), dp(8), dp(14), dp(8)]
            spacing: dp(2)
            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: root.header_color
                on_release: root.go_back()
            MDLabel:
                id: screen_title
                text: root.screen_title
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: root.header_color
                bold: True
                valign: "center"
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: [dp(14), dp(4)]
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDLabel:
                    text: "FROM"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                ScrollView:
                    size_hint_y: None
                    height: dp(40)
                    do_scroll_x: True
                    do_scroll_y: False
                    bar_width: 0
                    BoxLayout:
                        id: from_chips
                        size_hint_x: None
                        width: self.minimum_width
                        spacing: dp(6)
                        padding: [dp(2), dp(2)]
                RoundBox:
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: dp(80)
                    padding: [dp(14), dp(10)]
                    BoxLayout:
                        spacing: dp(8)
                        MDTextField:
                            id: input_field
                            hint_text: "Enter value..."
                            mode: "rectangle"
                            line_color_focus: root.header_color
                            line_color_normal: 0.2, 0.2, 0.2, 1
                            text_color_normal: root.text_color
                            text_color_focus: root.text_color
                            hint_text_color_normal: root.subtitle_color
                            fill_color_normal: root.card_bg
                            fill_color_focus: root.card_bg
                            font_size: dp(15)
                            on_text: root.do_convert(self.text)
                        FlatIconBtn:
                            icon: "content-paste"
                            btn_bg: root.header_color[:3] + [0.15]
                            icon_color: root.header_color
                            btn_radius: 10
                            size: dp(46), dp(46)
                            on_release: root.paste_input()
                MDLabel:
                    text: "TO — ALL UNITS"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                RoundBox:
                    id: results_box
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [dp(14), dp(10)]
                    BoxLayout:
                        id: results_col
                        orientation: "vertical"
                        spacing: dp(8)
                        size_hint_y: None
                        height: self.minimum_height
                Widget:
                    size_hint_y: None
                    height: dp(80)
<CurrencyScreen>:
    canvas.before:
        Color:
            rgba: root.screen_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: [dp(2), dp(8), dp(14), dp(8)]
            spacing: dp(2)
            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: root.header_color
                on_release: root.go_back()
            MDLabel:
                text: "Currency (Live)"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: root.header_color
                bold: True
                valign: "center"
            MDIconButton:
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: root.header_color
                on_release: root.fetch_rates()
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: [dp(14), dp(4)]
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDLabel:
                    id: rate_status
                    text: "Tap ↻ to load live rates"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                    halign: "center"
                MDLabel:
                    text: "FROM CURRENCY"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                ScrollView:
                    size_hint_y: None
                    height: dp(40)
                    do_scroll_x: True
                    do_scroll_y: False
                    bar_width: 0
                    BoxLayout:
                        id: from_chips
                        size_hint_x: None
                        width: self.minimum_width
                        spacing: dp(6)
                        padding: [dp(2), dp(2)]
                RoundBox:
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: dp(80)
                    padding: [dp(14), dp(10)]
                    BoxLayout:
                        spacing: dp(8)
                        MDTextField:
                            id: amount_field
                            hint_text: "Enter amount..."
                            mode: "rectangle"
                            line_color_focus: root.header_color
                            line_color_normal: 0.2, 0.2, 0.2, 1
                            text_color_normal: root.text_color
                            text_color_focus: root.text_color
                            hint_text_color_normal: root.subtitle_color
                            fill_color_normal: root.card_bg
                            fill_color_focus: root.card_bg
                            font_size: dp(15)
                            input_filter: "float"
                            on_text: root.do_convert()
                        FlatIconBtn:
                            icon: "content-paste"
                            btn_bg: root.header_color[:3] + [0.13]
                            icon_color: root.header_color
                            btn_radius: 10
                            size: dp(46), dp(46)
                            on_release: root.paste_input()
                MDLabel:
                    text: "TO — ALL CURRENCIES"
                    font_style: "Overline"
                    theme_text_color: "Custom"
                    text_color: root.subtitle_color
                    size_hint_y: None
                    height: dp(22)
                RoundBox:
                    id: results_box
                    bg_color: root.card_bg
                    box_radius: [16]*4
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [dp(14), dp(10)]
                    BoxLayout:
                        id: results_col
                        orientation: "vertical"
                        spacing: dp(8)
                        size_hint_y: None
                        height: self.minimum_height
                Widget:
                    size_hint_y: None
                    height: dp(80)
"""

Builder.load_string(KV)

# ── Global Theme ──
THEMES = {
    "amoled": {
        "screen_bg":          [0, 0, 0, 1],
        "header_color":       [0.0, 0.85, 0.72, 1],
        "subtitle_color":     [0.48, 0.48, 0.48, 1],
        "text_color":         [1, 1, 1, 1],
        "card_bg":            [0.05, 0.05, 0.05, 1],
        "card_title_color":   [1, 1, 1, 1],
        "card_subtitle_color":[0.42, 0.42, 0.42, 1],
        "bottom_nav_bg":      [0, 0, 0, 1],
        "bottom_nav_border":  [0.10, 0.10, 0.10, 1],
    },
    "grey": {
        "screen_bg":          [0.11, 0.11, 0.13, 1],
        "header_color":       [0.0, 0.85, 0.72, 1],
        "subtitle_color":     [0.55, 0.55, 0.60, 1],
        "text_color":         [0.95, 0.95, 0.95, 1],
        "card_bg":            [0.17, 0.17, 0.20, 1],
        "card_title_color":   [0.95, 0.95, 0.95, 1],
        "card_subtitle_color":[0.52, 0.52, 0.58, 1],
        "bottom_nav_bg":      [0.08, 0.08, 0.10, 1],
        "bottom_nav_border":  [0.20, 0.20, 0.24, 1],
    },
    "light": {
        "screen_bg":          [0.96, 0.96, 0.96, 1],
        "header_color":       [0.0, 0.60, 0.52, 1],
        "subtitle_color":     [0.40, 0.40, 0.40, 1],
        "text_color":         [0.10, 0.10, 0.10, 1],
        "card_bg":            [1, 1, 1, 1],
        "card_title_color":   [0.10, 0.10, 0.10, 1],
        "card_subtitle_color":[0.45, 0.45, 0.45, 1],
        "bottom_nav_bg":      [1, 1, 1, 1],
        "bottom_nav_border":  [0.82, 0.82, 0.82, 1],
    },
}

_current_theme = "amoled"

def apply_app_theme(theme_name):
    global _current_theme
    _current_theme = theme_name
    app = MDApp.get_running_app()
    sm = app.root

    # Switch KivyMD itself into Dark or Light mode
    app.theme_cls.theme_style = "Light" if theme_name == "light" else "Dark"

    # Set the window background colour
    t = THEMES[theme_name]
    Window.clearcolor = (*t["screen_bg"][:3], 1)

    # Update every screen that knows how to apply a theme
    for screen in sm.screens:
        if hasattr(screen, 'apply_theme'):
            screen.apply_theme(theme_name)


class RoundBox(BoxLayout):
    bg_color   = ListProperty([0.07, 0.07, 0.07, 1])
    box_radius = ListProperty([12, 12, 12, 12])

class FlatIconBtn(ButtonBehavior, BoxLayout):
    icon       = StringProperty("help")
    btn_bg     = ListProperty([0.15, 0.15, 0.15, 1])
    icon_color = ListProperty([1, 1, 1, 1])
    btn_radius = NumericProperty(10)

class BaseChip(ButtonBehavior, BoxLayout):
    chip_text = StringProperty("")
    is_active = BooleanProperty(False)
    accent    = ListProperty([0.0, 0.85, 0.72, 1])

class UnitChip(ButtonBehavior, BoxLayout):
    chip_text = StringProperty("")
    is_active = BooleanProperty(False)
    accent    = ListProperty([0.0, 0.85, 0.72, 1])
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(chip_text=self._resize)
        Clock.schedule_once(self._resize)
    def _resize(self, *_):
        self.width = len(self.chip_text) * dp(9) + dp(32)

class BaseRow(BoxLayout):
    base_label = StringProperty("UNIT")
    base_color = ListProperty([0.0, 0.85, 0.72, 1])
    text_color = ListProperty([1,1,1,1])
    def set_value(self, val):
        self.ids.value_lbl.text = val
    def copy_value(self):
        val = self.ids.value_lbl.text
        if val not in ("—", "error"):
            Clipboard.copy(val)
            _snack(f"Copied: {val[:36]}{'…' if len(val) > 36 else ''}")
        else:
            _snack("Nothing to copy")

class ModuleCard(ButtonBehavior, BoxLayout):
    mod_icon         = StringProperty("help-circle")
    title            = StringProperty("")
    subtitle         = StringProperty("")
    accent           = ListProperty([0.0, 0.85, 0.72, 1])
    card_bg          = ListProperty([0.07, 0.07, 0.07, 1])
    card_title_color = ListProperty([1, 1, 1, 1])
    card_subtitle_color = ListProperty([0.44, 0.44, 0.44, 1])

class BottomNavBar(ButtonBehavior, BoxLayout):
    bar_bg       = ListProperty([0.04, 0.04, 0.04, 1])
    bar_border   = ListProperty([0.12, 0.12, 0.12, 1])
    active_color = ListProperty([0.0, 0.85, 0.72, 1])
    btn_text     = StringProperty("Home")
    btn_callback = None

class ConverterScreen(MDScreen):
    screen_bg          = ListProperty([0,0,0,1])
    header_color       = ListProperty([0.0,0.85,0.72,1])
    subtitle_color     = ListProperty([0.48,0.48,0.48,1])
    text_color         = ListProperty([1,1,1,1])
    card_bg            = ListProperty([0.05,0.05,0.05,1])
    card_title_color   = ListProperty([1,1,1,1])
    card_subtitle_color= ListProperty([0.42,0.42,0.42,1])
    screen_title       = StringProperty("")
    _bottom_nav_added  = False

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget)
        if not self._bottom_nav_added:
            self._bottom_nav_added = True
            root = self.children[0] if self.children else None
            if root and isinstance(root, BoxLayout):
                has_nav = any(isinstance(child, BottomNavBar) for child in root.children)
                if not has_nav:
                    nav = BottomNavBar(bar_bg=[0.04,0.04,0.04,1],
                                       bar_border=[0.12,0.12,0.12,1],
                                       active_color=self.header_color)
                    if self.name == 'home':
                        nav.btn_text = 'EXIT'
                        nav.btn_callback = self._confirm_exit
                    else:
                        nav.btn_text = 'HOME'
                        nav.btn_callback = lambda: setattr(self.manager, 'current', 'home')
                    root.add_widget(nav)

    def apply_theme(self, theme_name):
        t = THEMES[theme_name]
        self.screen_bg    = t["screen_bg"]
        self.header_color = t["header_color"]
        self.subtitle_color = t["subtitle_color"]
        self.text_color   = t["text_color"]
        self.card_bg      = t["card_bg"]
        self.card_title_color = t["card_title_color"]
        self.card_subtitle_color = t["card_subtitle_color"]

    def _confirm_exit(self):
        if not hasattr(self, '_exit_dialog'):
            self._exit_dialog = MDDialog(
                title="Exit App",
                text="Are you sure you want to exit UniConverter?",
                # NO md_bg_color – let the dialog use the current theme
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.header_color,
                        on_release=lambda x: self._exit_dialog.dismiss(),
                    ),
                    MDFlatButton(
                        text="EXIT",
                        theme_text_color="Custom",
                        text_color=(1.0, 0.3, 0.3, 1),
                        on_release=lambda x: MDApp.get_running_app().stop(),
                    ),
                ],
            )
        self._exit_dialog.open()

class HomeScreen(ConverterScreen):
    screen_title = "Universal Convertor by SHV"
    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
    def go(self, name):
        self.manager.transition.direction = "left"
        self.manager.current = name
    def open_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

class SettingsScreen(ConverterScreen):
    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self.clear_widgets()
        # Top bar
        top = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back_btn = MDIconButton(icon="arrow-left", theme_text_color="Custom", text_color=self.header_color)
        back_btn.bind(on_release=self.go_back)
        title = MDLabel(text="Settings", font_style="H6", theme_text_color="Custom",
                        text_color=self.header_color, bold=True, valign="center")
        top.add_widget(back_btn)
        top.add_widget(title)
        self.add_widget(top)

        # Content
        content = ScrollView()
        box = BoxLayout(orientation='vertical', spacing=dp(12), padding=[dp(14), dp(4)], size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        box.add_widget(MDLabel(text="Select Theme", font_style="H6",
                               theme_text_color="Custom", text_color=self.header_color,
                               size_hint_y=None, height=dp(40)))
        for theme in ["amoled", "grey", "light"]:
            btn = MDRaisedButton(text=theme.upper(),
                                 md_bg_color=self.header_color[:3] + [0.2],
                                 theme_text_color="Custom", text_color=self.text_color)
            btn.bind(on_release=lambda x, t=theme: self.set_theme(t))
            box.add_widget(btn)
        content.add_widget(box)
        self.add_widget(content)

    def set_theme(self, theme):
        global _current_theme
        _current_theme = theme
        apply_app_theme(theme)

    def go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

class NumeralScreen(ConverterScreen):
    _from_base = "dec"
    _to_base   = "all"
    BASE_NAMES = {
        "dec": "DECIMAL", "bin": "BINARY",
        "hex": "HEXADECIMAL", "oct": "OCTAL", "txt": "TEXT / ASCII",
    }
    CHIP_IDS = {
        "dec": "chip_dec", "bin": "chip_bin", "hex": "chip_hex",
        "oct": "chip_oct", "txt": "chip_txt",
    }
    ROW_IDS = {
        "dec": "row_dec", "bin": "row_bin", "hex": "row_hex",
        "oct": "row_oct", "txt": "row_txt",
    }
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
        self.ids.input_field.text = ""
    def select_base(self, base):
        for b, cid in self.CHIP_IDS.items():
            self.ids[cid].is_active = (b == base)
        self._from_base = base
        self._to_base   = "all"
        self.ids.from_label.text = f"From: {self.BASE_NAMES[base]}"
        self.ids.to_label.text   = "To: ALL"
        self._update_hints(base)
        self.do_convert(self.ids.input_field.text)
    def _update_hints(self, base):
        hints = {
            "dec": "Enter decimal number...",
            "bin": "e.g. 1010  or  0b1010",
            "hex": "e.g. 1F  or  0x1F",
            "oct": "e.g. 17  or  0o17",
            "txt": "Type any text (ASCII)...",
        }
        tips = {
            "dec": "💡 Tap any chip to set it as input",
            "bin": "💡 Tap any chip to set it as input",
            "hex": "💡 Hex letters A–F are case-insensitive",
            "oct": "💡 Tap any chip to set it as input",
            "txt": "💡 Each character is shown as its ASCII code point",
        }
        self.ids.input_field.hint_text = hints.get(base, "Enter value...")
        self.ids.tip_label.text        = tips.get(base, "")
    def paste_input(self):
        text = Clipboard.paste()
        if text:
            self.ids.input_field.text = text.strip()
        else:
            _snack("Clipboard is empty")
    def copy_output(self):
        val = self.ids.output_field.text
        if val and val not in ("—", "error", "invalid input", ""):
            Clipboard.copy(val)
            _snack(f"Copied: {val[:36]}{'…' if len(val) > 36 else ''}")
        else:
            _snack("Nothing to copy")
    def swap_conversion(self):
        order = ["dec", "bin", "hex", "oct", "txt"]
        if self._to_base == "all":
            self._to_base = order[(order.index(self._from_base) + 1) % len(order)]
        else:
            self._from_base, self._to_base = self._to_base, self._from_base
        for b, cid in self.CHIP_IDS.items():
            self.ids[cid].is_active = (b == self._from_base)
        self.ids.from_label.text = f"From: {self.BASE_NAMES[self._from_base]}"
        self.ids.to_label.text = (
            "To: ALL" if self._to_base == "all"
            else f"To: {self.BASE_NAMES[self._to_base]}"
        )
        self._update_hints(self._from_base)
        out = self.ids.output_field.text
        self.ids.input_field.text = (
            out if out not in ("", "—", "error", "invalid input") else ""
        )
        self.do_convert(self.ids.input_field.text)
    def do_convert(self, raw):
        raw = raw.strip()
        if not raw:
            self.ids.output_field.text = ""
            self._set_all_rows("—")
            return
        try:
            if self._from_base == "txt":
                pts = [ord(c) for c in raw]
                self.ids.row_dec.set_value(" ".join(str(c)             for c in pts))
                self.ids.row_bin.set_value(" ".join(bin(c)[2:]          for c in pts))
                self.ids.row_hex.set_value(" ".join(hex(c)[2:].upper()  for c in pts))
                self.ids.row_oct.set_value(" ".join(oct(c)[2:]          for c in pts))
                self.ids.row_txt.set_value(raw)
                self.ids.output_field.text = "DEC: " + " ".join(str(c) for c in pts)
            else:
                n = self._parse(raw, self._from_base)
                self.ids.row_dec.set_value(str(n))
                self.ids.row_bin.set_value(bin(n)[2:])
                self.ids.row_hex.set_value(hex(n)[2:].upper())
                self.ids.row_oct.set_value(oct(n)[2:])
                self.ids.row_txt.set_value(self._to_char(n))
                if self._to_base == "all":
                    parts = []
                    if self._from_base != "dec": parts.append(f"DEC:{n}")
                    if self._from_base != "bin": parts.append(f"BIN:{bin(n)[2:]}")
                    if self._from_base != "hex": parts.append(f"HEX:{hex(n)[2:].upper()}")
                    if self._from_base != "oct": parts.append(f"OCT:{oct(n)[2:]}")
                    ch = self._to_char(n)
                    if ch:                        parts.append(f"TXT:{ch}")
                    self.ids.output_field.text = "  ".join(parts)
                elif self._to_base == "txt":
                    self.ids.output_field.text = self._to_char(n)
                else:
                    self.ids.output_field.text = self._format(n, self._to_base)
        except Exception:
            self.ids.output_field.text = "invalid input"
            self._set_all_rows("error")
    def _parse(self, s, base):
        s = s.strip().lower().replace("0x","").replace("0b","").replace("0o","")
        return int(s, {"dec":10,"bin":2,"hex":16,"oct":8}[base])
    def _format(self, n, base):
        return {"dec":str(n),"bin":bin(n)[2:],"hex":hex(n)[2:].upper(),"oct":oct(n)[2:]}[base]
    def _to_char(self, n):
        try:
            ch = chr(n)
            return ch if ch.isprintable() else f"<{n}>"
        except Exception:
            return "—"
    def _set_all_rows(self, val):
        for rid in self.ROW_IDS.values():
            self.ids[rid].set_value(val)

class GenericUnitScreen(ConverterScreen):
    UNITS       = []
    ACCENT      = ListProperty([0.0, 0.85, 0.72, 1])
    TITLE       = "Converter"
    FMT         = ":.6g"
    _from_unit  = None
    screen_title = StringProperty("")
    accent       = ListProperty([0.0, 0.85, 0.72, 1])

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self.screen_title = self.TITLE
        self.accent = self.ACCENT
        self._from_unit = self.UNITS[0][0]
        self._build_chips()
        self._build_rows()

    def _build_chips(self):
        container = self.ids.from_chips
        container.clear_widgets()
        self._chips = {}
        for label, _ in self.UNITS:
            chip = UnitChip(chip_text=label, accent=self.ACCENT)
            chip.is_active = (label == self._from_unit)
            chip.bind(on_release=lambda c, l=label: self._select_unit(l))
            container.add_widget(chip)
            self._chips[label] = chip

    def _build_rows(self):
        container = self.ids.results_col
        container.clear_widgets()
        self._rows = {}
        colors = [
            [0.0, 0.85, 0.72, 1], [1.0, 0.75, 0.2, 1], [0.55, 0.55, 1.0, 1],
            [1.0, 0.45, 0.45, 1], [0.3, 0.75, 1.0, 1], [0.8, 0.4, 1.0, 1],
            [1.0, 0.6, 0.2, 1],   [0.4, 1.0, 0.6, 1],  [1.0, 0.6, 0.9, 1],
            [0.6, 0.5, 1.0, 1],   [0.9, 0.85, 0.2, 1], [0.2, 0.85, 0.85, 1],
        ]
        for i, (label, _) in enumerate(self.UNITS):
            row = BaseRow(
                base_label=label,
                base_color=colors[i % len(colors)],
                text_color=self.text_color,
            )
            container.add_widget(row)
            self._rows[label] = row

    def _select_unit(self, label):
        self._from_unit = label
        for l, chip in self._chips.items():
            chip.is_active = (l == label)
        self.do_convert(self.ids.input_field.text)

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
        self.ids.input_field.text = ""

    def paste_input(self):
        text = Clipboard.paste()
        if text:
            self.ids.input_field.text = text.strip()
        else:
            _snack("Clipboard is empty")

    def do_convert(self, raw):
        raw = (raw or "").strip()
        if not raw:
            for row in self._rows.values():
                row.set_value("—")
            return
        try:
            val = float(raw)
        except ValueError:
            for row in self._rows.values():
                row.set_value("error")
            return

        def fmt(num):
            if isinstance(num, float):
                s = f"{num:.12f}"
                s = s.rstrip('0').rstrip('.') if '.' in s else s
                return s
            return str(num)

        for label, _ in self.UNITS:
            if label == self._from_unit:
                self._rows[label].set_value(fmt(val))
            else:
                try:
                    result = self._convert(val, self._from_unit, label)
                    self._rows[label].set_value(fmt(result))
                except Exception:
                    self._rows[label].set_value("error")

    def _convert(self, val, from_u, to_u):
        factors = {label: f for label, f in self.UNITS}
        return val * factors[from_u] / factors[to_u]

# --- All unit screens unchanged from converter_app_v9-1, inheriting GenericUnitScreen ---
class LengthScreen(GenericUnitScreen):
    TITLE  = "Length & Distance"
    ACCENT = [0.4, 0.6, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("m",   1.0), ("km",  1000.0), ("cm",  0.01), ("mm",  0.001),
        ("µm",  1e-6), ("nm",  1e-9), ("mi",  1609.344), ("yd",  0.9144),
        ("ft",  0.3048), ("in",  0.0254), ("nmi", 1852.0), ("ly",  9.4607e15),
        ("AU",  1.496e11),
    ]
class WeightScreen(GenericUnitScreen):
    TITLE  = "Weight & Mass"
    ACCENT = [1.0, 0.6, 0.2, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("kg",  1.0), ("g",   0.001), ("mg",  1e-6), ("µg",  1e-9),
        ("t",   1000.0), ("lb",  0.45359237), ("oz",  0.028349523125),
        ("st",  6.35029318), ("ct",  0.0002), ("gr",  6.479891e-5),
    ]
class TemperatureScreen(GenericUnitScreen):
    TITLE  = "Temperature"
    ACCENT = [1.0, 0.35, 0.35, 1]
    FMT    = ":.4f"
    UNITS  = [
        ("°C", 1), ("°F", 1), ("K", 1), ("°R", 1), ("°De", 1), ("°N", 1),
        ("°Ré", 1), ("°Rø", 1),
    ]
    def _convert(self, val, from_u, to_u):
        if   from_u == "°C":  c = val
        elif from_u == "°F":  c = (val - 32) * 5/9
        elif from_u == "K":   c = val - 273.15
        elif from_u == "°R":  c = (val - 491.67) * 5/9
        elif from_u == "°De": c = 100 - val * 2/3
        elif from_u == "°N":  c = val * 100/33
        elif from_u == "°Ré": c = val * 5/4
        elif from_u == "°Rø": c = (val - 7.5) * 40/21
        else: c = val
        if   to_u == "°C":  return c
        elif to_u == "°F":  return c * 9/5 + 32
        elif to_u == "K":   return c + 273.15
        elif to_u == "°R":  return (c + 273.15) * 9/5
        elif to_u == "°De": return (100 - c) * 3/2
        elif to_u == "°N":  return c * 33/100
        elif to_u == "°Ré": return c * 4/5
        elif to_u == "°Rø": return c * 21/40 + 7.5
        return c
class DataStorageScreen(GenericUnitScreen):
    TITLE  = "Data Storage"
    ACCENT = [0.8, 0.4, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("B",    1.0), ("KB",   1e3), ("MB",   1e6), ("GB",   1e9),
        ("TB",   1e12), ("PB",   1e15), ("EB",   1e18), ("KiB",  1024.0),
        ("MiB",  1024**2), ("GiB",  1024**3), ("TiB",  1024**4), ("PiB",  1024**5),
        ("bit",  0.125), ("Kbit", 125.0), ("Mbit", 125000.0), ("Gbit", 125000000.0),
    ]
class SpeedScreen(GenericUnitScreen):
    TITLE  = "Speed"
    ACCENT = [0.2, 0.85, 0.4, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("m/s",   1.0), ("km/h",  1/3.6), ("mph",   0.44704), ("ft/s",  0.3048),
        ("knot",  0.514444), ("mach",  343.0), ("c",     299792458.0),
    ]
class AreaScreen(GenericUnitScreen):
    TITLE  = "Area"
    ACCENT = [1.0, 0.75, 0.2, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("m²",   1.0), ("km²",  1e6), ("cm²",  1e-4), ("mm²",  1e-6),
        ("ha",   1e4), ("ac",   4046.856), ("ft²",  0.092903), ("in²",  6.4516e-4),
        ("yd²",  0.836127), ("mi²",  2589988.110),
    ]
class VolumeScreen(GenericUnitScreen):
    TITLE  = "Volume"
    ACCENT = [0.3, 0.75, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("L",       1.0), ("mL",      0.001), ("m³",      1000.0), ("cm³",     0.001),
        ("ft³",     28.316847), ("in³",     0.016387064), ("gal US",  3.785411784),
        ("gal UK",  4.54609), ("qt",      0.946353), ("pt",      0.473176),
        ("cup",     0.236588), ("fl oz",   0.0295735), ("tbsp",    0.0147868),
        ("tsp",     0.00492892), ("bbl",     158.987),
    ]
class TimeScreen(GenericUnitScreen):
    TITLE  = "Time"
    ACCENT = [0.6, 0.5, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("s",    1.0), ("ns",   1e-9), ("µs",   1e-6), ("ms",   0.001),
        ("min",  60.0), ("h",    3600.0), ("day",  86400.0), ("wk",   604800.0),
        ("mo",   2629800.0), ("yr",   31557600.0), ("dec",  315576000.0),
        ("cent", 3155760000.0),
    ]
class PressureScreen(GenericUnitScreen):
    TITLE  = "Pressure"
    ACCENT = [1.0, 0.45, 0.7, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("Pa",    1.0), ("kPa",   1e3), ("MPa",   1e6), ("GPa",   1e9),
        ("bar",   1e5), ("mbar",  100.0), ("psi",   6894.757), ("atm",   101325.0),
        ("mmHg",  133.322), ("inHg",  3386.39), ("cmH₂O", 98.0665), ("torr",  133.322),
    ]
class EnergyScreen(GenericUnitScreen):
    TITLE  = "Energy"
    ACCENT = [1.0, 0.8, 0.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("J",    1.0), ("kJ",   1e3), ("MJ",   1e6), ("GJ",   1e9),
        ("cal",  4.184), ("kcal", 4184.0), ("Wh",   3600.0), ("kWh",  3600000.0),
        ("MWh",  3.6e9), ("BTU",  1055.05585), ("eV",   1.602176634e-19),
        ("erg",  1e-7), ("ft·lb", 1.35582),
    ]
class PowerScreen(GenericUnitScreen):
    TITLE  = "Power"
    ACCENT = [0.0, 0.9, 0.6, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("W",      1.0), ("kW",     1000.0), ("MW",     1e6), ("GW",     1e9),
        ("hp",     745.69987), ("hp(m)",  735.49875), ("BTU/h",  0.29307107),
        ("BTU/s",  1055.05585), ("cal/s",  4.184), ("kcal/h", 1.163),
        ("ft·lb/s",1.35582), ("erg/s",  1e-7),
    ]
class AngleScreen(GenericUnitScreen):
    TITLE  = "Angle"
    ACCENT = [0.9, 0.5, 0.2, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("°",      1.0), ("rad",    180.0 / math.pi), ("grad",   0.9),
        ("arcmin", 1/60), ("arcsec", 1/3600), ("rev",    360.0),
        ("mrad",   180.0 / (math.pi * 1000)),
    ]
class FrequencyScreen(GenericUnitScreen):
    TITLE  = "Frequency"
    ACCENT = [0.5, 0.85, 0.5, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("Hz",   1.0), ("kHz",  1e3), ("MHz",  1e6), ("GHz",  1e9),
        ("THz",  1e12), ("rpm",  1/60), ("rad/s", 1/(2*math.pi)), ("mHz",  0.001),
    ]
class FuelScreen(GenericUnitScreen):
    TITLE  = "Fuel Economy"
    ACCENT = [0.85, 0.4, 0.4, 1]
    FMT    = ":.4f"
    UNITS  = [
        ("km/L",      1), ("L/100km",   1), ("mpg US",    1),
        ("mpg UK",    1), ("mi/L",      1), ("km/gal US", 1),
    ]
    def _convert(self, val, from_u, to_u):
        if   from_u == "km/L":      kml = val
        elif from_u == "L/100km":   kml = 100.0 / val if val else 0
        elif from_u == "mpg US":    kml = val * 0.425144
        elif from_u == "mpg UK":    kml = val * 0.354006
        elif from_u == "mi/L":      kml = val * 1.60934
        elif from_u == "km/gal US": kml = val / 3.78541
        else: kml = val
        if   to_u == "km/L":      return kml
        elif to_u == "L/100km":   return 100.0 / kml if kml else 0
        elif to_u == "mpg US":    return kml / 0.425144
        elif to_u == "mpg UK":    return kml / 0.354006
        elif to_u == "mi/L":      return kml / 1.60934
        elif to_u == "km/gal US": return kml * 3.78541
        return kml

# NEW MODULES
class AccelerationScreen(GenericUnitScreen):
    TITLE  = "Acceleration"
    ACCENT = [0.6, 0.4, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("m/s²", 1.0),
        ("ft/s²", 0.3048),
        ("g", 9.80665),
        ("Gal", 0.01),
        ("in/s²", 0.0254),
    ]

class TorqueScreen(GenericUnitScreen):
    TITLE  = "Torque"
    ACCENT = [1.0, 0.55, 0.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("Nm", 1.0),
        ("lb·ft", 1.35582),
        ("kg·m", 9.80665),
        ("oz·in", 0.00706155),
    ]

CURRENCIES = [
    ("USD", "🇺🇸"), ("EUR", "🇪🇺"), ("GBP", "🇬🇧"), ("JPY", "🇯🇵"),
    ("CNY", "🇨🇳"), ("INR", "🇮🇳"), ("CAD", "🇨🇦"), ("AUD", "🇦🇺"),
    ("CHF", "🇨🇭"), ("BRL", "🇧🇷"), ("MXN", "🇲🇽"), ("SGD", "🇸🇬"),
    ("HKD", "🇭🇰"), ("NOK", "🇳🇴"), ("SEK", "🇸🇪"), ("DKK", "🇩🇰"),
    ("NZD", "🇳🇿"), ("ZAR", "🇿🇦"), ("RUB", "🇷🇺"), ("TRY", "🇹🇷"),
    ("KRW", "🇰🇷"), ("IDR", "🇮🇩"), ("SAR", "🇸🇦"), ("AED", "🇦🇪"),
    ("PLN", "🇵🇱"), ("THB", "🇹🇭"), ("MYR", "🇲🇾"), ("PHP", "🇵🇭"),
    ("EGP", "🇪🇬"), ("PKR", "🇵🇰"), ("LKR", "🇱🇰"),
]

class CurrencyScreen(ConverterScreen):
    _from_currency = "USD"
    _rates         = {}
    _fetched       = False
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"
    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_chips()
        self._build_rows()
    def _build_chips(self):
        container = self.ids.from_chips
        container.clear_widgets()
        self._chips = {}
        for code, flag in CURRENCIES:
            label = f"{flag} {code}"
            chip = UnitChip(chip_text=label, accent=[0.3, 0.85, 0.55, 1])
            chip.is_active = (code == self._from_currency)
            chip.bind(on_release=lambda c, co=code: self._select(co))
            container.add_widget(chip)
            self._chips[code] = chip
    def _build_rows(self):
        container = self.ids.results_col
        container.clear_widgets()
        self._rows = {}
        colors = [
            [0.0, 0.85, 0.72, 1], [1.0, 0.75, 0.2, 1], [0.55, 0.55, 1.0, 1],
            [1.0, 0.45, 0.45, 1], [0.3, 0.75, 1.0, 1], [0.8, 0.4, 1.0, 1],
            [1.0, 0.6, 0.2, 1],   [0.4, 1.0, 0.6, 1],  [1.0, 0.6, 0.9, 1],
            [0.6, 0.5, 1.0, 1],
        ]
        for i, (code, flag) in enumerate(CURRENCIES):
            row = BaseRow(
                base_label=code,
                base_color=colors[i % len(colors)],
                text_color=self.text_color,
            )
            container.add_widget(row)
            self._rows[code] = row
    def _select(self, code):
        self._from_currency = code
        for c, chip in self._chips.items():
            chip.is_active = (c == code)
        self.do_convert()
    def paste_input(self):
        text = Clipboard.paste()
        if text:
            self.ids.amount_field.text = text.strip()
        else:
            _snack("Clipboard is empty")
    def fetch_rates(self):
        self.ids.rate_status.text = "⏳ Fetching live rates…"
        url = "https://open.er-api.com/v6/latest/USD"
        UrlRequest(url, on_success=self._on_rates,
                   on_failure=self._on_fail, on_error=self._on_fail)
    def _on_rates(self, req, result):
        rates = result.get("rates", {})
        if rates:
            self._rates = rates
            self._fetched = True
            self.ids.rate_status.text = "✅ Live rates loaded"
            self.do_convert()
        else:
            self._on_fail(req, result)
    def _on_fail(self, *_):
        self.ids.rate_status.text = "⚠️ Could not fetch rates — using offline fallback"
        self._rates = {
            "USD":1,"EUR":0.92,"GBP":0.79,"JPY":149.5,"CNY":7.24,"INR":83.1,
            "CAD":1.36,"AUD":1.53,"CHF":0.9,"BRL":4.97,"MXN":17.15,"SGD":1.34,
            "HKD":7.82,"NOK":10.6,"SEK":10.4,"DKK":6.89,"NZD":1.63,"ZAR":18.9,
            "RUB":91.5,"TRY":32.3,"KRW":1330,"IDR":15700,"SAR":3.75,"AED":3.67,
            "PLN":4.03,"THB":35.1,"MYR":4.72,"PHP":56.3,"EGP":30.9,"PKR":278,
            "LKR":365.0,
        }
        self._fetched = True
        self.do_convert()
    def do_convert(self):
        raw = self.ids.amount_field.text.strip()
        if not raw:
            for row in self._rows.values():
                row.set_value("—")
            return
        if not self._fetched:
            _snack("Tap ↻ to load live rates first")
            return
        try:
            amount = float(raw)
        except ValueError:
            for row in self._rows.values():
                row.set_value("error")
            return
        from_rate = self._rates.get(self._from_currency, 1.0)
        usd_val   = amount / from_rate
        for code, _ in CURRENCIES:
            to_rate = self._rates.get(code, 1.0)
            converted = usd_val * to_rate
            if code == self._from_currency:
                self._rows[code].set_value("{:,.4f}".format(amount))
            else:
                self._rows[code].set_value("{:,.4f}".format(converted))

# ── Screen map ──
SCREEN_MAP = [
    ("home",        HomeScreen),
    ("settings",    SettingsScreen),
    ("numeral",     NumeralScreen),
    ("length",      LengthScreen),
    ("weight",      WeightScreen),
    ("temperature", TemperatureScreen),
    ("datastorage", DataStorageScreen),
    ("speed",       SpeedScreen),
    ("area",        AreaScreen),
    ("volume",      VolumeScreen),
    ("time",        TimeScreen),
    ("pressure",    PressureScreen),
    ("energy",      EnergyScreen),
    ("power",       PowerScreen),
    ("angle",       AngleScreen),
    ("frequency",   FrequencyScreen),
    ("fuel",        FuelScreen),
    ("currency",    CurrencyScreen),
    ("acceleration", AccelerationScreen),
    ("torque",       TorqueScreen),
]

if __name__ == "__main__":
    SHVLicenseGateApp().run()