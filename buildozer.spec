[app]

title = Universal Convertor by SHV
package.name = uniconvertorbyshv
package.domain = com.shvertex

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,csv,wav,ogg,html,htm,md
version = 7.0

requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,requests,certifi,rsa,pyasn1,pyjnius,filetype

orientation = portrait
fullscreen = 0

icon.adaptive_foreground.filename = foreground.png
icon.adaptive_background.filename = background.png

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True

# ── FIX: enables Swype / autocorrect / keyboard suggestions ──────────────────
# The SDL keyboard patch that fixes Android IME suggestions lives in p4a develop.
# Without this, inputType flags are set incorrectly at the Java layer and no
# Python-level fix can reach it.
p4a.branch = develop

# Ensures a clean bootstrap is compiled with the patched SDLActivity.java.
# Remove your .buildozer cache folder before rebuilding, otherwise the old
# compiled bootstrap (without the patch) will be reused and nothing will change.
android.p4a_whitelist_manage = True
# ─────────────────────────────────────────────────────────────────────────────

[buildozer]

log_level = 2
warn_on_root = 1
