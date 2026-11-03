import sys
import os
import queue
import threading
import logging
import winreg
from pathlib import Path

import keyboard
import pystray
from PIL import Image, ImageDraw
from comtypes import CoInitialize, CoUninitialize, CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
from pycaw.api.endpointvolume import IAudioEndpointVolume

APP = "MicroToggle"
BASE = Path(os.environ["LOCALAPPDATA"]) / APP
BASE.mkdir(parents=True, exist_ok=True)
LOG_PATH = BASE / "microtoggle.log"
logging.basicConfig(
    filename=str(LOG_PATH), level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
commands = queue.Queue()


def thread_error(args):
    logging.critical(
        "Erreur non geree dans un thread",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = thread_error


def startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP)
        return True
    except FileNotFoundError:
        return False


def startup_command():
    if getattr(sys, "frozen", False):
        return '"' + sys.executable + '"'
    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    if pythonw.exists():
        executable = pythonw
    return '"' + str(executable) + '" "' + str(Path(__file__).resolve()) + '"'


def notify(icon, message):
    try:
        icon.notify(str(message), APP)
    except Exception:
        logging.exception("Notification impossible")


def toggle_startup(icon, item):
    try:
        enabled = startup_enabled()
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if enabled:
                winreg.DeleteValue(key, APP)
            else:
                winreg.SetValueEx(key, APP, 0, winreg.REG_SZ, startup_command())
        icon.update_menu()
        logging.info("Demarrage automatique : %s", not enabled)
    except Exception as exc:
        logging.exception("Demarrage automatique")
        notify(icon, exc)


def picture(muted=None):
    image = Image.new("RGB", (64, 64), "#202020")
    draw = ImageDraw.Draw(image)
    color = "#888888" if muted is None else ("#ef4444" if muted else "#22c55e")
    draw.rounded_rectangle((24, 9, 40, 38), radius=8, fill=color)
    draw.arc((17, 22, 47, 48), 0, 180, fill=color, width=4)
    draw.line((32, 47, 32, 55), fill=color, width=4)
    draw.line((23, 55, 41, 55), fill=color, width=4)
    if muted:
        draw.line((10, 9, 54, 55), fill="white", width=4)
    return image


def endpoints():
    enumerator = AudioUtilities.GetDeviceEnumerator()
    devices = enumerator.EnumAudioEndpoints(1, 1)
    result = []
    for index in range(devices.GetCount()):
        device = devices.Item(index)
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        # QueryInterface owns its COM reference; do not replace with ctypes.cast.
        volume = interface.QueryInterface(IAudioEndpointVolume)
        result.append(volume)
    if not result:
        raise RuntimeError("Aucun microphone actif detecte.")
    return result


def audio_action(action):
    # Keep COM pointers inside this call, on the initialized audio thread.
    volumes = endpoints()
    try:
        muted = all(bool(volume.GetMute()) for volume in volumes)
        if action == "toggle":
            muted = not muted
            for volume in volumes:
                volume.SetMute(int(muted), None)
        elif action in ("mute", "unmute"):
            muted = action == "mute"
            for volume in volumes:
                volume.SetMute(int(muted), None)
        return muted
    finally:
        volumes.clear()


def audio_worker(icon):
    CoInitialize()
    last_state = object()
    error_active = False
    logging.info("Thread audio demarre")
    try:
        while True:
            try:
                action = commands.get(timeout=1)
            except queue.Empty:
                action = "refresh"
            if action == "quit":
                break
            try:
                muted = audio_action(action)
                if muted != last_state or error_active:
                    icon.icon = picture(muted)
                    icon.title = APP + (" : micros coupes" if muted else " : micro actif")
                    last_state = muted
                error_active = False
                if action != "refresh":
                    logging.info("Action %s : mute=%s", action, muted)
            except Exception as exc:
                if not error_active or action != "refresh":
                    logging.exception("Erreur audio")
                error_active = True
                try:
                    icon.title = APP + " : erreur (voir journal)"
                    icon.icon = picture()
                except Exception:
                    logging.exception("Mise a jour de l'icone impossible")
                if action != "refresh":
                    notify(icon, exc)
    finally:
        # All endpoint references have left audio_action before COM shutdown.
        CoUninitialize()
        logging.info("Thread audio termine")


def quit_app(icon, item):
    logging.info("Commande Quitter recue")
    commands.put("quit")
    icon.stop()


def main():
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_bool
    handle = kernel.CreateMutexW(None, False, r"Local\MicroTogglePython")
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    already_running = ctypes.get_last_error() == 183
    if already_running:
        logging.info("Autre instance deja ouverte : sortie")
        kernel.CloseHandle(handle)
        return

    logging.info("Demarrage ; Python %s", sys.version)
    icon = pystray.Icon(APP, picture(), APP, menu=pystray.Menu(
        pystray.MenuItem("Couper / reactiver (Shift + pave 9)",
                        lambda icon, item: commands.put("toggle"), default=True),
        pystray.MenuItem("Couper tous les micros", lambda icon, item: commands.put("mute")),
        pystray.MenuItem("Reactiver tous les micros", lambda icon, item: commands.put("unmute")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Demarrer avec Windows", toggle_startup,
                        checked=lambda item: startup_enabled()),
        pystray.MenuItem("Ouvrir le journal", lambda icon, item: os.startfile(str(LOG_PATH))),
        pystray.MenuItem("Quitter (sans changer le mute)", quit_app),
    ))
    held = False

    def on_key(event):
        nonlocal held
        try:
            if event.scan_code != 73 or not event.is_keypad:
                return
            if event.event_type == "up":
                held = False
            elif not held:
                held = True
                if keyboard.is_pressed("shift"):
                    commands.put("toggle")
        except Exception:
            logging.exception("Detection du raccourci")

    worker = None
    try:
        keyboard.hook(on_key, suppress=False)
        worker = threading.Thread(target=audio_worker, args=(icon,),
                                  name="audio_worker", daemon=True)
        worker.start()
        icon.run()
        logging.info("Boucle de l'icone terminee")
    finally:
        keyboard.unhook_all()
        commands.put("quit")
        if worker is not None:
            worker.join(timeout=5)
            if worker.is_alive():
                logging.warning("Le thread audio ne s'est pas arrete sous 5 secondes")
        kernel.CloseHandle(handle)
        logging.info("Fin de main")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Erreur fatale Python")
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None, "Erreur : consulter " + str(LOG_PATH), APP, 16,
        )
