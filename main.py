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


from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
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
from kivy.uix.widget import Widget
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


from kivy.uix.widget import Widget as _KivyWidget

class _SpinnerWidget(_KivyWidget):
    """Pure-Kivy rotating arc spinner — no KivyMD dependency."""
    def __init__(self, size_dp=56, color=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        sz = dp(size_dp)
        self.size = (sz, sz)
        self._angle = 0.0
        self._spin_color = color or [0.12, 0.42, 0.92, 1]
        self._arc_instr = None
        self._color_instr = None
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(self._build_canvas, 0)

    def _build_canvas(self, *_):
        from kivy.graphics import Color, Line
        with self.canvas:
            self._color_instr = Color(*self._spin_color)
            self._arc_instr = Line(
                circle=(self.center_x, self.center_y,
                        self.width * 0.44,
                        self._angle, self._angle + 300),
                width=dp(3.5),
                cap='round',
            )

    def _redraw(self, *_):
        if self._arc_instr is None:
            return
        self._arc_instr.circle = (
            self.center_x, self.center_y,
            self.width * 0.44,
            self._angle, self._angle + 300,
        )

    def tick(self, dt):
        self._angle = (self._angle + 20) % 360
        if self._arc_instr:
            self._arc_instr.circle = (
                self.center_x, self.center_y,
                self.width * 0.44,
                self._angle, self._angle + 300,
            )


class LoadingScreen(Screen):
    """
    Professional splash screen with three layers:
      1. Canvas-based pulsing glow ring  — driven by kivy.animation.Animation,
         interpolated at render time, survives Python GIL stalls.
      2. Determinate progress bar        — advances with each screen batch so
         the user sees real progress, not a fake spinning lie.
      3. Lazy-screen status text         — "Building X of N…"
    """
    def __init__(self, total_screens=1, **kwargs):
        super().__init__(**kwargs)
        self._total   = max(total_screens, 1)
        self._done    = 0
        self._anim    = None
        self._pulse_w = None   # widget whose width drives the glow pulse
        self._bar_w   = None   # inner progress rectangle width ref

        accent  = get_color_from_hex(_C['accent'])   # teal/blue
        accent2 = [0.0, 0.85, 0.72, 1]               # green-teal

        from kivy.graphics import (Color, Rectangle, RoundedRectangle,
                                    Line, Ellipse)
        from kivy.animation import Animation

        root = BoxLayout(orientation='vertical')

        # ── solid black background ──
        with root.canvas.before:
            Color(0, 0, 0, 1)
            _bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w, v: setattr(_bg, 'pos', v),
                  size=lambda w, v: setattr(_bg, 'size', v))

        root.add_widget(Widget())   # top flex spacer

        # ── centre logo block ──
        logo_block = BoxLayout(orientation='vertical',
                               size_hint_y=None, height=dp(220),
                               spacing=dp(0))

        # Pulsing ring — implemented as a Widget with a canvas arc
        ring_size = dp(110)
        ring_wrap = BoxLayout(size_hint_y=None, height=ring_size)
        ring_wrap.add_widget(Widget())   # left spacer

        self._ring_widget = Widget(size_hint=(None, None),
                                   size=(ring_size, ring_size))

        with self._ring_widget.canvas:
            # Outer glow ring (static, faint)
            Color(*accent2[:3], 0.08)
            Ellipse(pos=self._ring_widget.pos, size=self._ring_widget.size)
            # Mid ring
            Color(*accent2[:3], 0.15)
            Line(circle=(ring_size/2, ring_size/2, ring_size*0.44),
                 width=dp(2))
            # Animated arc
            self._arc_color = Color(*accent2[:3], 1.0)
            self._arc = Line(
                circle=(ring_size/2, ring_size/2,
                        ring_size * 0.44, 0, 300),
                width=dp(4), cap='round',
            )

        self._ring_widget.bind(pos=self._update_ring,
                               size=self._update_ring)
        ring_wrap.add_widget(self._ring_widget)
        ring_wrap.add_widget(Widget())   # right spacer
        logo_block.add_widget(ring_wrap)

        # App name
        app_lbl = Label(
            text="Universal Convertor",
            font_size=dp(24), bold=True,
            color=[1, 1, 1, 1],
            halign='center', valign='middle',
            size_hint_y=None, height=dp(38),
        )
        app_lbl.bind(size=app_lbl.setter('text_size'))
        logo_block.add_widget(app_lbl)

        # Tagline
        tag_lbl = Label(
            text="by SH Vertex",
            font_size=dp(13),
            color=list(accent2[:3]) + [0.8],
            halign='center', valign='middle',
            size_hint_y=None, height=dp(22),
        )
        tag_lbl.bind(size=tag_lbl.setter('text_size'))
        logo_block.add_widget(tag_lbl)

        logo_block.add_widget(Widget(size_hint_y=None, height=dp(22)))

        # ── Progress bar ──
        bar_outer_h = dp(6)
        bar_outer = Widget(size_hint_y=None, height=bar_outer_h,
                           size_hint_x=None, width=dp(220))
        with bar_outer.canvas:
            Color(0.12, 0.12, 0.12, 1)
            self._bar_bg_rr = RoundedRectangle(
                pos=bar_outer.pos, size=bar_outer.size, radius=[3])
            Color(*accent2[:3], 1.0)
            self._bar_fg_rr = RoundedRectangle(
                pos=bar_outer.pos,
                size=(dp(4), bar_outer_h),
                radius=[3])
        bar_outer.bind(pos=self._update_bar_pos,
                       size=self._update_bar_bg)

        bar_wrap = BoxLayout(size_hint_y=None, height=bar_outer_h)
        bar_wrap.add_widget(Widget())
        bar_wrap.add_widget(bar_outer)
        bar_wrap.add_widget(Widget())
        logo_block.add_widget(bar_wrap)

        self._bar_outer_ref = bar_outer

        logo_block.add_widget(Widget(size_hint_y=None, height=dp(14)))

        # Status text
        self._status_lbl = Label(
            text="Initialising…",
            font_size=dp(13),
            color=get_color_from_hex(_C['subtext']),
            halign='center', valign='middle',
            size_hint_y=None, height=dp(24),
        )
        self._status_lbl.bind(size=self._status_lbl.setter('text_size'))
        logo_block.add_widget(self._status_lbl)

        root.add_widget(logo_block)
        root.add_widget(Widget())   # bottom flex spacer

        # Version / footer
        ver_lbl = Label(
            text="v7.0  •  45 modules",
            font_size=dp(11),
            color=[0.22, 0.22, 0.22, 1],
            halign='center', valign='middle',
            size_hint_y=None, height=dp(28),
        )
        ver_lbl.bind(size=ver_lbl.setter('text_size'))
        root.add_widget(ver_lbl)

        self.add_widget(root)
        self._arc_angle  = 0.0
        self._arc_event  = None

    # ── Canvas helpers ─────────────────────────────────────────────
    def _update_ring(self, w, *_):
        cx = w.center_x; cy = w.center_y; r = w.width * 0.44
        self._arc.circle = (cx, cy, r, self._arc_angle,
                            self._arc_angle + 300)

    def _update_bar_pos(self, w, pos):
        self._bar_bg_rr.pos = pos
        self._bar_fg_rr.pos = pos

    def _update_bar_bg(self, w, size):
        self._bar_bg_rr.size = size
        self._refresh_bar()

    def _refresh_bar(self):
        if not self._bar_outer_ref:
            return
        frac  = min(self._done / self._total, 1.0)
        total_w = self._bar_outer_ref.width or dp(220)
        filled  = max(dp(4), total_w * frac)
        h = self._bar_outer_ref.height or dp(6)
        self._bar_fg_rr.pos  = self._bar_outer_ref.pos
        self._bar_fg_rr.size = (filled, h)

    # ── Lifecycle ──────────────────────────────────────────────────
    def on_enter(self, *args):
        self._arc_event = Clock.schedule_interval(self._tick_arc, 1/24)

    def on_leave(self, *args):
        if self._arc_event:
            self._arc_event.cancel()
            self._arc_event = None

    def _tick_arc(self, dt):
        self._arc_angle = (self._arc_angle + 18) % 360
        w = self._ring_widget
        cx = w.center_x; cy = w.center_y; r = w.width * 0.44
        self._arc.circle = (cx, cy, r, self._arc_angle,
                            self._arc_angle + 300)

    # ── Public API: called by _build_batch ──────────────────────────
    def set_progress(self, done, total, screen_name=''):
        self._done  = done
        self._total = total
        pct = int(done / total * 100) if total else 0
        friendly = screen_name.replace('_', ' ').title()
        self._status_lbl.text = (
            f"Loading  {done}/{total}  ({pct}%)   {friendly}"
            if screen_name else f"Loading  {done}/{total}  ({pct}%)"
        )
        Clock.schedule_once(lambda dt: self._refresh_bar(), 0)



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
        # Build only HomeScreen now — every other screen is built on first
        # navigation to it (see HomeScreen.go).  This makes the transition
        # from the licence gate instant with zero waiting.
        home_name, home_cls = SCREEN_MAP[0]
        if not self.manager.has_screen(home_name):
            self.manager.add_widget(home_cls(name=home_name))
        apply_app_theme(_current_theme)
        self.manager.current = home_name


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
<CompactTile>:
    size_hint: 1, None
    height: dp(82)
    canvas.before:
        Color:
            rgba: root.card_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12]*4
    BoxLayout:
        orientation: "vertical"
        padding: [dp(8), dp(8), dp(8), dp(6)]
        spacing: dp(4)
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            spacing: dp(6)
            RoundBox:
                bg_color: root.accent[0]*0.18, root.accent[1]*0.18, root.accent[2]*0.18, 1
                box_radius: [8]*4
                size_hint: None, None
                size: dp(30), dp(30)
                pos_hint: {"center_y": .5}
                MDIcon:
                    icon: root.mod_icon
                    theme_text_color: "Custom"
                    text_color: root.accent
                    halign: "center"
                    font_size: dp(17)
            MDLabel:
                text: root.title
                font_style: "Body2"
                theme_text_color: "Custom"
                text_color: root.card_title_color
                bold: True
                valign: "center"
                shorten: False
                text_size: self.width, None
        MDLabel:
            text: root.subtitle
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: root.card_subtitle_color
            shorten: True
            shorten_from: "right"
            font_size: dp(11)
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
            height: dp(56)
            padding: [dp(16), dp(10), dp(8), dp(10)]
            MDLabel:
                text: "Universal Convertor"
                font_style: "H6"
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
        # ── Search bar ──
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            padding: [dp(10), dp(4), dp(10), dp(4)]
            MDTextField:
                id: search_field
                hint_text: "Search modules..."
                mode: "rectangle"
                line_color_focus: root.header_color
                line_color_normal: 0.18, 0.18, 0.18, 1
                text_color_normal: root.text_color
                text_color_focus: root.text_color
                hint_text_color_normal: root.subtitle_color
                fill_color_normal: 0.08, 0.08, 0.08, 1
                fill_color_focus: 0.10, 0.10, 0.10, 1
                font_size: dp(14)
                on_text: root.on_search(self.text)
        ScrollView:
            id: main_scroll
            BoxLayout:
                orientation: "vertical"
                padding: [dp(8), dp(4)]
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height

                # ── RECENTS ───────────────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(22)
                    padding: [dp(4), 0]
                    MDLabel:
                        text: "RECENTLY USED"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: root.subtitle_color
                        bold: True
                        valign: "center"
                ScrollView:
                    size_hint_y: None
                    height: dp(40)
                    do_scroll_x: True
                    do_scroll_y: False
                    bar_width: 0
                    BoxLayout:
                        id: recents_bar
                        size_hint_x: None
                        width: self.minimum_width
                        spacing: dp(6)
                        padding: [dp(2), dp(2)]

                # ── SEARCH RESULTS (shown when typing) ────────
                BoxLayout:
                    id: modules_grid
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(4)
                    padding: [0, dp(2)]

                # ── EVERYDAY ──────────────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 0.0, 0.85, 0.72, 0.12
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "view-grid-outline"
                        theme_text_color: "Custom"
                        text_color: 0.0, 0.85, 0.72, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "EVERYDAY"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 0.0, 0.85, 0.72, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "ruler"
                        title: "Length"
                        subtitle: "km · mi · ft · in"
                        accent: 0.4, 0.6, 1.0, 1
                        on_release: root.go("length")
                    CompactTile:
                        mod_icon: "weight"
                        title: "Weight"
                        subtitle: "kg · lb · oz · g"
                        accent: 1.0, 0.6, 0.2, 1
                        on_release: root.go("weight")
                    CompactTile:
                        mod_icon: "thermometer"
                        title: "Temp"
                        subtitle: "°C · °F · K"
                        accent: 1.0, 0.35, 0.35, 1
                        on_release: root.go("temperature")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "cup"
                        title: "Volume"
                        subtitle: "L · mL · gal"
                        accent: 0.3, 0.75, 1.0, 1
                        on_release: root.go("volume")
                    CompactTile:
                        mod_icon: "vector-square"
                        title: "Area"
                        subtitle: "m² · ft² · ha"
                        accent: 1.0, 0.75, 0.2, 1
                        on_release: root.go("area")
                    CompactTile:
                        mod_icon: "clock-outline"
                        title: "Time"
                        subtitle: "s · min · h · yr"
                        accent: 0.6, 0.5, 1.0, 1
                        on_release: root.go("time")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "speedometer"
                        title: "Speed"
                        subtitle: "km/h · mph"
                        accent: 0.2, 0.85, 0.4, 1
                        on_release: root.go("speed")
                    CompactTile:
                        mod_icon: "currency-usd"
                        title: "Currency"
                        subtitle: "USD · EUR · GBP"
                        accent: 0.3, 0.85, 0.55, 1
                        on_release: root.go("currency")
                    CompactTile:
                        mod_icon: "gas-station"
                        title: "Fuel"
                        subtitle: "km/L · L/100km"
                        accent: 0.85, 0.4, 0.4, 1
                        on_release: root.go("fuel")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "food"
                        title: "Cooking"
                        subtitle: "cup · tbsp · ml"
                        accent: 1.0, 0.55, 0.25, 1
                        on_release: root.go("cooking")
                    CompactTile:
                        mod_icon: "hanger"
                        title: "Clothing"
                        subtitle: "US · EU · UK · JP"
                        accent: 0.85, 0.4, 0.9, 1
                        on_release: root.go("clothing")
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)

                # ── SCIENCE & ENGINEERING ─────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 1.0, 0.8, 0.0, 0.10
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "flask-outline"
                        theme_text_color: "Custom"
                        text_color: 1.0, 0.82, 0.2, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "SCIENCE & ENGINEERING"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 1.0, 0.82, 0.2, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "gauge"
                        title: "Pressure"
                        subtitle: "Pa · bar · psi"
                        accent: 1.0, 0.45, 0.7, 1
                        on_release: root.go("pressure")
                    CompactTile:
                        mod_icon: "lightning-bolt"
                        title: "Energy"
                        subtitle: "J · cal · kWh"
                        accent: 1.0, 0.8, 0.0, 1
                        on_release: root.go("energy")
                    CompactTile:
                        mod_icon: "flash"
                        title: "Power"
                        subtitle: "W · kW · hp"
                        accent: 0.0, 0.9, 0.6, 1
                        on_release: root.go("power")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "engine"
                        title: "Torque"
                        subtitle: "Nm · lb·ft"
                        accent: 1.0, 0.55, 0.0, 1
                        on_release: root.go("torque")
                    CompactTile:
                        mod_icon: "car-brake-abs"
                        title: "Acceleration"
                        subtitle: "m/s² · g · Gal"
                        accent: 0.6, 0.4, 1.0, 1
                        on_release: root.go("acceleration")
                    CompactTile:
                        mod_icon: "arrow-expand-down"
                        title: "Force"
                        subtitle: "N · kN · lbf"
                        accent: 0.9, 0.35, 0.35, 1
                        on_release: root.go("force")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "dots-hexagon"
                        title: "Density"
                        subtitle: "kg/m³ · g/cm³"
                        accent: 0.4, 0.85, 0.55, 1
                        on_release: root.go("density")
                    CompactTile:
                        mod_icon: "waves"
                        title: "Flow Rate"
                        subtitle: "L/s · GPM"
                        accent: 0.3, 0.75, 1.0, 1
                        on_release: root.go("flowrate")
                    CompactTile:
                        mod_icon: "water"
                        title: "Viscosity"
                        subtitle: "Pa·s · cP"
                        accent: 0.5, 0.7, 1.0, 1
                        on_release: root.go("viscosity")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "rotate-right"
                        title: "Angle"
                        subtitle: "° · rad · grad"
                        accent: 0.9, 0.5, 0.2, 1
                        on_release: root.go("angle")
                    CompactTile:
                        mod_icon: "sine-wave"
                        title: "Frequency"
                        subtitle: "Hz · kHz · MHz"
                        accent: 0.5, 0.85, 0.5, 1
                        on_release: root.go("frequency")
                    CompactTile:
                        mod_icon: "radioactive"
                        title: "RadioActvty"
                        subtitle: "Bq · Ci · Sv"
                        accent: 0.6, 1.0, 0.3, 1
                        on_release: root.go("radioactivity")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "volume-high"
                        title: "Sound"
                        subtitle: "dB · dBm · dBW"
                        accent: 0.9, 0.6, 0.2, 1
                        on_release: root.go("sound")
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)

                # ── ELECTRONICS & DIGITAL ─────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 0.55, 0.55, 1.0, 0.12
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "chip"
                        theme_text_color: "Custom"
                        text_color: 0.7, 0.7, 1.0, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "ELECTRONICS & DIGITAL"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 0.7, 0.7, 1.0, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "flash"
                        title: "Electric"
                        subtitle: "V · A · Ω · kΩ"
                        accent: 0.55, 0.55, 1.0, 1
                        on_release: root.go("electric")
                    CompactTile:
                        mod_icon: "magnet"
                        title: "Magnetic"
                        subtitle: "T · mT · G · Oe"
                        accent: 1.0, 0.4, 0.7, 1
                        on_release: root.go("magnetic")
                    CompactTile:
                        mod_icon: "database"
                        title: "Data Storage"
                        subtitle: "B · KB · MB · GB"
                        accent: 0.8, 0.4, 1.0, 1
                        on_release: root.go("datastorage")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "format-font-size-increase"
                        title: "Typography"
                        subtitle: "px · pt · em · dp"
                        accent: 0.4, 0.9, 0.85, 1
                        on_release: root.go("typography")
                    CompactTile:
                        mod_icon: "palette"
                        title: "Color Codes"
                        subtitle: "HEX · RGB · HSL"
                        accent: 1.0, 0.5, 0.8, 1
                        on_release: root.go("color")
                    CompactTile:
                        mod_icon: "numeric"
                        title: "Numerals"
                        subtitle: "DEC · BIN · HEX"
                        accent: 0.0, 0.85, 0.72, 1
                        on_release: root.go("numeral")

                # ── LIGHT & OPTICS ────────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 1.0, 0.95, 0.4, 0.10
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "white-balance-sunny"
                        theme_text_color: "Custom"
                        text_color: 1.0, 0.95, 0.4, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "LIGHT & OPTICS"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 1.0, 0.95, 0.4, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "lightbulb-outline"
                        title: "Illuminance"
                        subtitle: "lux · fc · phot"
                        accent: 1.0, 0.92, 0.3, 1
                        on_release: root.go("illuminance")
                    CompactTile:
                        mod_icon: "white-balance-sunny"
                        title: "Luminance"
                        subtitle: "cd/m² · fL · nit"
                        accent: 1.0, 0.75, 0.2, 1
                        on_release: root.go("luminance")
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)

                # ── PRINTING & DESIGN ─────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 0.8, 0.4, 1.0, 0.10
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "printer-outline"
                        theme_text_color: "Custom"
                        text_color: 0.82, 0.5, 1.0, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "PRINTING & DESIGN"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 0.82, 0.5, 1.0, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "file-document-outline"
                        title: "Paper Sizes"
                        subtitle: "A4 · Letter · Legal"
                        accent: 0.8, 0.4, 1.0, 1
                        on_release: root.go("papersize")
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)
                    BoxLayout:
                        size_hint: 1, None
                        height: dp(82)

                # ── EVERYDAY TOOLS ─────────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(28)
                    padding: [dp(4), 0]
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 0.3, 0.85, 0.55, 0.12
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [6]*4
                    MDIcon:
                        icon: "tools"
                        theme_text_color: "Custom"
                        text_color: 0.3, 0.85, 0.55, 1
                        font_size: dp(14)
                        size_hint_x: None
                        width: dp(22)
                        halign: "center"
                        valign: "center"
                    MDLabel:
                        text: "EVERYDAY TOOLS"
                        font_style: "Overline"
                        theme_text_color: "Custom"
                        text_color: 0.3, 0.85, 0.55, 1
                        bold: True
                        valign: "center"
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "earth"
                        title: "Time Zones"
                        subtitle: "UTC · GMT · World"
                        accent: 0.3, 0.75, 1.0, 1
                        on_release: root.go("timezone")
                    CompactTile:
                        mod_icon: "calendar-range"
                        title: "Date & Age"
                        subtitle: "Days · Age · Diff"
                        accent: 0.8, 0.5, 1.0, 1
                        on_release: root.go("dateage")
                    CompactTile:
                        mod_icon: "percent"
                        title: "Tip Calc"
                        subtitle: "Bill · Tip · Split"
                        accent: 0.3, 0.85, 0.55, 1
                        on_release: root.go("tip")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "tag-outline"
                        title: "Discount %"
                        subtitle: "Sale · Off · Savings"
                        accent: 1.0, 0.55, 0.25, 1
                        on_release: root.go("discount")
                    CompactTile:
                        mod_icon: "heart-pulse"
                        title: "BMI / BMR"
                        subtitle: "Body · Health · Calc"
                        accent: 1.0, 0.35, 0.5, 1
                        on_release: root.go("bmibmr")
                    CompactTile:
                        mod_icon: "shoe-heel"
                        title: "Shoe Sizes"
                        subtitle: "US · UK · EU · JP"
                        accent: 0.55, 0.75, 1.0, 1
                        on_release: root.go("shoesize")
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "ring"
                        title: "Ring Sizes"
                        subtitle: "US · UK · EU · mm"
                        accent: 1.0, 0.78, 0.2, 1
                        on_release: root.go("ringsize")
                    CompactTile:
                        mod_icon: "water-percent"
                        title: "Blood Glucose"
                        subtitle: "mg/dL · mmol/L"
                        accent: 1.0, 0.4, 0.4, 1
                        on_release: root.go("bloodglucose")
                    CompactTile:
                        mod_icon: "car-tire-alert"
                        title: "Tire Sizes"
                        subtitle: "205/55R16 decoder"
                        accent: 0.6, 0.6, 0.6, 1
                        on_release: root.go("tiresize")

                # ── SCIENCE (extra) ──────────────────────────
                BoxLayout:
                    size_hint_y: None
                    height: dp(82)
                    spacing: dp(5)
                    CompactTile:
                        mod_icon: "flask"
                        title: "Concentration"
                        subtitle: "mol/L · ppm · ppb"
                        accent: 0.4, 0.9, 0.6, 1
                        on_release: root.go("concentration")
                    CompactTile:
                        mod_icon: "radioactive-circle"
                        title: "Rad Dose"
                        subtitle: "Sv · rem · Gy · rad"
                        accent: 0.6, 1.0, 0.3, 1
                        on_release: root.go("raddose")
                    CompactTile:
                        mod_icon: "weather-rainy"
                        title: "Humidity"
                        subtitle: "RH · dew · abs"
                        accent: 0.3, 0.75, 1.0, 1
                        on_release: root.go("humidity")

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
                    BaseChip:
                        id: chip_rom
                        chip_text: "ROM"
                        accent: 1.0, 0.78, 0.2, 1
                        on_release: root.select_base("rom")
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
                    height: dp(258)
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
                        BaseRow:
                            id: row_rom
                            base_label: "ROM"
                            base_color: 1.0, 0.78, 0.2, 1
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
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                padding: [dp(14), dp(4)]
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                BoxLayout:
                    size_hint_y: None
                    height: dp(32)
                    spacing: dp(8)
                    MDLabel:
                        id: rate_status
                        text: "⏳ Loading live rates…"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: root.subtitle_color
                        valign: "center"
                    FlatIconBtn:
                        icon: "content-copy"
                        btn_bg: root.header_color[:3] + [0.13]
                        icon_color: root.header_color
                        btn_radius: 8
                        size: dp(32), dp(32)
                        on_release: root._copy_all()
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
                        spacing: dp(6)
                        size_hint_y: None
                        height: self.minimum_height
                Widget:
                    size_hint_y: None
                    height: dp(80)
<CalcFAB>:
    size_hint: None, None
    size: dp(148), dp(50)
    canvas.before:
        Color:
            rgba: root.btn_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [root.btn_radius]*4
    BoxLayout:
        orientation: 'horizontal'
        spacing: dp(6)
        padding: [dp(10), 0, dp(10), 0]
        MDIcon:
            icon: root.icon
            theme_text_color: "Custom"
            text_color: root.icon_color
            font_size: dp(18)
            halign: "center"
            valign: "middle"
            size_hint_x: None
            width: dp(22)
        Label:
            text: root.btn_label
            font_size: dp(12)
            bold: True
            color: root.icon_color
            halign: "left"
            valign: "middle"
            text_size: self.size
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
}

_current_theme = "amoled"

def apply_app_theme(theme_name):
    global _current_theme
    _current_theme = theme_name
    app = MDApp.get_running_app()
    sm = app.root

    # Switch KivyMD itself into Dark mode (light theme removed)
    app.theme_cls.theme_style = "Dark"

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

class CalcFAB(ButtonBehavior, BoxLayout):
    """Rectangular floating button for the Mini Scientific Calculator."""
    icon       = StringProperty("calculator-variant")
    btn_bg     = ListProperty([0.0, 0.55, 0.46, 1])
    icon_color = ListProperty([0.0, 0.95, 0.80, 1])
    btn_radius = NumericProperty(12)
    btn_label  = StringProperty("MINI SCIENTIFIC\nCALCULATOR")

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

class CompactTile(ButtonBehavior, BoxLayout):
    mod_icon            = StringProperty("help-circle")
    title               = StringProperty("")
    subtitle            = StringProperty("")
    accent              = ListProperty([0.0, 0.85, 0.72, 1])
    card_bg             = ListProperty([0.07, 0.07, 0.07, 1])
    card_title_color    = ListProperty([1, 1, 1, 1])
    card_subtitle_color = ListProperty([0.40, 0.40, 0.40, 1])

class BottomNavBar(ButtonBehavior, BoxLayout):
    bar_bg       = ListProperty([0.04, 0.04, 0.04, 1])
    bar_border   = ListProperty([0.12, 0.12, 0.12, 1])
    active_color = ListProperty([0.0, 0.85, 0.72, 1])
    btn_text     = StringProperty("Home")
    btn_callback = None

def _open_sci_calculator():
    """Open the floating scientific calculator popup."""
    ScientificCalculatorPopup().open()


class ScientificCalculatorPopup(Popup):
    """Mini scientific calculator popup — KivyMD 1.2 compatible."""

    def __init__(self, **kwargs):
        super().__init__(
            title='',
            size_hint=(0.85, 0.68),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
            **kwargs
        )
        self._expr   = ''   # current expression string
        self._result = ''   # last result
        self._just_got_result = False  # flag to clear on next digit
        self._build()

    # ── UI ────────────────────────────────────────────────────────────
    def _build(self):
        from kivy.graphics import Color as _GC, RoundedRectangle as _GRR

        accent  = [0.0, 0.85, 0.72, 1]
        bg      = [0.06, 0.06, 0.08, 1]
        card_bg = [0.10, 0.10, 0.13, 1]

        root = BoxLayout(orientation='vertical', padding=dp(4), spacing=dp(4))

        # Rounded background
        with root.canvas.before:
            _GC(*bg)
            _rr = _GRR(pos=root.pos, size=root.size, radius=[18])
        root.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                  size=lambda w, v, r=_rr: setattr(r, 'size', v))

        # Title bar
        title_row = BoxLayout(size_hint_y=None, height=dp(40),
                              padding=[dp(14), dp(4), dp(4), dp(0)])
        title_lbl = MDLabel(
            text='Scientific Calculator',
            font_style='Subtitle1',
            theme_text_color='Custom',
            text_color=accent,
            bold=True,
            valign='center',
        )
        close_btn = FlatIconBtn(
            icon='close',
            btn_bg=[0.18, 0.18, 0.18, 1],
            icon_color=[0.7, 0.7, 0.7, 1],
            btn_radius=20,
            size=(dp(36), dp(36)),
        )
        close_btn.bind(on_release=lambda *_: self.dismiss())
        title_row.add_widget(title_lbl)
        title_row.add_widget(close_btn)
        root.add_widget(title_row)

        # Display
        disp_box = RoundBox(bg_color=card_bg, box_radius=[12]*4,
                            size_hint_y=None, height=dp(80),
                            padding=[dp(12), dp(6)])
        disp_col = BoxLayout(orientation='vertical', spacing=dp(2))

        self._expr_lbl = MDLabel(
            text='0',
            font_style='Body2',
            theme_text_color='Custom',
            text_color=[0.52, 0.52, 0.56, 1],
            halign='right', valign='center',
            size_hint_y=None, height=dp(26),
            shorten=True, shorten_from='left',
        )
        self._result_lbl = MDLabel(
            text='',
            font_style='H4',
            theme_text_color='Custom',
            text_color=[0.95, 0.95, 0.95, 1],
            halign='right', valign='center',
            bold=True,
            shorten=True, shorten_from='left',
        )
        disp_col.add_widget(self._expr_lbl)
        disp_col.add_widget(self._result_lbl)
        disp_box.add_widget(disp_col)
        root.add_widget(disp_box)

        # Button grid
        btn_colors = {
            'fn':   ([0.15, 0.15, 0.20, 1], [0.55, 0.75, 1.0, 1]),
            'op':   ([0.14, 0.22, 0.14, 1], [0.3,  0.85, 0.55, 1]),
            'eq':   ([0.0,  0.55, 0.46, 1], [0.0,  0.95, 0.80, 1]),
            'num':  ([0.12, 0.12, 0.15, 1], [0.90, 0.90, 0.90, 1]),
            'clr':  ([0.22, 0.08, 0.08, 1], [1.0,  0.4,  0.4,  1]),
            'mem':  ([0.18, 0.10, 0.22, 1], [0.85, 0.5,  1.0,  1]),
        }

        # Layout: rows of buttons
        rows = [
            # row 1 — memory / trig
            [('MC','mem'),('MR','mem'),('M+','mem'),('M−','mem'),('MS','mem')],
            # row 2 — trig / hyp
            [('sin','fn'),('cos','fn'),('tan','fn'),('sinh','fn'),('cosh','fn')],
            # row 3 — powers / log
            [('x²','fn'),('x³','fn'),('xʸ','fn'),('√','fn'), ('∛','fn')],
            # row 4 — log / const
            [('log','fn'),('ln','fn'),('eˣ','fn'),('10ˣ','fn'),('π','num')],
            # row 5 — digits + ops
            [('(',  'op'),(')',  'op'),('%',  'op'),('÷',  'op'),('⌫','clr')],
            [('7',  'num'),('8', 'num'),('9', 'num'),('×',  'op'),('C','clr')],
            [('4',  'num'),('5', 'num'),('6', 'num'),('−',  'op'),('±','fn')],
            [('1',  'num'),('2', 'num'),('3', 'num'),('+',  'op'),('=','eq')],
            [('0',  'num'),('00','num'),('.', 'num'),('e',  'num'),('=','eq')],
        ]

        self._memory = 0.0

        grid = BoxLayout(orientation='vertical', spacing=dp(4))
        for row in rows:
            row_box = BoxLayout(spacing=dp(4), size_hint_y=None, height=dp(46))
            for label, kind in row:
                bg_c, fg_c = btn_colors[kind]
                btn = self._make_calc_btn(label, bg_c, fg_c)
                row_box.add_widget(btn)
            grid.add_widget(row_box)

        root.add_widget(grid)
        self.content = root

    def _make_calc_btn(self, label, bg_c, fg_c):
        btn = ButtonBehavior.__new__(ButtonBehavior)
        box = BoxLayout(size_hint=(1, 1))

        from kivy.graphics import Color as _GC, RoundedRectangle as _GRR
        with box.canvas.before:
            _GC(*bg_c)
            _rr = _GRR(pos=box.pos, size=box.size, radius=[8])
        box.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                 size=lambda w, v, r=_rr: setattr(r, 'size', v))

        lbl = Label(
            text=label,
            font_size=dp(17),
            bold=True,
            color=fg_c,
            halign='center',
            valign='middle',
        )
        lbl.bind(size=lbl.setter('text_size'))
        box.add_widget(lbl)

        # Use ButtonBehavior mixin on the BoxLayout via a touch wrapper
        from kivy.uix.behaviors import ButtonBehavior as BB

        class _Btn(BB, BoxLayout):
            pass

        real_btn = _Btn(size_hint=(1, 1))
        with real_btn.canvas.before:
            _GC(*bg_c)
            _rr2 = _GRR(pos=real_btn.pos, size=real_btn.size, radius=[8])
        real_btn.bind(pos=lambda w, v, r=_rr2: setattr(r, 'pos', v),
                      size=lambda w, v, r=_rr2: setattr(r, 'size', v))
        inner_lbl = Label(
            text=label,
            font_size=dp(17),
            bold=True,
            color=fg_c,
            halign='center',
            valign='middle',
        )
        inner_lbl.bind(size=inner_lbl.setter('text_size'))
        real_btn.add_widget(inner_lbl)
        real_btn.bind(on_release=lambda *_, l=label: self._on_btn(l))
        return real_btn

    # ── Logic ─────────────────────────────────────────────────────────
    def _on_btn(self, label):
        try:
            self._handle(label)
        except Exception as e:
            self._show_error(str(e))

    def _handle(self, label):
        # ── Clear / backspace ──
        if label == 'C':
            self._expr = ''
            self._result = ''
            self._just_got_result = False
            self._refresh('0', '')
            return
        if label == '⌫':
            if self._just_got_result:
                self._expr = ''
                self._just_got_result = False
            else:
                self._expr = self._expr[:-1]
            self._refresh(self._expr or '0', self._result)
            return

        # ── Equals ──
        if label == '=':
            self._evaluate()
            return

        # ── Memory ──
        if label == 'MC':
            self._memory = 0.0;  _snack('Memory cleared');  return
        if label == 'MR':
            self._append(str(self._memory));  return
        if label == 'M+':
            self._memory += self._safe_eval();  _snack(f'M = {self._memory}');  return
        if label == 'M−':
            self._memory -= self._safe_eval();  _snack(f'M = {self._memory}');  return
        if label == 'MS':
            self._memory = self._safe_eval();   _snack(f'M = {self._memory}');  return

        # ── Constants ──
        if label == 'π':
            self._append(str(math.pi));  return
        if label == 'e':
            self._append(str(math.e));   return

        # ── Sign toggle ──
        if label == '±':
            if self._expr and self._expr[0] == '-':
                self._expr = self._expr[1:]
            else:
                self._expr = '-' + self._expr
            self._refresh(self._expr or '0', self._result)
            return

        # ── Functions that wrap the current expression ──
        fn_map = {
            'sin':  'sin(', 'cos':  'cos(', 'tan':  'tan(',
            'sinh': 'sinh(','cosh': 'cosh(',
            'log':  'log10(','ln':  'log(',
            'eˣ':   'exp(',  '10ˣ': '10**(', '√':   'sqrt(',
            '∛':    'cbrt(',
            'x²':   '**2',   'x³':  '**3',   'xʸ':  '**',
        }
        if label in fn_map:
            token = fn_map[label]
            if token.endswith('('):
                if self._just_got_result and self._result:
                    self._expr = token + self._result
                else:
                    self._expr = token + (self._expr or '')
                self._just_got_result = False
            else:
                # postfix operator like **2
                if self._just_got_result and self._result:
                    self._expr = self._result + token
                else:
                    self._expr = self._expr + token
                self._just_got_result = False
            self._refresh(self._expr or '0', '')
            return

        # ── Operators that replace ÷ / × with python equivalents ──
        op_map = {'÷': '/', '×': '*', '−': '-'}
        char = op_map.get(label, label)

        # If we just got a result and tap an operator, carry the result forward
        if self._just_got_result and self._result and char in '+-*/':
            self._expr = self._result + char
            self._just_got_result = False
            self._refresh(self._expr, '')
            return

        self._just_got_result = False
        self._append(char)

    def _append(self, char):
        if self._just_got_result:
            # Starting a new calculation
            if char not in '+-*/%^':
                self._expr = ''
            else:
                self._expr = self._result
            self._just_got_result = False
        self._expr += char
        self._refresh(self._expr, self._result)

    def _evaluate(self):
        raw = self._expr.strip()
        if not raw:
            return
        try:
            result = self._safe_eval(raw)
            # Format nicely
            if isinstance(result, float):
                if result == int(result) and abs(result) < 1e15:
                    txt = str(int(result))
                else:
                    txt = f'{result:.10g}'
            else:
                txt = str(result)
            self._result = txt
            self._just_got_result = True
            self._refresh(raw, txt)
        except ZeroDivisionError:
            self._show_error('Division by zero')
        except Exception:
            self._show_error('Error')

    def _safe_eval(self, expr=None):
        """Evaluate a math expression safely."""
        raw = (expr or self._expr or '0').strip()
        # Replace display chars
        raw = raw.replace('÷', '/').replace('×', '*').replace('−', '-')
        # Close unmatched parentheses
        opens = raw.count('(') - raw.count(')')
        raw += ')' * max(opens, 0)
        # Build a safe namespace
        safe_ns = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
            'log': math.log, 'log10': math.log10, 'log2': math.log2,
            'sqrt': math.sqrt, 'cbrt': lambda x: math.copysign(abs(x) ** (1/3), x),
            'exp': math.exp, 'abs': abs, 'round': round,
            'pi': math.pi, 'e': math.e, 'inf': math.inf,
            'pow': math.pow, 'factorial': math.factorial,
            '__builtins__': {},
        }
        result = eval(raw, safe_ns)  # noqa: S307
        return result

    def _refresh(self, expr_text, result_text):
        self._expr_lbl.text   = expr_text or '0'
        self._result_lbl.text = result_text or ''

    def _show_error(self, msg):
        self._result_lbl.text = msg
        self._expr_lbl.text   = self._expr or '0'


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
                    from kivy.uix.floatlayout import FloatLayout
                    float_layer = FloatLayout(size_hint_y=None, height=dp(58))
                    nav = BottomNavBar(bar_bg=[0.04,0.04,0.04,1],
                                       bar_border=[0.12,0.12,0.12,1],
                                       active_color=self.header_color,
                                       size_hint=(1, None),
                                       height=dp(58))
                    if self.name == 'home':
                        nav.btn_text = 'EXIT'
                        nav.btn_callback = self._confirm_exit
                    else:
                        nav.btn_text = 'HOME'
                        nav.btn_callback = lambda: setattr(self.manager, 'current', 'home')
                    float_layer.add_widget(nav)
                    # Show calc FAB on every screen including home
                    fab = CalcFAB(
                        icon='calculator-variant',
                        btn_bg=[0.0, 0.55, 0.46, 1],
                        icon_color=[0.0, 0.95, 0.80, 1],
                        btn_radius=12,
                        btn_label="MINI SCIENTIFIC\nCALCULATOR",
                        size=(dp(148), dp(50)),
                        pos_hint={'right': 0.97, 'top': 1.70},
                    )
                    fab.bind(on_release=lambda *_: _open_sci_calculator())
                    float_layer.add_widget(fab)
                    root.add_widget(float_layer)

    def _add_nav(self, root_box):
        """Append a floating calc FAB + HOME bottom nav bar to root_box."""
        from kivy.uix.floatlayout import FloatLayout
        from kivy.graphics import Color as _GC, RoundedRectangle as _GRR

        # Wrapper that holds FAB (floating) over nav bar
        wrapper = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(58))

        # Float layer for the FAB
        float_layer = FloatLayout(size_hint_y=None, height=dp(58))

        nav = BottomNavBar(
            bar_bg=[0.04, 0.04, 0.04, 1],
            bar_border=[0.12, 0.12, 0.12, 1],
            active_color=self.header_color,
            size_hint=(1, None),
            height=dp(58),
        )
        nav.btn_text = 'HOME'
        nav.btn_callback = lambda: setattr(self.manager, 'current', 'home')
        float_layer.add_widget(nav)

        # Floating calculator button — right corner above nav
        fab = CalcFAB(
            icon='calculator-variant',
            btn_bg=[0.0, 0.55, 0.46, 1],
            icon_color=[0.0, 0.95, 0.80, 1],
            btn_radius=12,
            btn_label="MINI SCIENTIFIC\nCALCULATOR",
            size=(dp(148), dp(50)),
            pos_hint={'right': 0.97, 'top': 1.70},
        )
        fab.bind(on_release=lambda *_: _open_sci_calculator())
        float_layer.add_widget(fab)

        root_box.add_widget(float_layer)

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
    _recents = []  # list of (name, screen_name) tuples

    # All searchable modules: (display_name, screen_name, keywords)
    _ALL_MODULES = [
        ("Length", "length", "length distance km mi ft meter"),
        ("Weight", "weight", "weight mass kg lb oz gram"),
        ("Temperature", "temperature", "temperature temp celsius fahrenheit kelvin"),
        ("Volume", "volume", "volume liter gallon ml cup"),
        ("Area", "area", "area square meter acre hectare"),
        ("Time", "time", "time second minute hour day year"),
        ("Speed", "speed", "speed velocity kmh mph knot"),
        ("Currency", "currency", "currency money usd eur gbp forex"),
        ("Fuel Economy", "fuel", "fuel mpg l/100km economy"),
        ("Cooking", "cooking", "cooking recipe cup tablespoon"),
        ("Clothing", "clothing", "clothing size shoes apparel"),
        ("Pressure", "pressure", "pressure pascal bar psi atm"),
        ("Energy", "energy", "energy joule calorie kwh"),
        ("Power", "power", "power watt kilowatt horsepower"),
        ("Torque", "torque", "torque newton meter lb ft"),
        ("Acceleration", "acceleration", "acceleration gravity g-force"),
        ("Force", "force", "force newton pound"),
        ("Density", "density", "density kg/m3 g/cm3"),
        ("Flow Rate", "flowrate", "flow rate liter per second gpm"),
        ("Viscosity", "viscosity", "viscosity poise centipoise"),
        ("Angle", "angle", "angle degree radian gradian"),
        ("Frequency", "frequency", "frequency hertz khz mhz"),
        ("Radioactivity", "radioactivity", "radioactivity becquerel curie sievert"),
        ("Sound", "sound", "sound decibel db"),
        ("Electric Units", "electric", "electric voltage current resistance ohm volt amp"),
        ("Magnetic Field", "magnetic", "magnetic tesla gauss"),
        ("Data Storage", "datastorage", "data storage byte kb mb gb tb"),
        ("Typography", "typography", "typography pixel point em rem"),
        ("Color Codes", "color", "color hex rgb hsl"),
        ("Numerals", "numeral", "numeral binary hex decimal octal roman"),
        ("Illuminance", "illuminance", "illuminance lux foot-candle"),
        ("Luminance", "luminance", "luminance candela nit"),
        ("Paper Sizes", "papersize", "paper size a4 letter legal"),
        ("Time Zones", "timezone", "timezone utc gmt time zone world clock"),
        ("Date & Age", "dateage", "date age difference birthday calculator"),
        ("Tip Calculator", "tip", "tip gratuity restaurant bill split"),
        ("Discount / %", "discount", "discount percentage off sale savings"),
        ("BMI / BMR", "bmibmr", "bmi bmr body mass index health"),
        ("Concentration", "concentration", "concentration mol ppm ppb solution"),
        ("Radiation Dose", "raddose", "radiation dose sievert rem mgy"),
        ("Shoe Sizes", "shoesize", "shoe size us uk eu jp cm"),
        ("Ring Sizes", "ringsize", "ring size us uk eu diameter mm"),
        ("Blood Glucose", "bloodglucose", "blood glucose sugar mg/dl mmol"),
        ("Tire Sizes", "tiresize", "tire tyre size aspect ratio"),
        ("Humidity", "humidity", "humidity dew point relative absolute"),
    ]

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_recents_bar()

    def _build_recents_bar(self):
        """Populate the recents chip row."""
        try:
            bar = self.ids.recents_bar
            bar.clear_widgets()
            if not self._recents:
                bar.add_widget(MDLabel(
                    text="No recent modules yet",
                    font_style='Caption',
                    theme_text_color='Custom',
                    text_color=self.subtitle_color,
                    size_hint_x=None, width=dp(200),
                ))
                return
            for name, sname in self._recents[-6:][::-1]:
                chip = UnitChip(chip_text=name, accent=self.header_color)
                chip.bind(on_release=lambda c, s=sname: self.go(s))
                bar.add_widget(chip)
        except Exception:
            pass

    def go(self, name):
        # Build the screen on-demand the very first time it is requested.
        # This replaces the old loading screen: screens are instant to
        # build individually, so the user never waits.
        if not self.manager.has_screen(name):
            cls = {n: c for n, c in SCREEN_MAP}.get(name)
            if cls:
                self.manager.add_widget(cls(name=name))

        # Track recents
        entry = (name.replace('_', ' ').title(), name)
        for dname, sname, _ in self._ALL_MODULES:
            if sname == name:
                entry = (dname, name)
                break
        if entry in self._recents:
            self._recents.remove(entry)
        self._recents.append(entry)
        self.manager.transition.direction = "left"
        self.manager.current = name

    def on_search(self, query):
        try:
            sv = self.ids.main_scroll
            grid = self.ids.modules_grid
        except Exception:
            return
        query = query.strip().lower()
        grid.clear_widgets()
        if not query:
            sv.scroll_y = 1
            return
        results = []
        for dname, sname, keywords in self._ALL_MODULES:
            if query in dname.lower() or any(query in kw for kw in keywords.split()):
                results.append((dname, sname))
        if not results:
            grid.add_widget(MDLabel(
                text="No results found",
                font_style='Body2',
                theme_text_color='Custom',
                text_color=self.subtitle_color,
                size_hint_y=None, height=dp(48),
                halign='center',
            ))
            return
        for dname, sname in results[:12]:
            from kivy.uix.behaviors import ButtonBehavior as _BB
            from kivy.graphics import Color as _C2, RoundedRectangle as _RR2
            class _Chip(_BB, BoxLayout):
                pass
            chip = _Chip(size_hint_y=None, height=dp(48),
                         padding=[dp(14), dp(8)], spacing=dp(8))
            with chip.canvas.before:
                _C2(*self.card_bg)
                _rr = _RR2(pos=chip.pos, size=chip.size, radius=[12])
            chip.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                      size=lambda w, v, r=_rr: setattr(r, 'size', v))
            chip.add_widget(MDLabel(
                text=dname,
                font_style='Body2',
                theme_text_color='Custom',
                text_color=self.header_color,
                bold=True, valign='center',
            ))
            chip.bind(on_release=lambda *_, s=sname: self.go(s))
            grid.add_widget(chip)

    def open_settings(self):
        _ensure_screen(self.manager, "settings")
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

class SettingsScreen(ConverterScreen):
    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_settings_ui()

    def _build_settings_ui(self):
        self.clear_widgets()
        t = THEMES[_current_theme]

        root_box = BoxLayout(orientation='vertical')

        # ── Top bar ──
        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        from kivy.graphics import Color, Rectangle
        with root_box.canvas.before:
            Color(*t["screen_bg"])
            _bg_rect = Rectangle(pos=root_box.pos, size=root_box.size)
        root_box.bind(pos=lambda w, v: setattr(_bg_rect, 'pos', v),
                      size=lambda w, v: setattr(_bg_rect, 'size', v))

        back_btn = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                text_color=self.header_color)
        back_btn.bind(on_release=self.go_back)
        title_lbl = MDLabel(text="Settings", font_style="H6", theme_text_color="Custom",
                            text_color=self.header_color, bold=True, valign="center")
        top.add_widget(back_btn)
        top.add_widget(title_lbl)
        root_box.add_widget(top)

        # ── Scrollable content ──
        sv = ScrollView()
        box = BoxLayout(orientation='vertical', spacing=dp(16),
                        padding=[dp(14), dp(8), dp(14), dp(16)], size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        # ── APPEARANCE section ──
        sec_lbl = MDLabel(text="APPEARANCE", font_style="Overline",
                          theme_text_color="Custom",
                          text_color=self.subtitle_color,
                          size_hint_y=None, height=dp(28), bold=True)
        box.add_widget(sec_lbl)

        # Theme selection cards
        themes_info = [
            ("amoled", "AMOLED Dark", "Pure black — best for OLED screens",
             "moon-waning-crescent", [0.0, 0.85, 0.72, 1]),
            ("grey",   "Grey Dark",   "Dark grey — easy on the eyes",
             "weather-night", [0.55, 0.55, 1.0, 1]),
        ]
        self._theme_cards = {}
        for theme_key, theme_name, theme_desc, theme_icon, t_accent in themes_info:
            card = self._make_theme_card(theme_key, theme_name, theme_desc,
                                         theme_icon, t_accent)
            box.add_widget(card)
            self._theme_cards[theme_key] = card

        # ── ABOUT section ──
        box.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))
        about_lbl = MDLabel(text="ABOUT", font_style="Overline",
                            theme_text_color="Custom",
                            text_color=self.subtitle_color,
                            size_hint_y=None, height=dp(28), bold=True)
        box.add_widget(about_lbl)

        # License Details row
        lic_row = self._make_settings_row(
            icon="certificate-outline",
            label="License Details",
            desc="View your license and activation status",
            accent=[0.0, 0.85, 0.72, 1],
            callback=self._open_license_details,
        )
        box.add_widget(lic_row)

        # Features & About row
        about_row = self._make_settings_row(
            icon="information-outline",
            label="Features & About",
            desc="All 45 modules, calculator, and app info",
            accent=[0.55, 0.55, 1.0, 1],
            callback=self._open_about,
        )
        box.add_widget(about_row)

        sv.add_widget(box)
        root_box.add_widget(sv)

        # ── Bottom nav: SETTINGS label ──
        nav_bar = BoxLayout(size_hint_y=None, height=dp(58))
        from kivy.graphics import Color as _C2, Rectangle as _R2
        with nav_bar.canvas.before:
            _C2(*t.get("bottom_nav_bg", t["card_bg"]))
            _nb_rect = _R2(pos=nav_bar.pos, size=nav_bar.size)
            _C2(*t.get("bottom_nav_border", [0.2, 0.2, 0.2, 1]))
            _nb_line = _R2(pos=(nav_bar.x, nav_bar.top), size=(nav_bar.width, dp(1)))
        nav_bar.bind(
            pos=lambda w, v: setattr(_nb_rect, 'pos', v),
            size=lambda w, v: setattr(_nb_rect, 'size', v),
        )
        nav_lbl = MDLabel(
            text="SETTINGS",
            font_style="Button",
            theme_text_color="Custom",
            text_color=self.header_color,
            halign="center", valign="middle",
            bold=True,
        )
        nav_bar.add_widget(nav_lbl)
        root_box.add_widget(nav_bar)

        self.add_widget(root_box)

    def _make_theme_card(self, theme_key, theme_name, theme_desc,
                         theme_icon, accent):
        """Build a tappable theme selection card with active indicator."""
        is_active = (_current_theme == theme_key)
        # Use a plain BoxLayout + ButtonBehavior via a small helper class
        from kivy.uix.behaviors import ButtonBehavior as BB
        class _ThemeCard(BB, BoxLayout):
            pass
        card = _ThemeCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(72),
            padding=[dp(14), dp(12), dp(14), dp(12)],
            spacing=dp(14),
        )
        from kivy.graphics import Color, RoundedRectangle
        border_col = list(accent[:3]) + [0.6] if is_active else [0.15, 0.15, 0.18, 1]
        card_bg    = list(accent[:3]) + [0.12] if is_active else list(self.card_bg)
        with card.canvas.before:
            _bg  = Color(*card_bg)
            _rr  = RoundedRectangle(pos=card.pos, size=card.size, radius=[14])
            _bor = Color(*border_col)
            from kivy.graphics import Line
            _line = Line(rounded_rectangle=(card.x, card.y,
                                            card.width, card.height, 14),
                         width=1.5 if is_active else 0.8)
        def _upd_card(w, v):
            _rr.pos  = w.pos;  _rr.size  = w.size
            _line.rounded_rectangle = (w.x, w.y, w.width, w.height, 14)
        card.bind(pos=_upd_card, size=_upd_card)

        # Icon
        icon_box = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)))
        icon_box.pos_hint = {"center_y": .5}
        from kivy.graphics import Color as Cb, RoundedRectangle as RRb
        with icon_box.canvas.before:
            Cb(*list(accent[:3]) + [0.18])
            RRb(pos=icon_box.pos, size=icon_box.size, radius=[12])
        icon_box.bind(pos=lambda w, v: None, size=lambda w, v: None)
        from kivymd.uix.label import MDIcon
        icon_lbl = MDIcon(
                icon=theme_icon, theme_text_color="Custom",
                text_color=accent, halign="center", font_size=dp(22))
        icon_box.add_widget(icon_lbl)

        # Text column
        txt_col = BoxLayout(orientation='vertical', spacing=dp(2))
        txt_col.pos_hint = {"center_y": .5}
        name_lbl = MDLabel(text=theme_name, font_style="Body1",
                           theme_text_color="Custom",
                           text_color=self.card_title_color,
                           bold=True, size_hint_y=None, height=dp(22))
        desc_lbl = MDLabel(text=theme_desc, font_style="Caption",
                           theme_text_color="Custom",
                           text_color=self.subtitle_color,
                           size_hint_y=None, height=dp(18))
        txt_col.add_widget(name_lbl)
        txt_col.add_widget(desc_lbl)

        # Active check
        from kivymd.uix.label import MDIcon as MDIconChk
        check_icon = MDIconChk(
            icon="check-circle" if is_active else "circle-outline",
            theme_text_color="Custom",
            text_color=accent if is_active else [0.3, 0.3, 0.3, 1],
            font_size=dp(22),
            size_hint=(None, None), size=(dp(28), dp(28)),
        )
        check_icon.pos_hint = {"center_y": .5}

        card.add_widget(icon_box)
        card.add_widget(txt_col)
        card.add_widget(check_icon)
        card.bind(on_release=lambda *_: self.set_theme(theme_key))
        return card

    def _make_settings_row(self, icon, label, desc, accent, callback):
        """Build a tappable settings row item."""
        from kivy.uix.behaviors import ButtonBehavior as BB
        class _Row(BB, BoxLayout):
            pass
        row = _Row(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(64),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(14),
        )
        from kivy.graphics import Color, RoundedRectangle
        with row.canvas.before:
            Color(*self.card_bg)
            _rr = RoundedRectangle(pos=row.pos, size=row.size, radius=[14])
        row.bind(pos=lambda w, v: setattr(_rr, 'pos', v),
                 size=lambda w, v: setattr(_rr, 'size', v))

        icon_box = BoxLayout(size_hint=(None, None), size=(dp(40), dp(40)))
        icon_box.pos_hint = {"center_y": .5}
        from kivy.graphics import Color as Cb, RoundedRectangle as RRb
        with icon_box.canvas.before:
            Cb(*list(accent[:3]) + [0.18])
            RRb(pos=icon_box.pos, size=icon_box.size, radius=[10])
        from kivymd.uix.label import MDIcon
        icon_box.add_widget(MDIcon(icon=icon, theme_text_color="Custom",
                                   text_color=accent, halign="center",
                                   font_size=dp(20)))

        txt_col = BoxLayout(orientation='vertical', spacing=dp(2))
        txt_col.pos_hint = {"center_y": .5}
        txt_col.add_widget(MDLabel(text=label, font_style="Body1",
                                   theme_text_color="Custom",
                                   text_color=self.card_title_color,
                                   bold=True, size_hint_y=None, height=dp(22)))
        txt_col.add_widget(MDLabel(text=desc, font_style="Caption",
                                   theme_text_color="Custom",
                                   text_color=self.subtitle_color,
                                   size_hint_y=None, height=dp(18)))

        from kivymd.uix.label import MDIcon as MDI2
        chev = MDI2(icon="chevron-right", theme_text_color="Custom",
                    text_color=self.subtitle_color, font_size=dp(20),
                    size_hint=(None, None), size=(dp(24), dp(24)))
        chev.pos_hint = {"center_y": .5}

        row.add_widget(icon_box)
        row.add_widget(txt_col)
        row.add_widget(chev)
        row.bind(on_release=lambda *_: callback())
        return row

    def set_theme(self, theme):
        global _current_theme
        _current_theme = theme
        apply_app_theme(theme)
        # Rebuild settings UI to update active indicators
        self._build_settings_ui()

    def go_back(self, *args):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        Clock.schedule_once(lambda dt: self._build_settings_ui(), 0)

    def _open_license_details(self):
        _ensure_screen(self.manager, "license_details")
        self.manager.transition.direction = "left"
        self.manager.current = "license_details"

    def _open_about(self):
        _ensure_screen(self.manager, "about")
        self.manager.transition.direction = "left"
        self.manager.current = "about"


class LicenseDetailsScreen(ConverterScreen):
    """Shows the full license gate screen content as a read-only view from settings."""
    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        t = THEMES[_current_theme]

        root_box = BoxLayout(orientation='vertical')
        from kivy.graphics import Color, Rectangle
        with root_box.canvas.before:
            Color(*t["screen_bg"])
            _bg = Rectangle(pos=root_box.pos, size=root_box.size)
        root_box.bind(pos=lambda w, v: setattr(_bg, 'pos', v),
                      size=lambda w, v: setattr(_bg, 'size', v))

        # Top bar
        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back_btn = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                text_color=self.header_color)
        back_btn.bind(on_release=lambda *_: self._go_settings())
        top.add_widget(back_btn)
        top.add_widget(MDLabel(text="License Details", font_style="H6",
                               theme_text_color="Custom",
                               text_color=self.header_color,
                               bold=True, valign="center"))
        root_box.add_widget(top)

        sv = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(12),
                            padding=[dp(14), dp(6), dp(14), dp(22)],
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # ── Access status ──
        access = _shv_get_access_status()
        trial = access.get('trial') or {}
        is_licensed = access.get('mode') == 'licensed'
        can_continue = bool(access.get('valid'))
        session = _shv_ensure_session(silent=True)
        signed_in = bool((session or {}).get('access_token'))
        name, email, plan = _shv_cloud_account_label(session)

        def _card_box(tint_hex):
            box = BoxLayout(orientation='vertical', spacing=dp(4),
                            size_hint_y=None,
                            padding=[dp(14), dp(12), dp(14), dp(12)])
            box.bind(minimum_height=box.setter('height'))
            _bind_tinted(box, tint_hex)
            return box

        # Status summary
        status_card = _card_box(_C['green'] if can_continue else _C['warning'])
        status_card.add_widget(make_lbl(
            '✅ ACCESS GRANTED' if can_continue else '⚠️  ACCESS REQUIRED',
            'green' if can_continue else 'warning', 13, bold=True, height=22))
        mode_text = {'licensed': 'Pro License', 'trial': 'Demo Trial', 'none': 'No Access'}
        status_card.add_widget(make_lbl(
            f"Mode: {mode_text.get(access.get('mode', 'none'), 'Unknown')}",
            'text', 12, height=20))
        status_card.add_widget(make_lbl(access.get('message', ''), 'subtext', 11, height=20))
        content.add_widget(status_card)

        # Device code
        dev_code = _shv_get_device_code()
        dev_card = _card_box(_C['accent2'])
        dev_card.add_widget(make_lbl('DEVICE CODE', 'subtext', 11, bold=True, height=16))
        dev_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(10))
        dev_row.add_widget(make_lbl(dev_code, 'text', 16, bold=True, height=26))
        copy_dev = MDRaisedButton(
            text="COPY", md_bg_color=self.header_color[:3] + [0.2],
            theme_text_color="Custom", text_color=self.header_color,
            size_hint=(None, None), size=(dp(70), dp(32)),
        )
        copy_dev.bind(on_release=lambda *_: (
            Clipboard.copy(dev_code), _snack(f"Copied: {dev_code}")))
        dev_row.add_widget(copy_dev)
        dev_card.add_widget(dev_row)
        content.add_widget(dev_card)

        # SH Vertex account
        acct_card = _card_box(_C['accent'] if signed_in else _C['border'])
        acct_card.add_widget(make_lbl('SH VERTEX ACCOUNT', 'subtext', 11, bold=True, height=16))
        acct_card.add_widget(make_lbl(
            'CONNECTED' if signed_in else 'NOT CONNECTED',
            'green' if signed_in else 'warning', 13, bold=True, height=20))
        if signed_in:
            acct_card.add_widget(make_lbl(name, 'text', 12, height=18))
            acct_card.add_widget(make_lbl(email, 'subtext', 10, height=16))
            acct_card.add_widget(make_lbl(f'Plan: {plan}', 'subtext', 10, height=14))
        content.add_widget(acct_card)

        # License info (if licensed)
        if is_licensed:
            lic = _shv_load_license() or {}
            payload = lic.get('payload') or {}
            lic_card = _card_box(_C['green'])
            lic_card.add_widget(make_lbl('ACTIVE PRO LICENSE', 'text', 11, bold=True, height=16))
            lic_card.add_widget(make_lbl(
                f"License ID: {access.get('license_id', '--')}", 'subtext', 10, height=16))
            lic_card.add_widget(make_lbl(
                f"Tier: {(access.get('tier') or 'pro').upper()}", 'text', 12, bold=True, height=20))
            expiry = str(payload.get('expires_at', '') or payload.get('expiry', '') or '').strip()
            lic_card.add_widget(make_lbl(
                f"Expires: {expiry[:10] if expiry else 'Never (Perpetual)'}",
                'subtext', 10, height=16))
            content.add_widget(lic_card)

        # Demo info (if trial)
        elif trial.get('valid'):
            trial_card = _card_box(_C['accent'])
            trial_card.add_widget(make_lbl('DEMO TRIAL ACTIVE', 'text', 11, bold=True, height=16))
            trial_card.add_widget(make_lbl(
                f"Time remaining: {trial.get('remaining_text', '?')}",
                'text', 13, bold=True, height=20))
            trial_card.add_widget(make_lbl(
                f"Trial duration: {trial.get('hours', 48)} hours",
                'subtext', 10, height=16))
            content.add_widget(trial_card)

        content.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(content)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _go_settings(self):
        _ensure_screen(self.manager, "settings")
        self.manager.transition.direction = "right"
        self.manager.current = "settings"

    def apply_theme(self, theme_name):
        super().apply_theme(theme_name)
        Clock.schedule_once(lambda dt: self._build_ui(), 0)

class NumeralScreen(ConverterScreen):
    _from_base = "dec"
    _to_base   = "all"
    BASE_NAMES = {
        "dec": "DECIMAL", "bin": "BINARY",
        "hex": "HEXADECIMAL", "oct": "OCTAL",
        "txt": "TEXT / ASCII", "rom": "ROMAN NUMERALS",
    }
    CHIP_IDS = {
        "dec": "chip_dec", "bin": "chip_bin", "hex": "chip_hex",
        "oct": "chip_oct", "txt": "chip_txt", "rom": "chip_rom",
    }
    ROW_IDS = {
        "dec": "row_dec", "bin": "row_bin", "hex": "row_hex",
        "oct": "row_oct", "txt": "row_txt", "rom": "row_rom",
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
            "rom": "e.g. XIV  or  MMXXIV",
        }
        tips = {
            "dec": "Tap any chip to set it as input",
            "bin": "Tap any chip to set it as input",
            "hex": "Hex letters A-F are case-insensitive",
            "oct": "Tap any chip to set it as input",
            "txt": "Each character shown as ASCII code point",
            "rom": "Roman numerals 1-3999 (I V X L C D M)",
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
            _snack(f"Copied: {val[:36]}{'...' if len(val) > 36 else ''}")
        else:
            _snack("Nothing to copy")
    def swap_conversion(self):
        order = ["dec", "bin", "hex", "oct", "txt", "rom"]
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
                self.ids.row_rom.set_value("—")
                self.ids.output_field.text = "DEC: " + " ".join(str(c) for c in pts)
            elif self._from_base == "rom":
                n = _roman_to_int(raw)
                self._populate_rows(n)
                self.ids.output_field.text = f"DEC:{n}  BIN:{bin(n)[2:]}  HEX:{hex(n)[2:].upper()}"
            else:
                n = self._parse(raw, self._from_base)
                self._populate_rows(n)
                if self._to_base == "all":
                    parts = []
                    if self._from_base != "dec": parts.append(f"DEC:{n}")
                    if self._from_base != "bin": parts.append(f"BIN:{bin(n)[2:]}")
                    if self._from_base != "hex": parts.append(f"HEX:{hex(n)[2:].upper()}")
                    if self._from_base != "oct": parts.append(f"OCT:{oct(n)[2:]}")
                    ch = self._to_char(n)
                    if ch:                        parts.append(f"TXT:{ch}")
                    rom = _int_to_roman(n)
                    if not rom.startswith('Out'): parts.append(f"ROM:{rom}")
                    self.ids.output_field.text = "  ".join(parts)
                elif self._to_base == "txt":
                    self.ids.output_field.text = self._to_char(n)
                elif self._to_base == "rom":
                    self.ids.output_field.text = _int_to_roman(n)
                else:
                    self.ids.output_field.text = self._format(n, self._to_base)
        except Exception:
            self.ids.output_field.text = "invalid input"
            self._set_all_rows("error")
    def _populate_rows(self, n):
        self.ids.row_dec.set_value(str(n))
        self.ids.row_bin.set_value(bin(n)[2:])
        self.ids.row_hex.set_value(hex(n)[2:].upper())
        self.ids.row_oct.set_value(oct(n)[2:])
        self.ids.row_txt.set_value(self._to_char(n))
        self.ids.row_rom.set_value(_int_to_roman(n))
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
    ("USD", "US"),  ("EUR", "EU"),  ("GBP", "GB"),  ("JPY", "JP"),
    ("CNY", "CN"),  ("INR", "IN"),  ("CAD", "CA"),  ("AUD", "AU"),
    ("CHF", "CH"),  ("BRL", "BR"),  ("MXN", "MX"),  ("SGD", "SG"),
    ("HKD", "HK"),  ("NOK", "NO"),  ("SEK", "SE"),  ("DKK", "DK"),
    ("NZD", "NZ"),  ("ZAR", "ZA"),  ("RUB", "RU"),  ("TRY", "TR"),
    ("KRW", "KR"),  ("IDR", "ID"),  ("SAR", "SA"),  ("AED", "AE"),
    ("PLN", "PL"),  ("THB", "TH"),  ("MYR", "MY"),  ("PHP", "PH"),
    ("EGP", "EG"),  ("PKR", "PK"),  ("LKR", "LK"),
    # Extended
    ("CZK", "CZ"),  ("HUF", "HU"),  ("RON", "RO"),  ("BGN", "BG"),
    ("VND", "VN"),  ("BDT", "BD"),  ("NGN", "NG"),  ("GHS", "GH"),
    ("KES", "KE"),  ("UAH", "UA"),  ("CLP", "CL"),  ("COP", "CO"),
    ("PEN", "PE"),  ("ILS", "IL"),  ("TWD", "TW"),  ("QAR", "QA"),
    ("KWD", "KW"),  ("BHD", "BH"),  ("OMR", "OM"),  ("JOD", "JO"),
]

# Default offline fallback rates (USD base)
_CURRENCY_FALLBACK = {
    "USD":1.0,"EUR":0.92,"GBP":0.79,"JPY":149.5,"CNY":7.24,"INR":83.1,
    "CAD":1.36,"AUD":1.53,"CHF":0.9,"BRL":4.97,"MXN":17.15,"SGD":1.34,
    "HKD":7.82,"NOK":10.6,"SEK":10.4,"DKK":6.89,"NZD":1.63,"ZAR":18.9,
    "RUB":91.5,"TRY":32.3,"KRW":1330.0,"IDR":15700.0,"SAR":3.75,"AED":3.67,
    "PLN":4.03,"THB":35.1,"MYR":4.72,"PHP":56.3,"EGP":30.9,"PKR":278.0,
    "LKR":365.0,"CZK":22.8,"HUF":357.0,"RON":4.58,"BGN":1.80,"VND":24500.0,
    "BDT":110.0,"NGN":1480.0,"GHS":12.5,"KES":130.0,"UAH":37.5,"CLP":930.0,
    "COP":3900.0,"PEN":3.72,"ILS":3.65,"TWD":31.5,"QAR":3.64,"KWD":0.307,
    "BHD":0.377,"OMR":0.385,"JOD":0.71,
}

class CurrencyScreen(ConverterScreen):
    _from_currency = "USD"
    _rates         = {}
    _fetched       = False
    _fetch_time    = ""
    _favourites    = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD"]

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_chips()
        self._build_rows()
        Clock.schedule_once(lambda dt: self.fetch_rates(), 0.3)

    def _build_chips(self):
        container = self.ids.from_chips
        container.clear_widgets()
        self._chips = {}
        for code, country in CURRENCIES:
            label = f"{country} {code}"
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
        from kivy.graphics import Color as _KC, RoundedRectangle as _KRR

        # ── Favourites section header ──
        fav_hdr = MDLabel(
            text="★  FAVOURITES",
            font_style='Overline',
            theme_text_color='Custom',
            text_color=[1.0, 0.85, 0.2, 1],
            bold=True,
            size_hint_y=None, height=dp(24),
        )
        container.add_widget(fav_hdr)

        all_codes = [c for c, _ in CURRENCIES]
        ordered = self._favourites + [c for c in all_codes if c not in self._favourites]

        self._all_hdr_added = False

        for i, code in enumerate(ordered):
            if not self._all_hdr_added and code not in self._favourites:
                all_hdr = MDLabel(
                    text="ALL CURRENCIES",
                    font_style='Overline',
                    theme_text_color='Custom',
                    text_color=[0.48, 0.48, 0.48, 1],
                    bold=True,
                    size_hint_y=None, height=dp(24),
                )
                container.add_widget(all_hdr)
                self._all_hdr_added = True

            country = dict(CURRENCIES).get(code, code[:2])
            col = colors[i % len(colors)]
            col_bg = list(col[:3]) + [0.12]
            is_fav = code in self._favourites

            card = BoxLayout(
                orientation='horizontal',
                size_hint_y=None, height=dp(48),
                padding=[dp(8), dp(6), dp(6), dp(6)],
                spacing=dp(6),
            )
            with card.canvas.before:
                _KC(*col_bg)
                _rr = _KRR(pos=card.pos, size=card.size, radius=[10])
            card.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                      size=lambda w, v, r=_rr: setattr(r, 'size', v))

            # Country badge
            badge = RoundBox(
                bg_color=list(col[:3]) + [0.22],
                box_radius=[6]*4,
                size_hint=(None, None),
                size=(dp(32), dp(28)),
            )
            badge.add_widget(MDLabel(
                text=country, font_style='Caption',
                theme_text_color='Custom', text_color=col,
                bold=True, halign='center', valign='center',
            ))

            # Code label
            code_lbl = MDLabel(
                text=code, font_style='Caption',
                theme_text_color='Custom', text_color=col,
                bold=True, size_hint=(None, 1), width=dp(38),
                halign='left', valign='center',
            )

            # Value label
            val_lbl = MDLabel(
                text='—', font_style='Body2',
                theme_text_color='Custom', text_color=self.text_color,
                halign='right', valign='center',
                shorten=True, shorten_from='right',
            )

            # Star (favourite toggle)
            star_btn = FlatIconBtn(
                icon='star' if is_fav else 'star-outline',
                btn_bg=[0.0, 0.0, 0.0, 0.0],
                icon_color=[1.0, 0.85, 0.2, 1] if is_fav else [0.3, 0.3, 0.3, 1],
                btn_radius=6,
                size=(dp(30), dp(30)),
            )
            star_btn.bind(on_release=lambda *_, c=code: self._toggle_fav(c))

            # Swap-source button (tap row to use as source)
            swap_btn = FlatIconBtn(
                icon='swap-horizontal',
                btn_bg=list(col[:3]) + [0.0],
                icon_color=list(col[:3]) + [0.7],
                btn_radius=6,
                size=(dp(30), dp(30)),
            )
            swap_btn.bind(on_release=lambda *_, c=code: self._select(c))

            # Copy button
            copy_btn = FlatIconBtn(
                icon='content-copy',
                btn_bg=list(col[:3]) + [0.0],
                icon_color=list(col[:3]) + [0.7],
                btn_radius=6,
                size=(dp(30), dp(30)),
            )
            copy_btn.bind(on_release=lambda *_, v=val_lbl, c=code: self._copy_val(v, c))

            card.add_widget(badge)
            card.add_widget(code_lbl)
            card.add_widget(val_lbl)
            card.add_widget(star_btn)
            card.add_widget(swap_btn)
            card.add_widget(copy_btn)

            container.add_widget(card)
            self._rows[code] = val_lbl

        # Disclaimer
        disc = MDLabel(
            text="ⓘ  Mid-market rates · Not bank/exchange rates · For reference only",
            font_style='Caption',
            theme_text_color='Custom',
            text_color=[0.45, 0.45, 0.45, 1],
            halign='center',
            size_hint_y=None, height=dp(32),
        )
        container.add_widget(disc)

    def _toggle_fav(self, code):
        if code in self._favourites:
            self._favourites.remove(code)
        else:
            self._favourites.insert(0, code)
        self._build_rows()
        self.do_convert()

    def _copy_val(self, val_lbl, code):
        val = val_lbl.text
        if val not in ('—', 'error', ''):
            Clipboard.copy(val)
            _snack(f"Copied {code}: {val}")
        else:
            _snack("Nothing to copy")

    def _copy_all(self):
        if not self._fetched:
            _snack("Rates not loaded yet")
            return
        lines = []
        for code, _ in CURRENCIES:
            v = self._rows.get(code)
            if v and v.text not in ('—', 'error', ''):
                lines.append(f"{code}: {v.text}")
        if lines:
            Clipboard.copy("\n".join(lines))
            _snack(f"Copied {len(lines)} rates")

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
            from datetime import datetime as _now
            self._fetch_time = _now.now().strftime("%H:%M")
            self.ids.rate_status.text = f"✅ Live rates  ·  Updated {self._fetch_time}  ·  Mid-market"
            self.do_convert()
        else:
            self._on_fail(req, result)

    def _on_fail(self, *_):
        self.ids.rate_status.text = "⚠️ Offline fallback rates (not live)"
        self._rates = dict(_CURRENCY_FALLBACK)
        self._fetched = True
        self.do_convert()

    def do_convert(self):
        raw = self.ids.amount_field.text.strip()
        if not raw:
            for lbl in self._rows.values():
                lbl.text = "—"
            return
        if not self._fetched:
            return
        try:
            amount = float(raw)
        except ValueError:
            for lbl in self._rows.values():
                lbl.text = "error"
            return
        from_rate = self._rates.get(self._from_currency, 1.0)
        usd_val   = amount / from_rate
        for code, _ in CURRENCIES:
            if code not in self._rows:
                continue
            to_rate = self._rates.get(code, _CURRENCY_FALLBACK.get(code, 1.0))
            converted = usd_val * to_rate
            if code == self._from_currency:
                self._rows[code].text = "{:,.4f}".format(amount)
            else:
                self._rows[code].text = "{:,.4f}".format(converted)

# ════════════════════════════════════════════════════════════════════
# NEW MODULE CLASSES  (Phase 3)
# ════════════════════════════════════════════════════════════════════

# ── Force ──────────────────────────────────────────────────────────
class ForceScreen(GenericUnitScreen):
    TITLE  = "Force"
    ACCENT = [0.9, 0.35, 0.35, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("N",     1.0),
        ("kN",    1e3),
        ("MN",    1e6),
        ("lbf",   4.4482216),
        ("kgf",   9.80665),
        ("dyne",  1e-5),
        ("kip",   4448.2216),
        ("ozf",   0.27801385),
        ("pdl",   0.13825495),
    ]

# ── Density ────────────────────────────────────────────────────────
class DensityScreen(GenericUnitScreen):
    TITLE  = "Density"
    ACCENT = [0.4, 0.85, 0.55, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("kg/m³",   1.0),
        ("g/cm³",   1000.0),
        ("g/mL",    1000.0),
        ("kg/L",    1000.0),
        ("lb/ft³",  16.018463),
        ("lb/in³",  27679.905),
        ("lb/gal",  119.8264),
        ("oz/in³",  1729.994),
        ("t/m³",    1000.0),
    ]

# ── Flow Rate ──────────────────────────────────────────────────────
class FlowRateScreen(GenericUnitScreen):
    TITLE  = "Flow Rate"
    ACCENT = [0.3, 0.75, 1.0, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("L/s",    1.0),
        ("L/min",  1/60),
        ("L/h",    1/3600),
        ("m³/s",   1000.0),
        ("m³/min", 1000/60),
        ("m³/h",   1000/3600),
        ("mL/s",   0.001),
        ("mL/min", 0.001/60),
        ("GPM",    0.0630902),    # US gal/min
        ("GPH",    0.00105150),   # US gal/h
        ("CFM",    0.471947),     # ft³/min
        ("CFS",    28.3168),      # ft³/s
    ]

# ── Viscosity (dynamic / kinematic) ────────────────────────────────
class ViscosityScreen(GenericUnitScreen):
    TITLE  = "Viscosity"
    ACCENT = [0.5, 0.7, 1.0, 1]
    FMT    = ":.6g"
    # Dynamic viscosity base = Pa·s
    UNITS  = [
        ("Pa·s",   1.0),
        ("mPa·s",  1e-3),
        ("cP",     1e-3),         # centipoise = mPa·s
        ("P",      0.1),          # poise
        ("lb/(ft·s)", 1.48816),
        ("lb/(ft·h)", 4.13378e-4),
        # Kinematic (base m²/s) – listed together for convenience
        # Only convert within dynamic OR kinematic; cross-group needs density.
        # We keep all as dynamic-equivalent and note in subtitle.
    ]
    # Override: kinematic sub-group uses its own base (m²/s = 1)
    # We add kinematic units by mapping via a note factor approach.
    # For simplicity we only expose dynamic units here.

# ── Electric Units ─────────────────────────────────────────────────
class ElectricScreen(ConverterScreen):
    """Three separate sub-groups: Voltage, Current, Resistance."""
    _group = "voltage"   # "voltage" | "current" | "resistance"

    GROUPS = {
        "voltage": {
            "label": "Voltage",
            "accent": [0.55, 0.55, 1.0, 1],
            "units": [
                ("V",   1.0), ("mV",  1e-3), ("µV",  1e-6),
                ("kV",  1e3), ("MV",  1e6),
            ],
        },
        "current": {
            "label": "Current",
            "accent": [1.0, 0.75, 0.2, 1],
            "units": [
                ("A",   1.0), ("mA",  1e-3), ("µA",  1e-6),
                ("kA",  1e3), ("nA",  1e-9),
            ],
        },
        "resistance": {
            "label": "Resistance",
            "accent": [0.4, 0.9, 0.5, 1],
            "units": [
                ("Ω",   1.0), ("mΩ",  1e-3), ("kΩ",  1e3),
                ("MΩ",  1e6), ("GΩ",  1e9),
            ],
        },
    }

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        t = THEMES[_current_theme]

        root_box = BoxLayout(orientation="vertical")

        # ── top bar ──
        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        lbl = MDLabel(text="Electric Units", font_style="H6",
                      theme_text_color="Custom", text_color=self.header_color,
                      bold=True, valign="center")
        top.add_widget(back)
        top.add_widget(lbl)
        root_box.add_widget(top)

        # ── group chips ──
        chip_row = BoxLayout(size_hint_y=None, height=dp(44),
                             padding=[dp(14), dp(4)], spacing=dp(8))
        self._group_chips = {}
        for key, info in self.GROUPS.items():
            chip = BaseChip(chip_text=info["label"],
                            accent=info["accent"],
                            is_active=(key == self._group))
            chip.bind(on_release=lambda c, k=key: self._switch_group(k))
            chip_row.add_widget(chip)
            self._group_chips[key] = chip
        root_box.add_widget(chip_row)

        # ── scroll area ──
        sv = ScrollView()
        self._content_box = BoxLayout(orientation="vertical",
                                      padding=[dp(14), dp(8)],
                                      spacing=dp(12),
                                      size_hint_y=None)
        self._content_box.bind(minimum_height=self._content_box.setter("height"))
        sv.add_widget(self._content_box)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)
        self._populate_group()

    def _switch_group(self, key):
        self._group = key
        for k, chip in self._group_chips.items():
            chip.is_active = (k == key)
        self._populate_group()

    def _populate_group(self):
        box = self._content_box
        box.clear_widgets()
        info  = self.GROUPS[self._group]
        units = info["units"]
        accent = info["accent"]
        self._from_unit = units[0][0]
        self._rows = {}

        # from-chips
        from_lbl = MDLabel(text="FROM", font_style="Overline",
                           theme_text_color="Custom",
                           text_color=self.subtitle_color,
                           size_hint_y=None, height=dp(22))
        box.add_widget(from_lbl)

        chip_sv = ScrollView(size_hint_y=None, height=dp(40),
                             do_scroll_x=True, do_scroll_y=False,
                             bar_width=0)
        chip_row = BoxLayout(size_hint_x=None, spacing=dp(6),
                             padding=[dp(2), dp(2)])
        chip_row.bind(minimum_width=chip_row.setter("width"))
        self._chips = {}
        for label, _ in units:
            chip = UnitChip(chip_text=label, accent=accent)
            chip.is_active = (label == self._from_unit)
            chip.bind(on_release=lambda c, l=label: self._select(l))
            chip_row.add_widget(chip)
            self._chips[label] = chip
        chip_sv.add_widget(chip_row)
        box.add_widget(chip_sv)

        # input field
        inp_box = RoundBox(bg_color=self.card_bg,
                           box_radius=[16, 16, 16, 16],
                           size_hint_y=None, height=dp(72),
                           padding=[dp(14), dp(10)])
        row = BoxLayout(spacing=dp(8))
        self._input = MDTextField(
            hint_text="Enter value…",
            mode="rectangle",
            line_color_focus=accent,
            line_color_normal=[0.2, 0.2, 0.2, 1],
            text_color_normal=self.text_color,
            text_color_focus=self.text_color,
            hint_text_color_normal=self.subtitle_color,
            fill_color_normal=self.card_bg,
            fill_color_focus=self.card_bg,
            font_size=dp(15),
            input_filter="float",
        )
        self._input.bind(text=lambda inst, val: self._do_convert(val))
        paste_btn = FlatIconBtn(icon="content-paste",
                                btn_bg=accent[:3] + [0.13],
                                icon_color=accent,
                                btn_radius=10,
                                size=(dp(46), dp(46)))
        paste_btn.bind(on_release=lambda *_: self._paste())
        row.add_widget(self._input)
        row.add_widget(paste_btn)
        inp_box.add_widget(row)
        box.add_widget(inp_box)

        # results
        res_lbl = MDLabel(text="TO — ALL UNITS", font_style="Overline",
                          theme_text_color="Custom",
                          text_color=self.subtitle_color,
                          size_hint_y=None, height=dp(22))
        box.add_widget(res_lbl)

        res_box = RoundBox(bg_color=self.card_bg,
                           box_radius=[16, 16, 16, 16],
                           size_hint_y=None)
        res_box.bind(minimum_height=res_box.setter("height"))
        res_col = BoxLayout(orientation="vertical", spacing=dp(8),
                            size_hint_y=None, padding=[dp(14), dp(10)])
        res_col.bind(minimum_height=res_col.setter("height"))
        colors = [
            [0.0, 0.85, 0.72, 1], [1.0, 0.75, 0.2, 1], [0.55, 0.55, 1.0, 1],
            [1.0, 0.45, 0.45, 1], [0.3, 0.75, 1.0, 1],
        ]
        for i, (label, _) in enumerate(units):
            r = BaseRow(base_label=label,
                        base_color=colors[i % len(colors)],
                        text_color=self.text_color)
            res_col.add_widget(r)
            self._rows[label] = r
        res_box.add_widget(res_col)
        box.add_widget(res_box)
        box.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))

    def _select(self, label):
        self._from_unit = label
        for l, chip in self._chips.items():
            chip.is_active = (l == label)
        self._do_convert(self._input.text)

    def _paste(self):
        text = Clipboard.paste()
        if text:
            self._input.text = text.strip()
        else:
            _snack("Clipboard is empty")

    def _do_convert(self, raw):
        raw = (raw or "").strip()
        units = self.GROUPS[self._group]["units"]
        factors = {l: f for l, f in units}
        if not raw:
            for r in self._rows.values():
                r.set_value("—")
            return
        try:
            val = float(raw)
        except ValueError:
            for r in self._rows.values():
                r.set_value("error")
            return
        from_f = factors[self._from_unit]
        for label, _ in units:
            if label == self._from_unit:
                self._rows[label].set_value(_fmt_num(val))
            else:
                self._rows[label].set_value(_fmt_num(val * from_f / factors[label]))


def _fmt_num(num):
    """Shared float formatter for ad-hoc screens."""
    s = f"{num:.12f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


# ── Magnetic Field ─────────────────────────────────────────────────
class MagneticScreen(GenericUnitScreen):
    TITLE  = "Magnetic Field"
    ACCENT = [1.0, 0.4, 0.7, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("T",   1.0),
        ("mT",  1e-3),
        ("µT",  1e-6),
        ("nT",  1e-9),
        ("G",   1e-4),      # Gauss
        ("mG",  1e-7),
        ("Oe",  79.5775),   # Oersted (H-field, approx in vacuum)
    ]

# ── Illuminance ────────────────────────────────────────────────────
class IlluminanceScreen(GenericUnitScreen):
    TITLE  = "Illuminance"
    ACCENT = [1.0, 0.92, 0.3, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("lux",  1.0),
        ("fc",   10.7639),   # foot-candle
        ("phot", 10000.0),
        ("nox",  0.001),
        ("lm/m²", 1.0),      # same as lux
        ("lm/ft²", 10.7639),
        ("lm/cm²", 10000.0),
    ]

# ── Luminance ──────────────────────────────────────────────────────
class LuminanceScreen(GenericUnitScreen):
    TITLE  = "Luminance"
    ACCENT = [1.0, 0.75, 0.2, 1]
    FMT    = ":.6g"
    UNITS  = [
        ("cd/m²", 1.0),       # = nit
        ("nit",   1.0),
        ("fL",    3.42626),   # foot-lambert
        ("L",     3183.099),  # lambert
        ("sb",    10000.0),   # stilb
        ("mcd/m²", 1e-3),
        ("kcd/m²", 1e3),
    ]

# ── Radioactivity ──────────────────────────────────────────────────
class RadioactivityScreen(GenericUnitScreen):
    TITLE  = "Radioactivity"
    ACCENT = [0.6, 1.0, 0.3, 1]
    FMT    = ":.6g"
    # Two physical quantities here – activity (Bq/Ci) and dose (Gy/Sv/Rad/Rem).
    # We keep them as-is with linear factors (same dimension only converts cleanly
    # within its sub-group, but listing them together is what most converter apps do).
    UNITS  = [
        # Activity
        ("Bq",    1.0),
        ("kBq",   1e3),
        ("MBq",   1e6),
        ("GBq",   1e9),
        ("Ci",    3.7e10),
        ("mCi",   3.7e7),
        ("µCi",   3.7e4),
        ("Rd",    1e6),      # Rutherford
        # Absorbed dose (base = Gy = J/kg)
        ("Gy",    1.0),
        ("mGy",   1e-3),
        ("rad",   0.01),
        # Dose equivalent (base = Sv)
        ("Sv",    1.0),
        ("mSv",   1e-3),
        ("µSv",   1e-6),
        ("rem",   0.01),
        ("mrem",  1e-4),
    ]
    # Note: cross-group conversions (Bq ↔ Gy) are not physically meaningful
    # without source info; they'll produce a number but carry a warning.

# ── Sound Level ────────────────────────────────────────────────────
class SoundScreen(GenericUnitScreen):
    TITLE  = "Sound Level"
    ACCENT = [0.9, 0.6, 0.2, 1]
    FMT    = ":.4f"
    # dB is logarithmic; we store linear power ratios relative to 1 W reference
    # and do log conversions in _convert.
    UNITS  = [
        ("dB",   0),    # placeholder – converted via log math
        ("dBm",  0),    # ref 1 mW
        ("dBW",  0),    # ref 1 W
        ("Np",   0),    # neper (natural log)
    ]
    def _convert(self, val, from_u, to_u):
        # Convert everything to dBW first, then out
        if   from_u == "dB":   dbw = val         # treat dB as dBW for reference
        elif from_u == "dBm":  dbw = val - 30.0
        elif from_u == "dBW":  dbw = val
        elif from_u == "Np":   dbw = val * 20.0 / math.log(10)
        else: dbw = val
        if   to_u == "dB":   return dbw
        elif to_u == "dBm":  return dbw + 30.0
        elif to_u == "dBW":  return dbw
        elif to_u == "Np":   return dbw * math.log(10) / 20.0
        return dbw

# ── Typography ─────────────────────────────────────────────────────
class TypographyScreen(GenericUnitScreen):
    TITLE  = "Typography"
    ACCENT = [0.4, 0.9, 0.85, 1]
    FMT    = ":.4f"
    # Base = px at 96 dpi (CSS default)
    UNITS  = [
        ("px",   1.0),
        ("pt",   96/72),          # 1 pt = 1/72 in → at 96dpi = 96/72 px
        ("pc",   16.0),           # 1 pica = 12 pt
        ("in",   96.0),           # 1 in = 96 px at 96 dpi
        ("cm",   96/2.54),
        ("mm",   96/25.4),
        ("em",   16.0),           # 1 em = 16 px (browser default)
        ("rem",  16.0),
        ("dp",   1.0),            # density-independent px (Android default 1:1 at mdpi)
        ("sp",   1.0),            # scale-independent px (same as dp baseline)
    ]

# ── Color Codes (custom screen) ─────────────────────────────────────
class ColorScreen(ConverterScreen):
    """HEX ↔ RGB ↔ HSL ↔ CMYK converter."""

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()

        root_box = BoxLayout(orientation="vertical")

        # top bar
        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        title_lbl = MDLabel(text="Color Codes", font_style="H6",
                            theme_text_color="Custom",
                            text_color=self.header_color,
                            bold=True, valign="center")
        top.add_widget(back)
        top.add_widget(title_lbl)
        root_box.add_widget(top)

        sv = ScrollView()
        content = BoxLayout(orientation="vertical",
                            padding=[dp(14), dp(8)],
                            spacing=dp(14), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        accent = [1.0, 0.5, 0.8, 1]

        # ── HEX input ──
        content.add_widget(MDLabel(
            text="HEX", font_style="Overline",
            theme_text_color="Custom", text_color=self.subtitle_color,
            size_hint_y=None, height=dp(22)))
        hex_box = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                           size_hint_y=None, height=dp(68),
                           padding=[dp(14), dp(8)])
        hex_row = BoxLayout(spacing=dp(8))
        self._hex_input = MDTextField(
            hint_text="#RRGGBB or RRGGBB",
            mode="rectangle",
            line_color_focus=accent,
            line_color_normal=[0.2, 0.2, 0.2, 1],
            text_color_normal=self.text_color,
            text_color_focus=self.text_color,
            hint_text_color_normal=self.subtitle_color,
            fill_color_normal=self.card_bg,
            fill_color_focus=self.card_bg,
            font_size=dp(15),
        )
        self._hex_input.bind(text=self._on_hex_change)
        paste_btn = FlatIconBtn(icon="content-paste",
                                btn_bg=accent[:3] + [0.13],
                                icon_color=accent,
                                btn_radius=10, size=(dp(46), dp(46)))
        paste_btn.bind(on_release=lambda *_: self._paste_hex())
        hex_row.add_widget(self._hex_input)
        hex_row.add_widget(paste_btn)
        hex_box.add_widget(hex_row)
        content.add_widget(hex_box)

        # ── colour preview swatch ──
        self._swatch = BoxLayout(size_hint_y=None, height=dp(50))
        from kivy.graphics import Color as KColor, RoundedRectangle as KRR
        with self._swatch.canvas.before:
            self._swatch_color = KColor(0.2, 0.2, 0.2, 1)
            self._swatch_rect  = KRR(pos=self._swatch.pos,
                                     size=self._swatch.size,
                                     radius=[10]*4)
        self._swatch.bind(
            pos=lambda w, v: setattr(self._swatch_rect, 'pos', v),
            size=lambda w, v: setattr(self._swatch_rect, 'size', v))
        content.add_widget(self._swatch)

        # ── result cards ──
        results_data = [
            ("RGB",  "rgb",  [0.0, 0.85, 0.72, 1]),
            ("HSL",  "hsl",  [0.55, 0.55, 1.0, 1]),
            ("CMYK", "cmyk", [1.0, 0.75, 0.2, 1]),
            ("HSV",  "hsv",  [1.0, 0.45, 0.45, 1]),
        ]
        self._result_labels = {}
        for title, key, col in results_data:
            card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                            size_hint_y=None, height=dp(62),
                            padding=[dp(14), dp(8)])
            row = BoxLayout(spacing=dp(10))
            lbl_title = MDLabel(text=title, font_style="Subtitle2",
                                theme_text_color="Custom",
                                text_color=col, bold=True,
                                size_hint_x=None, width=dp(46))
            lbl_val = MDLabel(text="—", font_style="Body2",
                              theme_text_color="Custom",
                              text_color=self.text_color)
            copy_btn = FlatIconBtn(icon="content-copy",
                                   btn_bg=col[:3] + [0.12],
                                   icon_color=col,
                                   btn_radius=8, size=(dp(32), dp(32)))
            copy_btn.bind(on_release=lambda *_, k=key: self._copy_result(k))
            row.add_widget(lbl_title)
            row.add_widget(lbl_val)
            row.add_widget(copy_btn)
            card.add_widget(row)
            content.add_widget(card)
            self._result_labels[key] = lbl_val

        content.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(content)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)
        text = Clipboard.paste()
        if text:
            self._hex_input.text = text.strip()
        else:
            _snack("Clipboard is empty")

    def _copy_result(self, key):
        lbl = self._result_labels.get(key)
        if lbl and lbl.text not in ("—", "error"):
            Clipboard.copy(lbl.text)
            _snack(f"Copied: {lbl.text[:40]}")
        else:
            _snack("Nothing to copy")

    def _on_hex_change(self, inst, value):
        raw = value.strip().lstrip("#")
        if len(raw) not in (3, 6):
            for lbl in self._result_labels.values():
                lbl.text = "—"
            self._swatch_color.rgba = (0.15, 0.15, 0.15, 1)
            return
        try:
            if len(raw) == 3:
                raw = raw[0]*2 + raw[1]*2 + raw[2]*2
            r = int(raw[0:2], 16)
            g = int(raw[2:4], 16)
            b = int(raw[4:6], 16)
        except ValueError:
            for lbl in self._result_labels.values():
                lbl.text = "error"
            return

        rf, gf, bf = r/255, g/255, b/255
        self._swatch_color.rgba = (rf, gf, bf, 1)

        # RGB
        self._result_labels["rgb"].text = f"rgb({r}, {g}, {b})"

        # HSL
        cmax = max(rf, gf, bf); cmin = min(rf, gf, bf); delta = cmax - cmin
        l_val = (cmax + cmin) / 2
        s_val = 0 if delta == 0 else delta / (1 - abs(2*l_val - 1))
        if delta == 0:   h_val = 0
        elif cmax == rf: h_val = 60 * (((gf - bf) / delta) % 6)
        elif cmax == gf: h_val = 60 * (((bf - rf) / delta) + 2)
        else:            h_val = 60 * (((rf - gf) / delta) + 4)
        self._result_labels["hsl"].text = (
            f"hsl({h_val:.1f}, {s_val*100:.1f}%, {l_val*100:.1f}%)")

        # HSV
        v_val = cmax
        sv_val = 0 if cmax == 0 else delta / cmax
        self._result_labels["hsv"].text = (
            f"hsv({h_val:.1f}, {sv_val*100:.1f}%, {v_val*100:.1f}%)")

        # CMYK
        if cmax == 0:
            self._result_labels["cmyk"].text = "cmyk(0%, 0%, 0%, 100%)"
        else:
            k_cmyk = 1 - cmax
            c_cmyk = (1 - rf - k_cmyk) / (1 - k_cmyk)
            m_cmyk = (1 - gf - k_cmyk) / (1 - k_cmyk)
            y_cmyk = (1 - bf - k_cmyk) / (1 - k_cmyk)
            self._result_labels["cmyk"].text = (
                f"cmyk({c_cmyk*100:.1f}%, {m_cmyk*100:.1f}%,"
                f" {y_cmyk*100:.1f}%, {k_cmyk*100:.1f}%)")


# ── Cooking (dedicated screen with logical grouping) ────────────────
class CookingScreen(GenericUnitScreen):
    TITLE  = "Cooking"
    ACCENT = [1.0, 0.55, 0.25, 1]
    FMT    = ":.5g"
    # Base = mL
    UNITS  = [
        ("mL",       1.0),
        ("L",        1000.0),
        ("tsp",      4.92892),
        ("tbsp",     14.7868),
        ("fl oz",    29.5735),
        ("cup",      236.588),
        ("pt",       473.176),
        ("qt",       946.353),
        ("gal",      3785.41),
        ("mL (UK)",  1.0),
        ("tsp (UK)", 5.91939),
        ("tbsp (UK)",17.7582),
        ("cup (UK)", 284.131),
        # Weight (via water density approximation)
        ("g",        1.0),
        ("kg",       1000.0),
        ("oz",       28.3495),
        ("lb",       453.592),
    ]

# ── Clothing & Shoe Size (lookup table, custom screen) ──────────────
_CLOTHING_DATA = {
    "Women's Tops": {
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "US":    ["0–2", "4–6", "8–10", "12–14", "16–18", "20"],
        "EU":    ["32–34", "36–38", "40–42", "44–46", "48–50", "52"],
        "UK":    ["4–6", "8–10", "12–14", "16–18", "20–22", "24"],
        "IT":    ["36–38", "40–42", "44–46", "48–50", "52–54", "56"],
    },
    "Men's Tops": {
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "US":    ["34–36", "38–40", "42–44", "46–48", "50–52", "54–56"],
        "EU":    ["44–46", "48–50", "52–54", "56–58", "60–62", "64–66"],
        "UK":    ["34–36", "38–40", "42–44", "46–48", "50–52", "54–56"],
        "IT":    ["44–46", "48–50", "52–54", "56–58", "60–62", "64–66"],
    },
    "Women's Shoes": {
        "sizes": ["5", "5.5", "6", "6.5", "7", "7.5", "8", "8.5", "9", "10"],
        "US":    ["5",   "5.5", "6",   "6.5", "7",   "7.5", "8",   "8.5", "9",   "10"],
        "EU":    ["35",  "35.5","36",  "37",  "37.5","38",  "38.5","39",  "40",  "41"],
        "UK":    ["2.5", "3",   "3.5", "4",   "4.5", "5",   "5.5", "6",   "6.5", "7.5"],
        "JP":    ["22",  "22",  "23",  "23",  "23.5","24",  "24",  "24.5","25",  "25.5"],
    },
    "Men's Shoes": {
        "sizes": ["6", "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "12"],
        "US":    ["6",  "7",  "7.5", "8",  "8.5", "9",  "9.5", "10", "10.5","11", "12"],
        "EU":    ["39", "40", "40.5","41", "42",  "42.5","43",  "44", "44.5","45", "46"],
        "UK":    ["5.5","6",  "6.5", "7",  "7.5", "8",  "8.5", "9",  "9.5", "10", "11"],
        "JP":    ["24", "25", "25",  "26", "26.5","27",  "27",  "28", "28",  "28.5","29"],
    },
    "Bra Sizes": {
        "sizes": ["28A","28B","28C","28D","30A","30B","30C","30D","32A","32B","32C","32D",
                  "34A","34B","34C","34D","36A","36B","36C","36D","38B","38C","38D","38DD"],
        "US":    ["28A","28B","28C","28D","30A","30B","30C","30D","32A","32B","32C","32D",
                  "34A","34B","34C","34D","36A","36B","36C","36D","38B","38C","38D","38E"],
        "EU":    ["60A","60B","60C","60D","65A","65B","65C","65D","70A","70B","70C","70D",
                  "75A","75B","75C","75D","80A","80B","80C","80D","85B","85C","85D","85E"],
        "UK":    ["28A","28B","28C","28D","30A","30B","30C","30D","32A","32B","32C","32D",
                  "34A","34B","34C","34D","36A","36B","36C","36D","38B","38C","38D","38DD"],
    },
}

class ClothingScreen(ConverterScreen):
    _category = "Women's Tops"

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        root_box = BoxLayout(orientation="vertical")

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        lbl = MDLabel(text="Clothing & Shoe Size", font_style="H6",
                      theme_text_color="Custom", text_color=self.header_color,
                      bold=True, valign="center")
        top.add_widget(back)
        top.add_widget(lbl)
        root_box.add_widget(top)

        # category chips
        accent = [0.85, 0.4, 0.9, 1]
        chip_sv = ScrollView(size_hint_y=None, height=dp(44),
                             do_scroll_x=True, do_scroll_y=False, bar_width=0)
        chip_row = BoxLayout(size_hint_x=None, spacing=dp(6),
                             padding=[dp(10), dp(4)])
        chip_row.bind(minimum_width=chip_row.setter("width"))
        self._cat_chips = {}
        for cat in _CLOTHING_DATA:
            chip = UnitChip(chip_text=cat, accent=accent)
            chip.is_active = (cat == self._category)
            chip.bind(on_release=lambda c, k=cat: self._switch_cat(k))
            chip_row.add_widget(chip)
            self._cat_chips[cat] = chip
        chip_sv.add_widget(chip_row)
        root_box.add_widget(chip_sv)

        sv = ScrollView()
        self._table_box = BoxLayout(orientation="vertical",
                                    padding=[dp(14), dp(8)],
                                    spacing=dp(10), size_hint_y=None)
        self._table_box.bind(minimum_height=self._table_box.setter("height"))
        sv.add_widget(self._table_box)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)
        self._render_table()

    def _switch_cat(self, key):
        self._category = key
        for k, chip in self._cat_chips.items():
            chip.is_active = (k == key)
        self._render_table()

    def _render_table(self):
        box = self._table_box
        box.clear_widgets()
        data = _CLOTHING_DATA[self._category]
        systems = [k for k in data if k != "sizes"]
        accent = [0.85, 0.4, 0.9, 1]
        colors_map = {
            "US": [0.0, 0.85, 0.72, 1],
            "EU": [1.0, 0.75, 0.2, 1],
            "UK": [0.55, 0.55, 1.0, 1],
            "JP": [1.0, 0.45, 0.45, 1],
            "IT": [0.3, 0.75, 1.0, 1],
        }
        card = RoundBox(bg_color=self.card_bg, box_radius=[16]*4,
                        size_hint_y=None, padding=[dp(10), dp(10)])
        card.bind(minimum_height=card.setter("height"))
        col = BoxLayout(orientation="vertical", spacing=dp(6),
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        # Header row
        hdr = BoxLayout(size_hint_y=None, height=dp(30))
        hdr.add_widget(MDLabel(text="SIZE", font_style="Caption",
                               theme_text_color="Custom",
                               text_color=self.subtitle_color,
                               bold=True, size_hint_x=None, width=dp(42),
                               halign="center"))
        for sys in systems:
            c = colors_map.get(sys, accent)
            hdr.add_widget(MDLabel(text=sys, font_style="Caption",
                                   theme_text_color="Custom",
                                   text_color=c, bold=True,
                                   halign="center"))
        col.add_widget(hdr)

        for i, sz in enumerate(data["sizes"]):
            row = BoxLayout(size_hint_y=None, height=dp(34))
            row_bg = [0.12, 0.12, 0.14, 1] if i % 2 == 0 else self.card_bg
            _bind_rr(row, 'card', rad=8)
            sz_lbl = MDLabel(text=sz, font_style="Body2",
                             theme_text_color="Custom",
                             text_color=self.header_color,
                             bold=True, halign="center",
                             size_hint_x=None, width=dp(42))
            row.add_widget(sz_lbl)
            for sys in systems:
                val = data[sys][i] if i < len(data[sys]) else "—"
                row.add_widget(MDLabel(text=val, font_style="Body2",
                                       theme_text_color="Custom",
                                       text_color=self.text_color,
                                       halign="center"))
            col.add_widget(row)

        card.add_widget(col)
        box.add_widget(card)
        box.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))


# ── Paper Sizes ─────────────────────────────────────────────────────
_PAPER_SIZES_MM = {
    # ISO A series
    "A0":  (841, 1189), "A1":  (594, 841),  "A2":  (420, 594),
    "A3":  (297, 420),  "A4":  (210, 297),  "A5":  (148, 210),
    "A6":  (105, 148),  "A7":  (74, 105),
    # ISO B series
    "B0":  (1000, 1414),"B1":  (707, 1000), "B2":  (500, 707),
    "B3":  (353, 500),  "B4":  (250, 353),  "B5":  (176, 250),
    # North American
    "Letter":    (216, 279),  "Legal":  (216, 356),
    "Tabloid":   (279, 432),  "Ledger": (432, 279),
    "Executive": (184, 267),  "Half Letter": (140, 216),
    # Other
    "C4 Envelope": (229, 324), "C5 Envelope": (162, 229),
    "DL Envelope": (110, 220),
}

class PaperSizeScreen(ConverterScreen):
    _unit = "mm"

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.8, 0.4, 1.0, 1]
        root_box = BoxLayout(orientation="vertical")

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        lbl = MDLabel(text="Paper Sizes", font_style="H6",
                      theme_text_color="Custom", text_color=self.header_color,
                      bold=True, valign="center")
        top.add_widget(back)
        top.add_widget(lbl)
        root_box.add_widget(top)

        # unit chips
        chip_row = BoxLayout(size_hint_y=None, height=dp(44),
                             padding=[dp(14), dp(4)], spacing=dp(8))
        self._unit_chips = {}
        for u in ["mm", "cm", "in", "px (96dpi)"]:
            chip = BaseChip(chip_text=u, accent=accent,
                            is_active=(u == self._unit))
            chip.bind(on_release=lambda c, v=u: self._switch_unit(v))
            chip_row.add_widget(chip)
            self._unit_chips[u] = chip
        root_box.add_widget(chip_row)

        sv = ScrollView()
        self._rows_box = BoxLayout(orientation="vertical",
                                   padding=[dp(14), dp(8)],
                                   spacing=dp(8), size_hint_y=None)
        self._rows_box.bind(minimum_height=self._rows_box.setter("height"))
        sv.add_widget(self._rows_box)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)
        self._render_table()

    def _switch_unit(self, u):
        self._unit = u
        for k, chip in self._unit_chips.items():
            chip.is_active = (k == u)
        self._render_table()

    def _mm_to(self, val_mm, unit):
        if unit == "mm":            return val_mm
        elif unit == "cm":          return val_mm / 10
        elif unit == "in":          return val_mm / 25.4
        elif unit == "px (96dpi)":  return round(val_mm / 25.4 * 96)
        return val_mm

    def _render_table(self):
        box = self._rows_box
        box.clear_widgets()
        accent = [0.8, 0.4, 1.0, 1]
        colors = [
            [0.0, 0.85, 0.72, 1], [1.0, 0.75, 0.2, 1], [0.55, 0.55, 1.0, 1],
            [1.0, 0.45, 0.45, 1], [0.3, 0.75, 1.0, 1], [0.8, 0.4, 1.0, 1],
        ]
        u = self._unit
        for i, (name, (w_mm, h_mm)) in enumerate(_PAPER_SIZES_MM.items()):
            w = self._mm_to(w_mm, u)
            h = self._mm_to(h_mm, u)
            fmt = "{:.1f}" if u in ("mm", "cm", "in") else "{}"
            dim = f"{fmt.format(w)} × {fmt.format(h)} {u}"
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            col = colors[i % len(colors)]
            name_lbl = MDLabel(text=name, font_style="Body2",
                               theme_text_color="Custom",
                               text_color=col, bold=True,
                               size_hint_x=None, width=dp(110))
            dim_lbl  = MDLabel(text=dim, font_style="Body2",
                               theme_text_color="Custom",
                               text_color=self.text_color)
            copy_btn = FlatIconBtn(icon="content-copy",
                                   btn_bg=col[:3] + [0.12],
                                   icon_color=col,
                                   btn_radius=8, size=(dp(32), dp(32)))
            copy_btn.bind(on_release=lambda *_, d=dim: (
                Clipboard.copy(d), _snack(f"Copied: {d}")))
            row.add_widget(name_lbl)
            row.add_widget(dim_lbl)
            row.add_widget(copy_btn)
            box.add_widget(row)
        box.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))


# ════════════════════════════════════════════════════════════════════
# PHASE 7 NEW MODULES
# ════════════════════════════════════════════════════════════════════

# ── Time Zones ──────────────────────────────────────────────────────
_TIMEZONES = [
    ("UTC",       0,    "Universal"),
    ("GMT",       0,    "London (GMT)"),
    ("BST",       1,    "London (BST)"),
    ("CET",       1,    "Paris / Berlin"),
    ("CEST",      2,    "Paris / Berlin (Summer)"),
    ("EET",       2,    "Athens / Helsinki"),
    ("MSK",       3,    "Moscow"),
    ("GST",       4,    "Dubai / Abu Dhabi"),
    ("PKT",       5,    "Karachi"),
    ("IST",       5.5,  "India"),
    ("BST+6",     6,    "Dhaka"),
    ("WIB",       7,    "Jakarta"),
    ("CST+8",     8,    "Beijing / Singapore"),
    ("JST",       9,    "Tokyo"),
    ("AEST",      10,   "Sydney"),
    ("NZST",      12,   "Auckland"),
    ("EST",       -5,   "New York"),
    ("EDT",       -4,   "New York (Summer)"),
    ("CST",       -6,   "Chicago"),
    ("MST",       -7,   "Denver"),
    ("PST",       -8,   "Los Angeles"),
    ("PDT",       -7,   "Los Angeles (Summer)"),
    ("AKST",      -9,   "Anchorage"),
    ("HST",       -10,  "Honolulu"),
    ("ART",       -3,   "Buenos Aires"),
    ("BRT",       -3,   "Brasília"),
    ("CAT",       2,    "Nairobi / Harare"),
    ("WAT",       1,    "Lagos"),
    ("SGT",       8,    "Singapore"),
    ("HKT",       8,    "Hong Kong"),
]

class TimeZoneScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.3, 0.75, 1.0, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Time Zones', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        # Input row — UTC time entry
        inp_box = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                           size_hint_y=None, height=dp(72), padding=[dp(14), dp(10)])
        inp_row = BoxLayout(spacing=dp(8))
        self._time_inp = MDTextField(
            hint_text='Enter UTC time  e.g. 14:30',
            mode='rectangle',
            line_color_focus=accent,
            line_color_normal=[0.2, 0.2, 0.2, 1],
            text_color_normal=self.text_color,
            text_color_focus=self.text_color,
            hint_text_color_normal=self.subtitle_color,
            fill_color_normal=self.card_bg,
            fill_color_focus=self.card_bg,
            font_size=dp(15),
        )
        self._time_inp.bind(text=lambda *_: self._convert())
        now_btn = FlatIconBtn(icon='clock-outline', btn_bg=list(accent[:3]) + [0.13],
                              icon_color=accent, btn_radius=10, size=(dp(46), dp(46)))
        now_btn.bind(on_release=lambda *_: self._set_now())
        inp_row.add_widget(self._time_inp)
        inp_row.add_widget(now_btn)
        inp_box.add_widget(inp_row)
        root_box.add_widget(inp_box)

        root_box.add_widget(MDLabel(text='ALL TIME ZONES', font_style='Overline',
                                    theme_text_color='Custom', text_color=self.subtitle_color,
                                    size_hint_y=None, height=dp(26),
                                    padding=[dp(14), 0]))

        sv = ScrollView()
        self._col = BoxLayout(orientation='vertical', spacing=dp(6),
                              padding=[dp(14), dp(4)], size_hint_y=None)
        self._col.bind(minimum_height=self._col.setter('height'))

        colors = [[0.3, 0.75, 1.0, 1], [0.0, 0.85, 0.72, 1], [0.8, 0.5, 1.0, 1],
                  [1.0, 0.75, 0.2, 1], [1.0, 0.45, 0.45, 1], [0.4, 1.0, 0.6, 1]]
        self._tz_rows = {}
        from kivy.graphics import Color as _GC, RoundedRectangle as _GRR
        for i, (code, offset, city) in enumerate(_TIMEZONES):
            col = colors[i % len(colors)]
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(52),
                            padding=[dp(10), dp(6)], spacing=dp(8))
            with row.canvas.before:
                _GC(*list(col[:3]) + [0.10])
                _rr = _GRR(pos=row.pos, size=row.size, radius=[10])
            row.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                     size=lambda w, v, r=_rr: setattr(r, 'size', v))

            off_str = f"UTC{'+' if offset >= 0 else ''}{offset:g}"
            lbl_code = MDLabel(text=code, font_style='Caption', theme_text_color='Custom',
                               text_color=col, bold=True, size_hint=(None, 1), width=dp(52))
            lbl_city = MDLabel(text=city, font_style='Caption', theme_text_color='Custom',
                               text_color=self.subtitle_color, size_hint=(None, 1), width=dp(130))
            lbl_time = MDLabel(text='—', font_style='Body1', theme_text_color='Custom',
                               text_color=self.text_color, bold=True, halign='right')
            off_lbl  = MDLabel(text=off_str, font_style='Caption', theme_text_color='Custom',
                               text_color=self.subtitle_color, size_hint=(None, 1), width=dp(52),
                               halign='right')
            copy_btn = FlatIconBtn(icon='content-copy', btn_bg=[0,0,0,0],
                                   icon_color=list(col[:3]) + [0.6], btn_radius=6,
                                   size=(dp(28), dp(28)))
            copy_btn.bind(on_release=lambda *_, l=lbl_time, c=code: (
                Clipboard.copy(l.text), _snack(f"Copied {c}: {l.text}")))

            row.add_widget(lbl_code)
            row.add_widget(lbl_city)
            row.add_widget(lbl_time)
            row.add_widget(off_lbl)
            row.add_widget(copy_btn)
            self._col.add_widget(row)
            self._tz_rows[code] = (lbl_time, offset)

        self._col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(self._col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _set_now(self):
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        self._time_inp.text = now_utc.strftime('%H:%M')

    def _convert(self):
        raw = self._time_inp.text.strip()
        try:
            parts = raw.replace('.', ':').split(':')
            h = int(parts[0]) % 24
            m = int(parts[1]) if len(parts) > 1 else 0
            utc_minutes = h * 60 + m
            for code, (lbl, offset) in self._tz_rows.items():
                total = (utc_minutes + int(offset * 60)) % (24 * 60)
                lh, lm = divmod(total, 60)
                lbl.text = f'{lh:02d}:{lm:02d}'
        except Exception:
            for code, (lbl, offset) in self._tz_rows.items():
                lbl.text = '—'


# ── Date & Age Calculator ───────────────────────────────────────────
class DateAgeScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.8, 0.5, 1.0, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Date & Age', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(12),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        def _field(hint):
            f = MDTextField(hint_text=hint, mode='rectangle',
                            line_color_focus=accent,
                            line_color_normal=[0.2, 0.2, 0.2, 1],
                            text_color_normal=self.text_color,
                            text_color_focus=self.text_color,
                            hint_text_color_normal=self.subtitle_color,
                            fill_color_normal=self.card_bg,
                            fill_color_focus=self.card_bg,
                            font_size=dp(15), size_hint_y=None, height=dp(52))
            return f

        # ── AGE CALCULATOR ──
        age_card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                            size_hint_y=None, padding=[dp(14), dp(12)])
        age_card.bind(minimum_height=age_card.setter('height'))
        age_col = BoxLayout(orientation='vertical', spacing=dp(8),
                            size_hint_y=None)
        age_col.bind(minimum_height=age_col.setter('height'))
        age_col.add_widget(MDLabel(text='AGE CALCULATOR', font_style='Overline',
                                   theme_text_color='Custom', text_color=accent,
                                   bold=True, size_hint_y=None, height=dp(22)))
        self._dob_field = _field('Date of birth  (YYYY-MM-DD or DD/MM/YYYY)')
        self._age_result = MDLabel(text='Enter date of birth above',
                                   font_style='H5', theme_text_color='Custom',
                                   text_color=self.text_color, bold=True,
                                   halign='center', size_hint_y=None, height=dp(48))
        calc_age_btn = MDRaisedButton(text='CALCULATE AGE',
                                      md_bg_color=list(accent[:3]) + [0.85],
                                      theme_text_color='Custom',
                                      text_color=[0,0,0,1],
                                      size_hint_y=None, height=dp(44))
        calc_age_btn.bind(on_release=lambda *_: self._calc_age())
        age_col.add_widget(self._dob_field)
        age_col.add_widget(calc_age_btn)
        age_col.add_widget(self._age_result)
        age_card.add_widget(age_col)
        col.add_widget(age_card)

        # ── DATE DIFFERENCE ──
        diff_card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                             size_hint_y=None, padding=[dp(14), dp(12)])
        diff_card.bind(minimum_height=diff_card.setter('height'))
        diff_col = BoxLayout(orientation='vertical', spacing=dp(8),
                             size_hint_y=None)
        diff_col.bind(minimum_height=diff_col.setter('height'))
        diff_col.add_widget(MDLabel(text='DATE DIFFERENCE', font_style='Overline',
                                    theme_text_color='Custom', text_color=accent,
                                    bold=True, size_hint_y=None, height=dp(22)))
        self._d1_field = _field('Start date  (YYYY-MM-DD)')
        self._d2_field = _field('End date  (YYYY-MM-DD)')
        self._diff_result = MDLabel(text='Enter two dates above',
                                    font_style='Body1', theme_text_color='Custom',
                                    text_color=self.text_color, halign='center',
                                    size_hint_y=None, height=dp(60))
        calc_diff_btn = MDRaisedButton(text='CALCULATE DIFFERENCE',
                                       md_bg_color=list(accent[:3]) + [0.85],
                                       theme_text_color='Custom',
                                       text_color=[0,0,0,1],
                                       size_hint_y=None, height=dp(44))
        calc_diff_btn.bind(on_release=lambda *_: self._calc_diff())
        diff_col.add_widget(self._d1_field)
        diff_col.add_widget(self._d2_field)
        diff_col.add_widget(calc_diff_btn)
        diff_col.add_widget(self._diff_result)
        diff_card.add_widget(diff_col)
        col.add_widget(diff_card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _parse_date(self, s):
        from datetime import date
        s = s.strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
            try:
                return _dt.strptime(s, fmt).date()
            except Exception:
                pass
        return None

    def _calc_age(self):
        from datetime import date
        d = self._parse_date(self._dob_field.text)
        if not d:
            self._age_result.text = 'Invalid date format'
            return
        today = date.today()
        years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        months = (today.month - d.month - (today.day < d.day)) % 12
        days = (today - d.replace(year=today.year)).days
        if days < 0:
            days += 365
        total_days = (today - d).days
        self._age_result.text = (
            f'{years} yrs  {months} mo  ·  {total_days:,} days total'
        )

    def _calc_diff(self):
        d1 = self._parse_date(self._d1_field.text)
        d2 = self._parse_date(self._d2_field.text)
        if not d1 or not d2:
            self._diff_result.text = 'Invalid date format'
            return
        delta = abs((d2 - d1).days)
        weeks, days = divmod(delta, 7)
        months = delta // 30
        years = delta // 365
        self._diff_result.text = (
            f'{delta:,} days  ·  {weeks} weeks {days} days\n'
            f'≈ {months} months  ·  ≈ {years} years'
        )


# ── Tip Calculator ──────────────────────────────────────────────────
class TipScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.3, 0.85, 0.55, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Tip Calculator', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(12),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                        size_hint_y=None, padding=[dp(14), dp(14)])
        card.bind(minimum_height=card.setter('height'))
        inp_col = BoxLayout(orientation='vertical', spacing=dp(10),
                            size_hint_y=None)
        inp_col.bind(minimum_height=inp_col.setter('height'))

        def _tf(hint):
            return MDTextField(hint_text=hint, mode='rectangle',
                               line_color_focus=accent,
                               line_color_normal=[0.2, 0.2, 0.2, 1],
                               text_color_normal=self.text_color,
                               text_color_focus=self.text_color,
                               hint_text_color_normal=self.subtitle_color,
                               fill_color_normal=self.card_bg,
                               fill_color_focus=self.card_bg,
                               font_size=dp(15), input_filter='float',
                               size_hint_y=None, height=dp(52))

        self._bill_f   = _tf('Bill amount')
        self._tip_f    = _tf('Tip %  (e.g. 15)')
        self._split_f  = _tf('Split between  (people)')
        self._tip_f.text = '15'
        self._split_f.text = '1'

        for f in (self._bill_f, self._tip_f, self._split_f):
            f.bind(text=lambda *_: self._calc_tip())

        self._tip_result = MDLabel(text='Enter bill amount above',
                                   font_style='H6', theme_text_color='Custom',
                                   text_color=self.text_color, halign='center',
                                   size_hint_y=None, height=dp(100))

        # Quick tip % chips
        chip_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for pct in [10, 12, 15, 18, 20, 25]:
            c = BaseChip(chip_text=f'{pct}%', accent=accent, is_active=(pct == 15))
            c.bind(on_release=lambda ch, p=pct: self._set_tip_pct(p))
            chip_row.add_widget(c)
        self._tip_chips = {10: None, 12: None, 15: None, 18: None, 20: None, 25: None}

        inp_col.add_widget(self._bill_f)
        inp_col.add_widget(chip_row)
        inp_col.add_widget(self._tip_f)
        inp_col.add_widget(self._split_f)
        inp_col.add_widget(self._tip_result)
        card.add_widget(inp_col)
        col.add_widget(card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _set_tip_pct(self, pct):
        self._tip_f.text = str(pct)

    def _calc_tip(self):
        try:
            bill  = float(self._bill_f.text or 0)
            tip_p = float(self._tip_f.text or 0)
            split = max(1, int(float(self._split_f.text or 1)))
            tip_amt   = bill * tip_p / 100
            total     = bill + tip_amt
            per_head  = total / split
            tip_each  = tip_amt / split
            self._tip_result.text = (
                f'Tip:  {tip_amt:.2f}\n'
                f'Total:  {total:.2f}\n'
                f'Per person:  {per_head:.2f}  (tip {tip_each:.2f})'
            )
        except Exception:
            self._tip_result.text = '—'


# ── Discount / Percentage Calculator ───────────────────────────────
class DiscountScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [1.0, 0.55, 0.25, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Discount & %', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(14),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        def _card(title_text):
            c = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                         size_hint_y=None, padding=[dp(14), dp(12)])
            c.bind(minimum_height=c.setter('height'))
            inner = BoxLayout(orientation='vertical', spacing=dp(8),
                              size_hint_y=None)
            inner.bind(minimum_height=inner.setter('height'))
            inner.add_widget(MDLabel(text=title_text, font_style='Overline',
                                     theme_text_color='Custom', text_color=accent,
                                     bold=True, size_hint_y=None, height=dp(22)))
            c.add_widget(inner)
            return c, inner

        def _tf(hint, filt='float'):
            return MDTextField(hint_text=hint, mode='rectangle',
                               line_color_focus=accent,
                               line_color_normal=[0.2, 0.2, 0.2, 1],
                               text_color_normal=self.text_color,
                               text_color_focus=self.text_color,
                               hint_text_color_normal=self.subtitle_color,
                               fill_color_normal=self.card_bg,
                               fill_color_focus=self.card_bg,
                               font_size=dp(15), input_filter=filt,
                               size_hint_y=None, height=dp(52))

        def _res():
            return MDLabel(text='—', font_style='H5', theme_text_color='Custom',
                           text_color=self.text_color, bold=True, halign='center',
                           size_hint_y=None, height=dp(48))

        # Block 1: X% off price
        c1, i1 = _card('DISCOUNT — X% OFF')
        self._orig_f = _tf('Original price')
        self._disc_f = _tf('Discount %')
        self._disc_res = _res()
        for f in (self._orig_f, self._disc_f):
            f.bind(text=lambda *_: self._calc_disc())
        i1.add_widget(self._orig_f); i1.add_widget(self._disc_f); i1.add_widget(self._disc_res)
        col.add_widget(c1)

        # Block 2: what % is X of Y
        c2, i2 = _card('WHAT % IS X OF Y?')
        self._xof_x = _tf('X (part)')
        self._xof_y = _tf('Y (whole)')
        self._xof_res = _res()
        for f in (self._xof_x, self._xof_y):
            f.bind(text=lambda *_: self._calc_xofy())
        i2.add_widget(self._xof_x); i2.add_widget(self._xof_y); i2.add_widget(self._xof_res)
        col.add_widget(c2)

        # Block 3: % change
        c3, i3 = _card('% CHANGE (OLD → NEW)')
        self._chg_old = _tf('Old value')
        self._chg_new = _tf('New value')
        self._chg_res = _res()
        for f in (self._chg_old, self._chg_new):
            f.bind(text=lambda *_: self._calc_change())
        i3.add_widget(self._chg_old); i3.add_widget(self._chg_new); i3.add_widget(self._chg_res)
        col.add_widget(c3)

        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _calc_disc(self):
        try:
            orig = float(self._orig_f.text or 0)
            disc = float(self._disc_f.text or 0)
            saved = orig * disc / 100
            final = orig - saved
            self._disc_res.text = f'Save {saved:.2f}  →  Pay {final:.2f}'
        except Exception:
            self._disc_res.text = '—'

    def _calc_xofy(self):
        try:
            x = float(self._xof_x.text or 0)
            y = float(self._xof_y.text or 1)
            self._xof_res.text = f'{x / y * 100:.4g} %'
        except Exception:
            self._xof_res.text = '—'

    def _calc_change(self):
        try:
            old = float(self._chg_old.text or 0)
            new = float(self._chg_new.text or 0)
            change = (new - old) / old * 100
            sign = '+' if change >= 0 else ''
            self._chg_res.text = f'{sign}{change:.4g} %'
        except Exception:
            self._chg_res.text = '—'


# ── BMI / BMR Calculator ────────────────────────────────────────────
class BMIBMRScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [1.0, 0.35, 0.5, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='BMI & BMR', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(12),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                        size_hint_y=None, padding=[dp(14), dp(14)])
        card.bind(minimum_height=card.setter('height'))
        inner = BoxLayout(orientation='vertical', spacing=dp(10),
                          size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        def _tf(hint):
            return MDTextField(hint_text=hint, mode='rectangle',
                               line_color_focus=accent,
                               line_color_normal=[0.2, 0.2, 0.2, 1],
                               text_color_normal=self.text_color,
                               text_color_focus=self.text_color,
                               hint_text_color_normal=self.subtitle_color,
                               fill_color_normal=self.card_bg,
                               fill_color_focus=self.card_bg,
                               font_size=dp(15), input_filter='float',
                               size_hint_y=None, height=dp(52))

        self._h_f  = _tf('Height (cm)')
        self._w_f  = _tf('Weight (kg)')
        self._age_f = _tf('Age (years)')

        # Sex chips
        sex_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self._sex = 'M'
        self._chip_m = BaseChip(chip_text='Male',   accent=accent, is_active=True)
        self._chip_f = BaseChip(chip_text='Female', accent=accent, is_active=False)
        self._chip_m.bind(on_release=lambda *_: self._set_sex('M'))
        self._chip_f.bind(on_release=lambda *_: self._set_sex('F'))
        sex_row.add_widget(self._chip_m)
        sex_row.add_widget(self._chip_f)

        # Activity level chips
        act_lbl = MDLabel(text='ACTIVITY LEVEL', font_style='Overline',
                          theme_text_color='Custom', text_color=accent,
                          bold=True, size_hint_y=None, height=dp(22))
        act_sv = ScrollView(size_hint_y=None, height=dp(40),
                            do_scroll_x=True, do_scroll_y=False, bar_width=0)
        act_row = BoxLayout(size_hint_x=None, spacing=dp(6), padding=[dp(2), 0])
        act_row.bind(minimum_width=act_row.setter('width'))
        self._act_labels = ['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active']
        self._act_factors = [1.2, 1.375, 1.55, 1.725, 1.9]
        self._act_idx = 1
        self._act_chips = []
        for i, lbl in enumerate(self._act_labels):
            chip = UnitChip(chip_text=lbl, accent=accent, is_active=(i == 1))
            chip.bind(on_release=lambda c, idx=i: self._set_act(idx))
            act_row.add_widget(chip)
            self._act_chips.append(chip)
        act_sv.add_widget(act_row)

        calc_btn = MDRaisedButton(text='CALCULATE',
                                  md_bg_color=list(accent[:3]) + [0.85],
                                  theme_text_color='Custom', text_color=[0,0,0,1],
                                  size_hint_y=None, height=dp(44))
        calc_btn.bind(on_release=lambda *_: self._calc())

        self._result = MDLabel(text='Enter your details above',
                               font_style='Body1', theme_text_color='Custom',
                               text_color=self.text_color, halign='center',
                               size_hint_y=None, height=dp(120))

        for w in (MDLabel(text='BMI / BMR CALCULATOR', font_style='Overline',
                          theme_text_color='Custom', text_color=accent,
                          bold=True, size_hint_y=None, height=dp(22)),
                  self._h_f, self._w_f, self._age_f,
                  MDLabel(text='SEX', font_style='Overline',
                          theme_text_color='Custom', text_color=self.subtitle_color,
                          bold=True, size_hint_y=None, height=dp(20)),
                  sex_row, act_lbl, act_sv, calc_btn, self._result):
            inner.add_widget(w)

        card.add_widget(inner)
        col.add_widget(card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _set_sex(self, s):
        self._sex = s
        self._chip_m.is_active = (s == 'M')
        self._chip_f.is_active = (s == 'F')

    def _set_act(self, idx):
        self._act_idx = idx
        for i, c in enumerate(self._act_chips):
            c.is_active = (i == idx)

    def _calc(self):
        try:
            h  = float(self._h_f.text)
            w  = float(self._w_f.text)
            a  = float(self._age_f.text)
            h_m = h / 100
            bmi = w / (h_m ** 2)
            if bmi < 18.5:   cat = 'Underweight'
            elif bmi < 25:   cat = 'Normal weight'
            elif bmi < 30:   cat = 'Overweight'
            else:            cat = 'Obese'
            # Mifflin-St Jeor BMR
            if self._sex == 'M':
                bmr = 10*w + 6.25*h - 5*a + 5
            else:
                bmr = 10*w + 6.25*h - 5*a - 161
            tdee = bmr * self._act_factors[self._act_idx]
            self._result.text = (
                f'BMI: {bmi:.1f}  ({cat})\n'
                f'BMR: {bmr:.0f} kcal/day\n'
                f'TDEE: {tdee:.0f} kcal/day\n'
                f'({self._act_labels[self._act_idx]})'
            )
        except Exception:
            self._result.text = 'Enter valid numbers'


# ── Shoe Sizes ──────────────────────────────────────────────────────
_SHOE_DATA = [
    # (US M, US W, UK, EU, JP cm)
    (4,   5.5, 3,   35,  22.0),
    (4.5, 6,   3.5, 36,  22.5),
    (5,   6.5, 4,   37,  23.0),
    (5.5, 7,   4.5, 37,  23.5),
    (6,   7.5, 5,   38,  24.0),
    (6.5, 8,   5.5, 39,  24.5),
    (7,   8.5, 6,   40,  25.0),
    (7.5, 9,   6.5, 40,  25.5),
    (8,   9.5, 7,   41,  26.0),
    (8.5, 10,  7.5, 42,  26.5),
    (9,   10.5,8,   42,  27.0),
    (9.5, 11,  8.5, 43,  27.5),
    (10,  11.5,9,   44,  28.0),
    (10.5,12,  9.5, 44,  28.5),
    (11,  12.5,10,  45,  29.0),
    (11.5,13,  10.5,46,  29.5),
    (12,  13.5,11,  46,  30.0),
    (13,  14.5,12,  47,  31.0),
    (14,  15.5,13,  48,  32.0),
]

class ShoeSizeScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.55, 0.75, 1.0, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Shoe Sizes', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(6),
                        padding=[dp(10), dp(4)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        # Header row
        hdr = BoxLayout(size_hint_y=None, height=dp(30))
        for txt, w in [('US M', 60), ('US W', 60), ('UK', 50), ('EU', 50), ('JP (cm)', 70)]:
            hdr.add_widget(MDLabel(text=txt, font_style='Caption',
                                   theme_text_color='Custom',
                                   text_color=accent, bold=True,
                                   halign='center', size_hint_x=None, width=dp(w)))
        col.add_widget(hdr)

        colors = [[0.3,0.75,1,1],[0,0.85,0.72,1],[0.8,0.5,1,1],[1,0.75,0.2,1],[1,0.45,0.45,1]]
        from kivy.graphics import Color as _GC, RoundedRectangle as _GRR
        for i, row_data in enumerate(_SHOE_DATA):
            usm, usw, uk, eu, jp = row_data
            row = BoxLayout(size_hint_y=None, height=dp(38))
            col_c = colors[i % len(colors)]
            with row.canvas.before:
                _GC(*list(col_c[:3]) + [0.08])
                _rr = _GRR(pos=row.pos, size=row.size, radius=[8])
            row.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                     size=lambda w, v, r=_rr: setattr(r, 'size', v))
            for val, w in [(f'{usm:g}', 60), (f'{usw:g}', 60), (f'{uk:g}', 50),
                           (f'{eu}', 50), (f'{jp}', 70)]:
                row.add_widget(MDLabel(text=val, font_style='Body2',
                                       theme_text_color='Custom',
                                       text_color=self.text_color,
                                       halign='center', size_hint_x=None, width=dp(w)))
            col.add_widget(row)

        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)


# ── Ring Sizes ──────────────────────────────────────────────────────
_RING_DATA = [
    # (US, UK, EU, diameter mm)
    (4,   'H', 46.8, 14.9),
    (4.5, 'I', 47.8, 15.2),
    (5,   'J', 49.3, 15.7),
    (5.5, 'K', 50.6, 16.1),
    (6,   'L', 51.9, 16.5),
    (6.5, 'M', 53.1, 16.9),
    (7,   'N', 54.4, 17.3),
    (7.5, 'O', 55.7, 17.7),
    (8,   'P', 57.0, 18.1),
    (8.5, 'Q', 58.3, 18.6),
    (9,   'R', 59.5, 18.9),
    (9.5, 'S', 60.8, 19.4),
    (10,  'T', 62.1, 19.8),
    (10.5,'U', 63.4, 20.2),
    (11,  'V', 64.6, 20.6),
    (11.5,'W', 65.9, 21.0),
    (12,  'X', 67.2, 21.4),
    (13,  'Z', 69.7, 22.2),
]

class RingSizeScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [1.0, 0.78, 0.2, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Ring Sizes', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(6),
                        padding=[dp(10), dp(4)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        hdr = BoxLayout(size_hint_y=None, height=dp(30))
        for txt, w in [('US', 50), ('UK', 50), ('EU', 55), ('Diam. mm', 80)]:
            hdr.add_widget(MDLabel(text=txt, font_style='Caption',
                                   theme_text_color='Custom',
                                   text_color=accent, bold=True,
                                   halign='center', size_hint_x=None, width=dp(w)))
        col.add_widget(hdr)

        colors = [[1,0.78,0.2,1],[0,0.85,0.72,1],[0.8,0.5,1,1],[0.3,0.75,1,1],[1,0.45,0.45,1]]
        from kivy.graphics import Color as _GC2, RoundedRectangle as _GRR2
        for i, (us, uk, eu, diam) in enumerate(_RING_DATA):
            row = BoxLayout(size_hint_y=None, height=dp(38))
            col_c = colors[i % len(colors)]
            with row.canvas.before:
                _GC2(*list(col_c[:3]) + [0.08])
                _rr = _GRR2(pos=row.pos, size=row.size, radius=[8])
            row.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
                     size=lambda w, v, r=_rr: setattr(r, 'size', v))
            for val, w in [(f'{us:g}', 50), (uk, 50), (f'{eu}', 55), (f'{diam}', 80)]:
                row.add_widget(MDLabel(text=str(val), font_style='Body2',
                                       theme_text_color='Custom',
                                       text_color=self.text_color,
                                       halign='center', size_hint_x=None, width=dp(w)))
            col.add_widget(row)

        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)


# ── Blood Glucose ───────────────────────────────────────────────────
class BloodGlucoseScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [1.0, 0.4, 0.4, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Blood Glucose', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(14),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                        size_hint_y=None, padding=[dp(14), dp(14)])
        card.bind(minimum_height=card.setter('height'))
        inner = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        def _tf(hint):
            return MDTextField(hint_text=hint, mode='rectangle',
                               line_color_focus=accent,
                               line_color_normal=[0.2, 0.2, 0.2, 1],
                               text_color_normal=self.text_color,
                               text_color_focus=self.text_color,
                               hint_text_color_normal=self.subtitle_color,
                               fill_color_normal=self.card_bg,
                               fill_color_focus=self.card_bg,
                               font_size=dp(15), input_filter='float',
                               size_hint_y=None, height=dp(52))

        inner.add_widget(MDLabel(text='BLOOD GLUCOSE CONVERTER', font_style='Overline',
                                 theme_text_color='Custom', text_color=accent,
                                 bold=True, size_hint_y=None, height=dp(22)))

        self._mgdl_f = _tf('mg/dL  (US / Canada)')
        self._mmol_f = _tf('mmol/L  (UK / Australia / Europe)')
        self._mgdl_f.bind(text=lambda inst, v: self._from_mgdl(v))
        self._mmol_f.bind(text=lambda inst, v: self._from_mmol(v))
        self._converting = False

        ref = MDLabel(
            text='Reference ranges:\nFasting: 70–99 mg/dL  (3.9–5.5 mmol/L)\n'
                 'Post-meal: < 140 mg/dL  (< 7.8 mmol/L)',
            font_style='Caption', theme_text_color='Custom',
            text_color=self.subtitle_color,
            size_hint_y=None, height=dp(60),
        )

        inner.add_widget(self._mgdl_f)
        inner.add_widget(self._mmol_f)
        inner.add_widget(ref)
        card.add_widget(inner)
        col.add_widget(card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _from_mgdl(self, v):
        if self._converting: return
        try:
            self._converting = True
            self._mmol_f.text = f'{float(v) / 18.018:.2f}'
        except Exception:
            pass
        finally:
            self._converting = False

    def _from_mmol(self, v):
        if self._converting: return
        try:
            self._converting = True
            self._mgdl_f.text = f'{float(v) * 18.018:.1f}'
        except Exception:
            pass
        finally:
            self._converting = False


# ── Tire Size Decoder ───────────────────────────────────────────────
class TireSizeScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.6, 0.6, 0.6, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Tire Size Decoder', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(14),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                        size_hint_y=None, padding=[dp(14), dp(14)])
        card.bind(minimum_height=card.setter('height'))
        inner = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(MDLabel(text='TIRE SIZE DECODER', font_style='Overline',
                                 theme_text_color='Custom', text_color=accent,
                                 bold=True, size_hint_y=None, height=dp(22)))

        self._tire_inp = MDTextField(
            hint_text='e.g.  205/55R16  or  225/45R17',
            mode='rectangle', line_color_focus=accent,
            line_color_normal=[0.2,0.2,0.2,1],
            text_color_normal=self.text_color, text_color_focus=self.text_color,
            hint_text_color_normal=self.subtitle_color,
            fill_color_normal=self.card_bg, fill_color_focus=self.card_bg,
            font_size=dp(15), size_hint_y=None, height=dp(52),
        )
        self._tire_inp.bind(text=lambda *_: self._decode())

        self._tire_result = MDLabel(
            text='Enter a tire size above',
            font_style='Body1', theme_text_color='Custom',
            text_color=self.text_color, size_hint_y=None, height=dp(180),
        )

        inner.add_widget(self._tire_inp)
        inner.add_widget(self._tire_result)
        card.add_widget(inner)
        col.add_widget(card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _decode(self):
        import re
        raw = self._tire_inp.text.strip().upper().replace(' ', '')
        m = re.match(r'(\d{3})/(\d{2})R(\d{2}(?:\.\d)?)', raw)
        if not m:
            self._tire_result.text = 'Format: 205/55R16'
            return
        width_mm  = int(m.group(1))
        aspect    = int(m.group(2))
        rim_in    = float(m.group(3))
        sidewall_mm   = width_mm * aspect / 100
        rim_mm        = rim_in * 25.4
        total_diam_mm = rim_mm + 2 * sidewall_mm
        total_diam_in = total_diam_mm / 25.4
        circumf_mm    = math.pi * total_diam_mm
        circumf_in    = circumf_mm / 25.4
        width_in      = width_mm / 25.4
        self._tire_result.text = (
            f'Width:       {width_mm} mm  ({width_in:.2f} in)\n'
            f'Aspect:      {aspect}%\n'
            f'Rim:         {rim_in:g}"  ({rim_mm:.1f} mm)\n'
            f'Sidewall:    {sidewall_mm:.1f} mm\n'
            f'Total Ø:     {total_diam_mm:.1f} mm  ({total_diam_in:.2f} in)\n'
            f'Circumf:     {circumf_mm:.0f} mm  ({circumf_in:.1f} in)\n'
            f'Rev/km:      {1000000/circumf_mm:.0f}'
        )


# ── Concentration ───────────────────────────────────────────────────
class ConcentrationScreen(GenericUnitScreen):
    TITLE  = "Concentration"
    ACCENT = [0.4, 0.9, 0.6, 1]
    FMT    = ":.6g"
    # Base: mol/L (M)
    UNITS  = [
        ("mol/L (M)",    1.0),
        ("mmol/L (mM)",  1e-3),
        ("µmol/L (µM)",  1e-6),
        ("nmol/L (nM)",  1e-9),
        ("mol/m³",       1e-3),
        ("g/L",          1.0),      # Note: depends on MW; approximation for water
        ("mg/L",         1e-3),
        ("µg/L",         1e-6),
        ("ppm (mg/kg)",  1e-3),
        ("ppb (µg/kg)",  1e-6),
        ("ppt (ng/kg)",  1e-9),
        ("% (v/v)",      10.0),
    ]


# ── Radiation Dose ──────────────────────────────────────────────────
class RadiationDoseScreen(GenericUnitScreen):
    TITLE  = "Radiation Dose"
    ACCENT = [0.6, 1.0, 0.3, 1]
    FMT    = ":.6g"
    # Base: Sievert (Sv)
    UNITS  = [
        ("Sv",    1.0),
        ("mSv",   1e-3),
        ("µSv",   1e-6),
        ("rem",   0.01),
        ("mrem",  1e-4),
        ("Gy",    1.0),        # 1 Gy ≈ 1 Sv for X-rays/gamma
        ("mGy",   1e-3),
        ("rad",   0.01),
        ("mrad",  1e-4),
        ("J/kg",  1.0),
    ]


# ── Humidity ────────────────────────────────────────────────────────
class HumidityScreen(ConverterScreen):
    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        accent = [0.3, 0.75, 1.0, 1]
        root_box = BoxLayout(orientation='vertical')

        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back = MDIconButton(icon='arrow-left', theme_text_color='Custom',
                            text_color=self.header_color)
        back.bind(on_release=lambda *_: self.go_back())
        top.add_widget(back)
        top.add_widget(MDLabel(text='Humidity', font_style='H6',
                               theme_text_color='Custom', text_color=self.header_color,
                               bold=True, valign='center'))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(14),
                        padding=[dp(14), dp(8)], size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                        size_hint_y=None, padding=[dp(14), dp(14)])
        card.bind(minimum_height=card.setter('height'))
        inner = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        def _tf(hint):
            return MDTextField(hint_text=hint, mode='rectangle',
                               line_color_focus=accent,
                               line_color_normal=[0.2, 0.2, 0.2, 1],
                               text_color_normal=self.text_color,
                               text_color_focus=self.text_color,
                               hint_text_color_normal=self.subtitle_color,
                               fill_color_normal=self.card_bg,
                               fill_color_focus=self.card_bg,
                               font_size=dp(15), input_filter='float',
                               size_hint_y=None, height=dp(52))

        inner.add_widget(MDLabel(text='DEW POINT & HUMIDITY', font_style='Overline',
                                 theme_text_color='Custom', text_color=accent,
                                 bold=True, size_hint_y=None, height=dp(22)))
        inner.add_widget(MDLabel(
            text='Enter temperature (°C) and relative humidity (%)',
            font_style='Caption', theme_text_color='Custom',
            text_color=self.subtitle_color, size_hint_y=None, height=dp(22)))

        self._temp_f = _tf('Air temperature (°C)')
        self._rh_f   = _tf('Relative humidity (%)  e.g. 65')
        self._hum_result = MDLabel(
            text='Enter temperature and RH above',
            font_style='Body1', theme_text_color='Custom',
            text_color=self.text_color, size_hint_y=None, height=dp(130),
        )
        calc_btn = MDRaisedButton(text='CALCULATE',
                                  md_bg_color=list(accent[:3]) + [0.85],
                                  theme_text_color='Custom', text_color=[0,0,0,1],
                                  size_hint_y=None, height=dp(44))
        calc_btn.bind(on_release=lambda *_: self._calc())

        for w in (self._temp_f, self._rh_f, calc_btn, self._hum_result):
            inner.add_widget(w)
        card.add_widget(inner)
        col.add_widget(card)
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    def _calc(self):
        try:
            T  = float(self._temp_f.text)
            RH = float(self._rh_f.text)
            # Magnus formula dew point
            a, b = 17.625, 243.04
            alpha = math.log(RH / 100) + (a * T) / (b + T)
            Td    = b * alpha / (a - alpha)
            # Absolute humidity g/m³
            Psat  = 6.1078 * 10 ** (7.5 * T / (237.3 + T))
            AH    = 216.7 * (RH / 100 * Psat / (273.15 + T))
            # Heat index (only valid for T >= 27°C and RH >= 40%)
            hi_str = ''
            if T >= 27 and RH >= 40:
                c = [-8.784695, 1.61139411, 2.338549, -0.14611605,
                     -0.01230809, -0.01642482, 0.00221173, 0.00072546, -0.00000358]
                HI = (c[0] + c[1]*T + c[2]*RH + c[3]*T*RH + c[4]*T**2 +
                      c[5]*RH**2 + c[6]*T**2*RH + c[7]*T*RH**2 + c[8]*T**2*RH**2)
                hi_str = f'\nHeat Index:  {HI:.1f} °C'
            self._hum_result.text = (
                f'Dew Point:       {Td:.1f} °C\n'
                f'Frost Point:     {Td - 0.5*(T - Td):.1f} °C\n'
                f'Abs. Humidity:   {AH:.2f} g/m³\n'
                f'Wet Bulb (approx): {T * math.atan(0.151977*(RH+8.313659)**0.5) + math.atan(T+RH) - math.atan(RH-1.676331) + 0.00391838*RH**1.5*math.atan(0.023101*RH) - 4.686035:.1f} °C'
                + hi_str
            )
        except Exception:
            self._hum_result.text = 'Enter valid numbers'


# ── Scientific Calculator: add Deg/Rad toggle + inverse trig ────────
# (Patch into existing ScientificCalculatorPopup)
# We override _build to inject the toggle and asin/acos/atan rows.
_ORIG_SCI_BUILD = ScientificCalculatorPopup._build

def _patched_sci_build(self):
    _ORIG_SCI_BUILD(self)
    # The base build already created self.content; we're done here.
    # Deg/Rad is handled via self._deg_mode flag set during _build.

# Patch: override __init__ to set deg mode and inject extra rows
_ORIG_SCI_INIT = ScientificCalculatorPopup.__init__

def _patched_sci_init(self, **kwargs):
    self._deg_mode = True  # default: degrees
    _ORIG_SCI_INIT(self, **kwargs)

ScientificCalculatorPopup.__init__ = _patched_sci_init

# Override _build entirely to add Deg/Rad + inverse trig
def _new_sci_build(self):
    from kivy.graphics import Color as _GC, RoundedRectangle as _GRR

    accent  = [0.0, 0.85, 0.72, 1]
    bg      = [0.06, 0.06, 0.08, 1]
    card_bg = [0.10, 0.10, 0.13, 1]

    root = BoxLayout(orientation='vertical', padding=dp(4), spacing=dp(4))

    with root.canvas.before:
        _GC(*bg)
        _rr = _GRR(pos=root.pos, size=root.size, radius=[18])
    root.bind(pos=lambda w, v, r=_rr: setattr(r, 'pos', v),
              size=lambda w, v, r=_rr: setattr(r, 'size', v))

    # Title bar with Deg/Rad toggle
    title_row = BoxLayout(size_hint_y=None, height=dp(40),
                          padding=[dp(14), dp(4), dp(4), dp(0)])
    title_lbl = MDLabel(text='Scientific Calculator', font_style='Subtitle1',
                        theme_text_color='Custom', text_color=accent,
                        bold=True, valign='center')
    self._deg_chip = BaseChip(chip_text='DEG', accent=accent, is_active=True,
                               size_hint=(None, None), size=(dp(56), dp(32)))
    self._rad_chip = BaseChip(chip_text='RAD', accent=[1.0,0.75,0.2,1], is_active=False,
                               size_hint=(None, None), size=(dp(56), dp(32)))
    self._deg_chip.bind(on_release=lambda *_: self._set_angle(True))
    self._rad_chip.bind(on_release=lambda *_: self._set_angle(False))
    close_btn = FlatIconBtn(icon='close', btn_bg=[0.18,0.18,0.18,1],
                            icon_color=[0.7,0.7,0.7,1], btn_radius=20,
                            size=(dp(36), dp(36)))
    close_btn.bind(on_release=lambda *_: self.dismiss())
    title_row.add_widget(title_lbl)
    title_row.add_widget(self._deg_chip)
    title_row.add_widget(self._rad_chip)
    title_row.add_widget(close_btn)
    root.add_widget(title_row)

    # Display
    disp_box = RoundBox(bg_color=card_bg, box_radius=[12]*4,
                        size_hint_y=None, height=dp(80),
                        padding=[dp(12), dp(6)])
    disp_col = BoxLayout(orientation='vertical', spacing=dp(2))
    self._expr_lbl = MDLabel(text='0', font_style='Body2',
                             theme_text_color='Custom',
                             text_color=[0.52,0.52,0.56,1],
                             halign='right', valign='center',
                             size_hint_y=None, height=dp(26),
                             shorten=True, shorten_from='left')
    self._result_lbl = MDLabel(text='', font_style='H4',
                               theme_text_color='Custom',
                               text_color=[0.95,0.95,0.95,1],
                               halign='right', valign='center',
                               bold=True, shorten=True, shorten_from='left')
    # Copy result button
    disp_row = BoxLayout()
    copy_res = FlatIconBtn(icon='content-copy', btn_bg=[0,0,0,0],
                           icon_color=[0.3,0.3,0.3,1], btn_radius=8,
                           size=(dp(30), dp(30)))
    copy_res.bind(on_release=lambda *_: (
        Clipboard.copy(self._result_lbl.text or self._expr_lbl.text),
        _snack('Copied result')))
    disp_row.add_widget(self._result_lbl)
    disp_row.add_widget(copy_res)
    disp_col.add_widget(self._expr_lbl)
    disp_col.add_widget(disp_row)
    disp_box.add_widget(disp_col)
    root.add_widget(disp_box)

    # Calc history label
    self._hist_lbl = MDLabel(text='', font_style='Caption',
                             theme_text_color='Custom',
                             text_color=[0.35,0.35,0.35,1],
                             halign='right', valign='center',
                             size_hint_y=None, height=dp(18),
                             shorten=True, shorten_from='left',
                             padding=[dp(8),0])
    root.add_widget(self._hist_lbl)
    self._history = []

    btn_colors = {
        'fn':  ([0.15,0.15,0.20,1], [0.55,0.75,1.0,1]),
        'op':  ([0.14,0.22,0.14,1], [0.3, 0.85,0.55,1]),
        'eq':  ([0.0, 0.55,0.46,1], [0.0, 0.95,0.80,1]),
        'num': ([0.12,0.12,0.15,1], [0.90,0.90,0.90,1]),
        'clr': ([0.22,0.08,0.08,1], [1.0, 0.4, 0.4, 1]),
        'mem': ([0.18,0.10,0.22,1], [0.85,0.5, 1.0, 1]),
        'inv': ([0.20,0.14,0.10,1], [1.0, 0.78,0.3, 1]),
    }

    rows = [
        [('MC','mem'),('MR','mem'),('M+','mem'),('M−','mem'),('MS','mem')],
        [('sin','fn'), ('cos','fn'), ('tan','fn'), ('sinh','fn'),('cosh','fn')],
        [('sin⁻¹','inv'),('cos⁻¹','inv'),('tan⁻¹','inv'),('tanh','fn'),('log2','fn')],
        [('x²','fn'),  ('x³','fn'),  ('xʸ','fn'),  ('√','fn'),  ('∛','fn')],
        [('log','fn'), ('ln','fn'),  ('eˣ','fn'),  ('10ˣ','fn'),('π','num')],
        [('(',  'op'), (')',  'op'), ('%',  'op'), ('÷',  'op'), ('⌫','clr')],
        [('7',  'num'),('8',  'num'),('9',  'num'),('×',  'op'), ('C','clr')],
        [('4',  'num'),('5',  'num'),('6',  'num'),('−',  'op'), ('±','fn')],
        [('1',  'num'),('2',  'num'),('3',  'num'),('+',  'op'), ('=','eq')],
        [('0',  'num'),('00', 'num'),('.',  'num'),('e',  'num'), ('=','eq')],
    ]

    self._memory = 0.0
    grid = BoxLayout(orientation='vertical', spacing=dp(3))
    for row in rows:
        row_box = BoxLayout(spacing=dp(3), size_hint_y=None, height=dp(43))
        for label, kind in row:
            bg_c, fg_c = btn_colors[kind]
            row_box.add_widget(self._make_calc_btn(label, bg_c, fg_c))
        grid.add_widget(row_box)
    root.add_widget(grid)
    self.content = root

ScientificCalculatorPopup._build = _new_sci_build

# Patch _set_angle
def _set_angle(self, deg):
    self._deg_mode = deg
    self._deg_chip.is_active = deg
    self._rad_chip.is_active = not deg

ScientificCalculatorPopup._set_angle = _set_angle

# Patch _safe_eval to respect deg/rad mode
def _safe_eval_v2(self, expr=None):
    raw = (expr or self._expr or '0').strip()
    raw = raw.replace('÷', '/').replace('×', '*').replace('−', '-')
    opens = raw.count('(') - raw.count(')')
    raw += ')' * max(opens, 0)
    if getattr(self, '_deg_mode', True):
        def _sin(x): return math.sin(math.radians(x))
        def _cos(x): return math.cos(math.radians(x))
        def _tan(x): return math.tan(math.radians(x))
        def _asin(x): return math.degrees(math.asin(x))
        def _acos(x): return math.degrees(math.acos(x))
        def _atan(x): return math.degrees(math.atan(x))
    else:
        _sin = math.sin; _cos = math.cos; _tan = math.tan
        _asin = math.asin; _acos = math.acos; _atan = math.atan
    safe_ns = {
        'sin': _sin, 'cos': _cos, 'tan': _tan,
        'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
        'log': math.log, 'log10': math.log10, 'log2': math.log2,
        'sqrt': math.sqrt, 'cbrt': lambda x: math.copysign(abs(x)**(1/3), x),
        'exp': math.exp, 'abs': abs, 'round': round,
        'pi': math.pi, 'e': math.e, 'inf': math.inf,
        'pow': math.pow, 'factorial': math.factorial,
        # inverse trig — stored as asin/acos/atan in expression string
        'asin': _asin, 'acos': _acos, 'atan': _atan,
        '__builtins__': {},
    }
    return eval(raw, safe_ns)

ScientificCalculatorPopup._safe_eval = _safe_eval_v2

# Patch _handle to map sin⁻¹ → asin( etc, and track history
_ORIG_HANDLE = ScientificCalculatorPopup._handle

def _patched_handle(self, label):
    inv_map = {'sin⁻¹': 'asin(', 'cos⁻¹': 'acos(', 'tan⁻¹': 'atan(', 'log2': 'log2('}
    if label in inv_map:
        token = inv_map[label]
        if self._just_got_result and self._result:
            self._expr = token + self._result
        else:
            self._expr = token + (self._expr or '')
        self._just_got_result = False
        self._refresh(self._expr or '0', '')
        return
    _ORIG_HANDLE(self, label)

ScientificCalculatorPopup._handle = _patched_handle

# Patch _evaluate to store history
_ORIG_EVAL = ScientificCalculatorPopup._evaluate

def _patched_evaluate(self):
    old_expr = self._expr
    _ORIG_EVAL(self)
    if self._result and self._result not in ('', 'Error'):
        self._history.append(f'{old_expr} = {self._result}')
        self._history = self._history[-5:]
        self._hist_lbl.text = '  ·  '.join(self._history[-3:])

ScientificCalculatorPopup._evaluate = _patched_evaluate


# ── Roman Numeral support in NumeralScreen ──────────────────────────
def _int_to_roman(n):
    if n <= 0 or n > 3999:
        return 'Out of range (1–3999)'
    val = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    sym = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I']
    result = ''
    for v, s in zip(val, sym):
        while n >= v:
            result += s
            n -= v
    return result

def _roman_to_int(s):
    rom = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    s = s.upper().strip()
    result = 0
    prev = 0
    for ch in reversed(s):
        if ch not in rom:
            raise ValueError(f'Invalid Roman numeral character: {ch}')
        val = rom[ch]
        result += val if val >= prev else -val
        prev = val
    return result


# ── About / Features Screen ─────────────────────────────────────────
_ABOUT_TEXT = """\
UNIVERSAL CONVERTOR  v7.0
by SH Vertex
─────────────────────────────────────

45 CONVERSION MODULES

EVERYDAY
  Length          km, mi, ft, m, in, cm, mm, nm, ly, au
  Weight          kg, lb, oz, g, mg, t, st, ct
  Temperature     C, F, K, Ra, Re
  Volume          L, ml, gal, qt, pt, cup, fl oz, m3
  Area            m2, km2, ac, ha, ft2, mi2, in2
  Time            s, min, h, day, wk, mo, yr, decade
  Speed           km/h, mph, m/s, knot, ft/s, mach
  Currency        51 live currencies (USD EUR GBP JPY CNY INR +45)
                  Live mid-market rates via open.er-api.com
                  Offline fallback for all 51 currencies
                  Favourites, swap-source, copy-all, timestamp
  Fuel Economy    mpg (US/UK), L/100km, km/L
  Cooking         cup, tbsp, tsp, ml, fl oz, pinch
  Clothing        Women/Men tops, shoes (US UK EU JP IT)
                  Bra sizes (US EU UK), extended ranges

EVERYDAY TOOLS
  Time Zones      30 world zones, live UTC input, now button
  Date & Age      Age calculator, date difference, days/weeks/years
  Tip Calculator  Bill + tip % + split, quick % chips
  Discount / %    X% off, X as % of Y, % change
  BMI / BMR       Mifflin-St Jeor, TDEE, activity level, Deg/Rad
  Shoe Sizes      US M/W, UK, EU, JP  (19 sizes)
  Ring Sizes      US, UK, EU, diameter mm  (18 sizes)
  Blood Glucose   mg/dL <-> mmol/L  (live bidirectional)
  Tire Sizes      205/55R16 decoder: sidewall, diameter, circumference

SCIENCE & ENGINEERING
  Pressure        Pa, bar, psi, atm, mmHg, inHg, kPa
  Energy          J, cal, kcal, kWh, BTU, eV, MJ
  Power           W, kW, MW, hp (mech/elec), BTU/hr
  Torque          Nm, lbft, lbin, kgm
  Acceleration    m/s2, g, ft/s2, gal
  Force           N, lbf, kgf, dyn
  Density         kg/m3, g/cm3, lb/ft3, lb/in3
  Flow Rate       L/s, m3/s, GPM, CFM
  Viscosity       Pa·s, cP, P, St, cSt
  Angle           deg, rad, grad, turn, arcmin, arcsec
  Frequency       Hz, kHz, MHz, GHz, rpm
  Radioactivity   Bq, Ci, Rd, dps
  Sound           dB scale reference converter
  Concentration   mol/L, mmol, µmol, g/L, ppm, ppb, ppt, %
  Radiation Dose  Sv, mSv, rem, Gy, mGy, rad  (X-ray/gamma)
  Humidity        Dew point, frost point, abs humidity, heat index

ELECTRONICS & DIGITAL
  Electric Units  V, A, Ω, W, kWh, C, F, H conversions
  Magnetic Field  T, mT, G, Oe, A/m
  Data Storage    bit, B, KB, MB, GB, TB, PB (binary & decimal)
  Typography      px, pt, em, rem, mm, in, pica
  Color Codes     HEX <-> RGB <-> HSL

NUMERALS & CODES
  Numeral System  DEC, BIN, HEX, OCT, TXT/ASCII, Roman (I–MMMCMXCIX)

LIGHT & OPTICS
  Illuminance     lux, fc, lm/m2, phot
  Luminance       cd/m2, nit, fL, sb

PRINTING & DESIGN
  Paper Sizes     A0–A10, B0–B5, Letter, Legal, Tabloid

─────────────────────────────────────

SCIENTIFIC CALCULATOR
  Full scientific calc with:
  Deg / Rad toggle
  sin cos tan  |  sin-1 cos-1 tan-1
  sinh cosh tanh
  log ln log2 log10
  sqrt cbrt x^2 x^3 x^y
  e^x  10^x
  Pi and e constants
  Memory: MC MR M+ M- MS
  Last 5 results history
  Copy result button

─────────────────────────────────────

HOME SCREEN
  Full-text search across all 45 modules
  Recently used modules bar (last 6)
  Floating calculator FAB on every screen

CURRENCY SCREEN
  51 currencies with country codes
  Live mid-market rates (open.er-api.com)
  Offline fallback rates built in
  Last-fetched timestamp displayed
  Favourites system (star to pin)
  Swap-source button on every row
  Copy individual or all results
  Mid-market disclaimer

SPLASH / LOADING
  Determinate progress bar (N of 47)
  Animated arc ring
  Lazy screen building — home loads in <1 s

SETTINGS
  AMOLED Dark theme (pure black, OLED)
  Grey Dark theme
  License details & device code
  Features & About (this screen)

─────────────────────────────────────
SH Vertex  •  Universal Convertor v7.0
Built with Python + Kivy + KivyMD 1.2
"""

class AboutScreen(ConverterScreen):
    def go_back(self, *_):
        _ensure_screen(self.manager, "settings")
        self.manager.transition.direction = "right"
        self.manager.current = "settings"

    def on_kv_post(self, base_widget, *args):
        super().on_kv_post(base_widget, *args)
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()
        from kivy.graphics import Color, Rectangle, RoundedRectangle
        t = THEMES[_current_theme]
        accent   = [0.0, 0.85, 0.72, 1]
        accent2  = [0.55, 0.55, 1.0, 1]
        accent3  = [1.0, 0.75, 0.2, 1]

        root_box = BoxLayout(orientation='vertical')
        with root_box.canvas.before:
            Color(*t["screen_bg"])
            _bg = Rectangle(pos=root_box.pos, size=root_box.size)
        root_box.bind(pos=lambda w, v: setattr(_bg, 'pos', v),
                      size=lambda w, v: setattr(_bg, 'size', v))

        # ── Top bar ──
        top = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(2), dp(8), dp(14), dp(8)], spacing=dp(2))
        back_btn = MDIconButton(icon="arrow-left", theme_text_color="Custom",
                                text_color=self.header_color)
        back_btn.bind(on_release=self.go_back)
        top.add_widget(back_btn)
        top.add_widget(MDLabel(text="Features & About", font_style="H6",
                               theme_text_color="Custom", text_color=self.header_color,
                               bold=True, valign="center"))
        root_box.add_widget(top)

        sv = ScrollView()
        col = BoxLayout(orientation='vertical', spacing=dp(14),
                        padding=[dp(12), dp(8), dp(12), dp(16)],
                        size_hint_y=None)
        col.bind(minimum_height=col.setter('height'))

        # ── Hero card ──
        hero = self._make_card(
            icon='calculator-variant',
            icon_color=accent,
            title='Universal Convertor  v7.0',
            subtitle='by SH Vertex   •   45 modules   •   Python + Kivy + KivyMD 1.2',
            accent=accent,
        )
        col.add_widget(hero)

        # ── Feature section cards ──
        sections = [
            ('ruler',            accent,  'Everyday Conversions',
             'Length, Weight, Temperature, Volume, Area, Time, Speed, Fuel, Cooking, Clothing & Bra sizes'),
            ('currency-usd',     accent3, 'Currency  (51 live)',
             'Live mid-market rates, 51 currencies, favourites, swap-source, copy-all, offline fallback, timestamp'),
            ('toolbox-outline',  [0.3,0.75,1,1], 'Everyday Tools',
             'Time Zones, Date & Age, Tip Calc, Discount/%, BMI/BMR, Shoe Sizes, Ring Sizes, Blood Glucose, Tire Decoder'),
            ('flask-outline',    [0.4,0.9,0.6,1], 'Science & Engineering',
             'Pressure, Energy, Power, Torque, Force, Density, Flow, Viscosity, Angle, Frequency, Radioactivity, Sound, Concentration, Radiation Dose, Humidity'),
            ('chip',             [0.8,0.5,1,1], 'Electronics & Digital',
             'Electric Units, Magnetic Field, Data Storage, Typography, Color Codes (HEX/RGB/HSL)'),
            ('numeric',          [1,0.45,0.45,1], 'Numeral Systems',
             'Decimal, Binary, Hex, Octal, ASCII/Text, Roman Numerals (I–MMMCMXCIX)  — bidirectional'),
            ('lightbulb-outline',[1,0.78,0.2,1], 'Light, Optics & Print',
             'Illuminance, Luminance, Paper Sizes (A0–A10, Letter, Legal, Tabloid)'),
            ('calculator',       accent,  'Scientific Calculator',
             'Deg/Rad toggle, sin/cos/tan + inverses, sinh/cosh/tanh, log/ln/log2, sqrt/cbrt, x^y, e^x, 10^x, Pi, e, Memory (MC/MR/M+/M-/MS), 5-result history, copy button'),
            ('magnify',          accent2, 'Smart Home Screen',
             'Full-text search across all 45 modules, recently-used bar, floating calculator FAB on every screen'),
            ('progress-download',accent,  'Fast Splash Screen',
             'Determinate progress bar, animated arc ring, lazy screen building — home loads in under 1 second'),
            ('palette-outline',  [0.55,0.55,1,1], 'Themes & Settings',
             'AMOLED pure black (OLED optimised) and Grey Dark theme, license details, device code'),
        ]

        for icon, ic, title, body in sections:
            col.add_widget(self._make_feature_row(icon, ic, title, body))

        # ── Full text block with copy button ──
        col.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))
        col.add_widget(self._make_section_header('FULL FEATURE LIST  (tap to copy)', accent))

        txt_card = RoundBox(bg_color=self.card_bg, box_radius=[14]*4,
                            size_hint_y=None, padding=[dp(14), dp(12)])
        txt_card.bind(minimum_height=txt_card.setter('height'))
        txt_col = BoxLayout(orientation='vertical', spacing=dp(8),
                            size_hint_y=None)
        txt_col.bind(minimum_height=txt_col.setter('height'))

        txt_lbl = Label(
            text=_ABOUT_TEXT,
            font_size=dp(11.5),
            color=[0.80, 0.80, 0.80, 1],
            halign='left', valign='top',
            size_hint_y=None,
            markup=False,
        )
        txt_lbl.bind(width=lambda w, v: setattr(w, 'text_size', (v, None)))
        txt_lbl.bind(texture_size=lambda w, v: setattr(w, 'height', v[1]))

        copy_btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        copy_btn_row.add_widget(Widget())
        copy_btn = MDRaisedButton(
            text='COPY FULL LIST',
            md_bg_color=list(accent[:3]) + [0.85],
            theme_text_color='Custom',
            text_color=[0, 0, 0, 1],
            size_hint=(None, None), size=(dp(160), dp(40)),
        )
        copy_btn.bind(on_release=lambda *_: (
            Clipboard.copy(_ABOUT_TEXT),
            _snack('Copied full feature list')))
        copy_btn_row.add_widget(copy_btn)
        copy_btn_row.add_widget(Widget())

        txt_col.add_widget(txt_lbl)
        txt_col.add_widget(copy_btn_row)
        txt_card.add_widget(txt_col)
        col.add_widget(txt_card)

        col.add_widget(BoxLayout(size_hint_y=None, height=dp(80)))
        sv.add_widget(col)
        root_box.add_widget(sv)
        self._add_nav(root_box)
        self.add_widget(root_box)

    # ── Widget builders ────────────────────────────────────────────
    def _make_section_header(self, text, accent):
        from kivy.graphics import Color, RoundedRectangle
        row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8),
                        padding=[dp(6), dp(2)])
        with row.canvas.before:
            Color(*accent[:3], 0.10)
            _rr = RoundedRectangle(pos=row.pos, size=row.size, radius=[6]*4)
        row.bind(pos=lambda w, v: setattr(_rr, 'pos', v),
                 size=lambda w, v: setattr(_rr, 'size', v))
        from kivymd.uix.label import MDIcon
        row.add_widget(MDIcon(icon='chevron-right', theme_text_color='Custom',
                              text_color=accent, font_size=dp(14),
                              size_hint_x=None, width=dp(18)))
        row.add_widget(MDLabel(text=text, font_style='Overline',
                               theme_text_color='Custom', text_color=accent,
                               bold=True, valign='center'))
        return row

    def _make_card(self, icon, icon_color, title, subtitle, accent):
        from kivy.graphics import Color, RoundedRectangle
        from kivy.uix.behaviors import ButtonBehavior
        card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80),
                         padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(14))
        with card.canvas.before:
            Color(*list(accent[:3]) + [0.10])
            _rr = RoundedRectangle(pos=card.pos, size=card.size, radius=[16]*4)
            Color(*list(accent[:3]) + [0.35])
            from kivy.graphics import Line
            _ln = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, 16),
                       width=1.2)
        def _upd(w, v):
            _rr.pos = w.pos; _rr.size = w.size
            _ln.rounded_rectangle = (w.x, w.y, w.width, w.height, 16)
        card.bind(pos=_upd, size=_upd)

        icon_box = self._icon_box(icon, icon_color, 48)
        card.add_widget(icon_box)

        txt = BoxLayout(orientation='vertical', spacing=dp(4))
        txt.add_widget(MDLabel(text=title, font_style='Body1',
                               theme_text_color='Custom', text_color=self.card_title_color,
                               bold=True, size_hint_y=None, height=dp(24)))
        txt.add_widget(MDLabel(text=subtitle, font_style='Caption',
                               theme_text_color='Custom', text_color=self.subtitle_color,
                               size_hint_y=None, height=dp(28)))
        card.add_widget(txt)
        return card

    def _make_feature_row(self, icon, icon_color, title, body):
        from kivy.graphics import Color, RoundedRectangle
        card = BoxLayout(orientation='horizontal', size_hint_y=None,
                         padding=[dp(12), dp(10), dp(12), dp(10)], spacing=dp(12))
        card.bind(minimum_height=card.setter('height'))
        with card.canvas.before:
            Color(*list(icon_color[:3]) + [0.07])
            _rr = RoundedRectangle(pos=card.pos, size=card.size, radius=[12]*4)
        card.bind(pos=lambda w, v: setattr(_rr, 'pos', v),
                  size=lambda w, v: setattr(_rr, 'size', v))

        icon_box = self._icon_box(icon, icon_color, 36)
        icon_box.pos_hint = {'top': 1}
        card.add_widget(icon_box)

        txt = BoxLayout(orientation='vertical', spacing=dp(2),
                        size_hint_y=None)
        txt.bind(minimum_height=txt.setter('height'))
        txt.add_widget(MDLabel(text=title, font_style='Body2',
                               theme_text_color='Custom',
                               text_color=list(icon_color[:3]) + [1],
                               bold=True, size_hint_y=None, height=dp(22)))
        body_lbl = Label(text=body, font_size=dp(11.5),
                         color=[0.76, 0.76, 0.76, 1],
                         halign='left', valign='top', size_hint_y=None)
        body_lbl.bind(width=lambda w, v: setattr(w, 'text_size', (v, None)))
        body_lbl.bind(texture_size=lambda w, v: setattr(w, 'height', v[1] + dp(4)))
        txt.add_widget(body_lbl)
        card.add_widget(txt)

        # Fix card height to content
        def _fix_h(w, v):
            card.height = max(dp(58), v + dp(20))
        txt.bind(height=_fix_h)
        return card

    def _icon_box(self, icon, color, size_dp):
        from kivy.graphics import Color, RoundedRectangle
        from kivymd.uix.label import MDIcon
        box = BoxLayout(size_hint=(None, None), size=(dp(size_dp), dp(size_dp)))
        with box.canvas.before:
            Color(*list(color[:3]) + [0.18])
            _rr = RoundedRectangle(pos=box.pos, size=box.size,
                                   radius=[int(size_dp * 0.28)]*4)
        box.bind(pos=lambda w, v: setattr(_rr, 'pos', v),
                 size=lambda w, v: setattr(_rr, 'size', v))
        box.add_widget(MDIcon(icon=icon, theme_text_color='Custom',
                              text_color=color, halign='center',
                              font_size=dp(size_dp * 0.45)))
        return box


# ── Screen map ──
# ── On-demand screen builder ─────────────────────────────────────────────────
def _ensure_screen(manager, name):
    """Build and register a screen the first time it is navigated to.
    Called before every manager.current = name assignment outside HomeScreen.go()
    so that screens are never pre-built in bulk (no loading screen needed)."""
    if not manager.has_screen(name):
        cls = {n: c for n, c in SCREEN_MAP}.get(name)
        if cls:
            manager.add_widget(cls(name=name))

SCREEN_MAP = [
    # Core
    ("home",            HomeScreen),
    ("settings",        SettingsScreen),
    ("license_details", LicenseDetailsScreen),
    # Everyday
    ("numeral",       NumeralScreen),
    ("length",        LengthScreen),
    ("weight",        WeightScreen),
    ("temperature",   TemperatureScreen),
    ("volume",        VolumeScreen),
    ("area",          AreaScreen),
    ("time",          TimeScreen),
    ("speed",         SpeedScreen),
    ("fuel",          FuelScreen),
    ("currency",      CurrencyScreen),
    ("cooking",       CookingScreen),
    ("clothing",      ClothingScreen),
    # Science & Engineering
    ("pressure",      PressureScreen),
    ("energy",        EnergyScreen),
    ("power",         PowerScreen),
    ("torque",        TorqueScreen),
    ("acceleration",  AccelerationScreen),
    ("force",         ForceScreen),
    ("density",       DensityScreen),
    ("flowrate",      FlowRateScreen),
    ("viscosity",     ViscosityScreen),
    ("angle",         AngleScreen),
    ("frequency",     FrequencyScreen),
    ("radioactivity", RadioactivityScreen),
    ("sound",         SoundScreen),
    # Electronics & Digital
    ("electric",      ElectricScreen),
    ("magnetic",      MagneticScreen),
    ("datastorage",   DataStorageScreen),
    ("typography",    TypographyScreen),
    ("color",         ColorScreen),
    # Light & Optics
    ("illuminance",   IlluminanceScreen),
    ("luminance",     LuminanceScreen),
    # Printing & Design
    ("papersize",     PaperSizeScreen),
    # Phase 7 — Everyday Tools
    ("timezone",      TimeZoneScreen),
    ("dateage",       DateAgeScreen),
    ("tip",           TipScreen),
    ("discount",      DiscountScreen),
    ("bmibmr",        BMIBMRScreen),
    ("shoesize",      ShoeSizeScreen),
    ("ringsize",      RingSizeScreen),
    ("bloodglucose",  BloodGlucoseScreen),
    ("tiresize",      TireSizeScreen),
    # Phase 7 — Science
    ("concentration", ConcentrationScreen),
    ("raddose",       RadiationDoseScreen),
    ("humidity",      HumidityScreen),
    # About
    ("about",         AboutScreen),
]

if __name__ == "__main__":
    SHVLicenseGateApp().run()