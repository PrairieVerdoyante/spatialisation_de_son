"""Utilities for Sonos management and simple GUI to input speaker IPs.

This module is designed to be imported from different parts of the project.

Key functions:
- ask_for_ips_gui(defaults=None): small Tkinter window returning a dict role->ip
- load_config(path) / save_config(path)
- roles_to_ordered_ips(role_map, order=('Front Gauche', 'Front Droite', 'Rear Gauche', 'Rear Droite'))
- discover_sonos(limit=4)
- connect_by_ips(ips, role_names=None)
- recover_devices(devices_or_ips)
- safe_group_and_play(devices, uri, master_index=0)
- set_volumes(devices, volumes)

The functions gracefully degrade if `soco` or `tkinter` are not available.
"""

from typing import Dict, List, Optional, Tuple
import json
import time
import threading

try:
    from soco import SoCo
    from soco.discovery import discover
    HAVE_SOCO = True
except Exception:
    SoCo = None
    discover = None
    HAVE_SOCO = False


def ask_for_ips_gui(defaults: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """Show a small Tkinter dialog to enter up to 4 speaker IPs.

    Returns a dict mapping role label -> ip, or None if cancelled or tkinter missing.
    Roles: 'Front Gauche', 'Front Droite', 'Rear Gauche', 'Rear Droite'
    """
    try:
        import tkinter as tk
    except Exception:
        return None

    roles = [
        ("Front Gauche", "FL"),
        ("Front Droite", "FR"),
        ("Rear Gauche", "RL"),
        ("Rear Droite", "RR"),
    ]

    root = tk.Tk()
    root.title("Configurer les IP Sonos")
    root.geometry('480x220')

    entries = {}
    for i, (label, key) in enumerate(roles):
        tk.Label(root, text=label).grid(row=i, column=0, sticky='w', padx=8, pady=4)
        var = tk.StringVar()
        if defaults and label in defaults:
            var.set(defaults[label])
        ent = tk.Entry(root, textvariable=var, width=50)
        ent.grid(row=i, column=1, padx=8, pady=4)
        entries[label] = var

    result = {}

    def on_ok():
        for label, key in roles:
            v = entries[label].get().strip()
            if v:
                result[label] = v
        root.destroy()

    def on_cancel():
        root.destroy()

    btn_ok = tk.Button(root, text='OK', width=12, command=on_ok)
    btn_ok.grid(row=len(roles), column=0, pady=10)
    btn_cancel = tk.Button(root, text='Annuler', width=12, command=on_cancel)
    btn_cancel.grid(row=len(roles), column=1, pady=10)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 3
    root.geometry(f'+{x}+{y}')

    root.mainloop()
    return result if result else None


def load_config(path: str) -> Optional[Dict[str, str]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_config(config: Dict[str, str], path: str) -> bool:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def roles_to_ordered_ips(role_map: Dict[str, str], order: Tuple[str, ...] = ("Front Gauche", "Front Droite", "Rear Gauche", "Rear Droite")) -> List[str]:
    """Return a list of IPs in the canonical order (TL,TR,BL,BR) derived from role_map.

    If a role is missing, its slot will be an empty string.
    """
    return [role_map.get(k, '') for k in order]


def discover_sonos(limit: int = 4) -> List[object]:
    """Discover Sonos devices using soco. Returns list of SoCo instances.

    If soco is not available, returns an empty list.
    """
    if not HAVE_SOCO:
        return []
    found = discover()
    if not found:
        return []
    devices = list(found)
    return devices[:limit]


def connect_by_ips(ips: List[str], role_names: Optional[List[str]] = None) -> List[Tuple[str, object]]:
    """Connect to Sonos devices given a list of IP addresses.

    Returns list of (role_name_or_ip, SoCo_instance) for successful connections.
    """
    result = []
    for i, ip in enumerate(ips):
        if not ip:
            continue
        name = role_names[i] if role_names and i < len(role_names) else ip
        try:
            dev = SoCo(ip) if HAVE_SOCO else None
            if dev:
                result.append((name, dev))
        except Exception as e:
            # skip unreachable devices
            print(f"connect_by_ips: failed {ip}: {e}")
    return result


def recover_devices(devices_or_ips: List[object]) -> None:
    """Stop and unjoin devices. Accepts list of SoCo instances or IP strings."""
    if not HAVE_SOCO:
        return
    for item in devices_or_ips:
        try:
            dev = item if hasattr(item, 'ip_address') or hasattr(item, 'player_name') else SoCo(item)
        except Exception:
            # couldn't construct SoCo from IP
            continue
        try:
            dev.stop()
        except Exception:
            pass
        try:
            dev.unjoin()
        except Exception:
            pass


def safe_group_and_play(devices: List[object], uri: str, master_index: int = 0, wait: float = 0.6) -> None:
    """Robustly group devices and play URI on the chosen master.

    devices: list of SoCo instances
    """
    if not HAVE_SOCO or not devices:
        print("safe_group_and_play: soco not available or no devices")
        return

    # 1) stop and unjoin all devices
    for d in devices:
        try:
            d.stop()
        except Exception:
            pass
        try:
            d.unjoin()
        except Exception:
            pass

    time.sleep(wait)

    # 2) join slaves to master
    master = devices[master_index]
    for dev in devices:
        if dev is master:
            continue
        try:
            dev.join(master)
        except Exception as e:
            print(f"safe_group_and_play: join failed for {getattr(dev,'player_name',dev)}: {e}")

    # 3) play on master
    try:
        master.play_uri(uri)
    except Exception as e:
        print(f"safe_group_and_play: play_uri failed on master: {e}")


def set_volumes(devices: List[object], volumes: List[int]) -> None:
    """Set volume per device. devices are SoCo instances; volumes is same-length list."""
    if not HAVE_SOCO:
        print("set_volumes: soco not available")
        return
    for dev, vol in zip(devices, volumes):
        try:
            dev.volume = int(max(0, min(100, vol)))
        except Exception as e:
            print(f"set_volumes: failed for {getattr(dev,'player_name',dev)}: {e}")


if __name__ == '__main__':
    # quick demo when run standalone
    print('sonos_utils demo')
    cfg = ask_for_ips_gui()
    if cfg:
        print('Got:', cfg)
    else:
        print('No GUI input or cancelled')
