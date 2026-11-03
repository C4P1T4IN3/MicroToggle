import sys
import os
import queue
import threading
import logging
import winreg
from pathlib import Path
from ctypes import POINTER, cast

import keyboard
import pystray
from PIL import Image, ImageDraw
from comtypes import CoInitialize, CoUninitialize, CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
from pycaw.api.endpointvolume import IAudioEndpointVolume

APP = "MicroToggle"
BASE = Path(os.environ['LOCALAPPDATA']) / APP
BASE.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=str(BASE / 'microtoggle.log'), level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
commands = queue.Queue()


def startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP)
        return True
    except FileNotFoundError:
        return False


def startup_command():
    if getattr(sys, 'frozen', False):
        return '"' + sys.executable + '"'
    executable = Path(sys.executable)
    pythonw = executable.with_name('pythonw.exe')
    if pythonw.exists():
        executable = pythonw
    return '"' + str(executable) + '" "' + str(Path(__file__).resolve()) + '"'


def toggle_startup(icon, item):
    try:
        enabled = startup_enabled()
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if enabled:
                winreg.DeleteValue(key, APP)
            else:
                winreg.SetValueEx(key, APP, 0, winreg.REG_SZ, startup_command())
        icon.update_menu()
    except Exception as exc:
        logging.exception('Startup')
        icon.notify(str(exc), APP)


def picture(muted=None):
    image = Image.new('RGB', (64, 64), '#202020')
    draw = ImageDraw.Draw(image)
    color = '#888888' if muted is None else ('#ef4444' if muted else '#22c55e')
    draw.rounded_rectangle((24, 9, 40, 38), radius=8, fill=color)
    draw.arc((17, 22, 47, 48), 0, 180, fill=color, width=4)
    draw.line((32, 47, 32, 55), fill=color, width=4)
    draw.line((23, 55, 41, 55), fill=color, width=4)
    if muted:
        draw.line((10, 9, 54, 55), fill='white', width=4)
    return image


def endpoints():
    enumerator = AudioUtilities.GetDeviceEnumerator()
    devices = enumerator.EnumAudioEndpoints(1, 1)  # eCapture, DEVICE_STATE_ACTIVE
    result = []
    for index in range(devices.GetCount()):
        device = devices.Item(index)
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        result.append(cast(interface, POINTER(IAudioEndpointVolume)))
    if not result:
        raise RuntimeError('Aucun microphone actif detecte.')
    return result


def audio_worker(icon):
    CoInitialize()
    last_state = object()
    try:
        while True:
            try:
                action = commands.get(timeout=1)
            except queue.Empty:
                action = 'refresh'
            if action == 'quit':
                break
            try:
                volumes = endpoints()
                muted = all(bool(v.GetMute()) for v in volumes)
                if action == 'toggle':
                    muted = not muted
                    for volume in volumes:
                        volume.SetMute(int(muted), None)
                elif action in ('mute', 'unmute'):
                    muted = action == 'mute'
                    for volume in volumes:
                        volume.SetMute(int(muted), None)
                if muted != last_state:
                    icon.icon = picture(muted)
                    icon.title = APP + (' : micros coupes' if muted else ' : micro actif')
                    last_state = muted
            except Exception as exc:
                icon.title = APP + ' : erreur (voir journal)'
                icon.icon = picture()
                if action != 'refresh':
                    logging.exception('Audio')
                    icon.notify(str(exc), APP)
    finally:
        CoUninitialize()


def quit_app(icon, item):
    keyboard.unhook_all()
    commands.put('quit')
    icon.stop()


def main():
    # A named mutex avoids starting the application twice in this session.
    import ctypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, r'Local\MicroTogglePython')
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        return

    icon = pystray.Icon(APP, picture(), APP, menu=pystray.Menu(
        pystray.MenuItem('Couper / reactiver (Shift + pave 9)',
                        lambda icon, item: commands.put('toggle'), default=True),
        pystray.MenuItem('Couper tous les micros', lambda icon, item: commands.put('mute')),
        pystray.MenuItem('Reactiver tous les micros', lambda icon, item: commands.put('unmute')),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Demarrer avec Windows', toggle_startup,
                        checked=lambda item: startup_enabled()),
        pystray.MenuItem('Ouvrir le journal', lambda icon, item: os.startfile(str(BASE / 'microtoggle.log'))),
        pystray.MenuItem('Quitter (sans changer le mute)', quit_app),
    ))
    held = False

    def on_key(event):
        nonlocal held
        # Physical keypad 9 / Page Up: scan code 73, independent of Num Lock.
        # is_keypad excludes the separate Page Up navigation key.
        if event.scan_code != 73 or not event.is_keypad:
            return
        if event.event_type == 'up':
            held = False
        elif not held:
            held = True
            if keyboard.is_pressed('shift'):
                commands.put('toggle')

    keyboard.hook(on_key, suppress=False)
    worker = threading.Thread(target=audio_worker, args=(icon,), daemon=True)
    worker.start()
    try:
        icon.run()
    finally:
        keyboard.unhook_all()
        commands.put('quit')
        worker.join(timeout=3)
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception('Fatal')
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, 'Erreur : consulter ' + str(BASE / 'microtoggle.log'), APP, 16)
