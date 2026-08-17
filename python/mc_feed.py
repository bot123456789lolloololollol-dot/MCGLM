"""
Shared plumbing for the MCGLM overlay tools (features 3, 4, 5).

- FeedClient: listens for JSON datagrams sent by the feed Fabric mod
  (feed-mod/) on 127.0.0.1:5010 and hands each parsed message to your callback.
  Calling bind() both grabs a port and starts the listener thread.
- make_overlay(): creates a borderless, topmost, click-through pygame window
  using a magenta color key for transparency (works over windowed/borderless
  Minecraft; exclusive fullscreen cannot be overdrawn).

Port sharing: only one process can bind a UDP port, so FeedClient tries
5010 first and prints a note if it had to fall back. Whichever tool owns
5010 also relays every raw datagram to 5011/5012 inside its single reader
thread, so all three overlay tools can run at the same time.
"""

import json
import socket
import threading

import pygame

BASE_PORTS = (5010, 5011, 5012)   # 5010 = mod's target, 5011/5012 = relay fan-out
MAGENTA = (255, 0, 255)           # color key -> fully transparent pixels


class FeedClient(threading.Thread):
    """Daemon thread: recv -> relay (if base-port owner) -> handler(msg_dict).

    Single reader thread on purpose: two threads recvfrom()ing the same UDP
    socket would steal each other's datagrams.
    """

    def __init__(self, handler):
        super().__init__(daemon=True)
        self.handler = handler
        self._sock = None
        self.port = None
        self._owns_base = False

    def bind(self):
        """Grab the first free port (5010 -> 5011 -> 5012) and start listening."""
        for i, port in enumerate(BASE_PORTS):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            self._sock, self.port, self._owns_base = s, port, i == 0
            break
        else:
            raise OSError(f"no free feed port in {BASE_PORTS}")
        if not self._owns_base:
            print(f"feed note: port {BASE_PORTS[0]} is taken - listening on {port} "
                  f"(fine if that's another MCGLM tool relaying; no data will arrive "
                  f"if a foreign program holds {BASE_PORTS[0]})")
        self.start()
        return self.port

    def run(self):
        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if self._owns_base else None
        while True:
            data, _ = self._sock.recvfrom(65536)
            if relay_sock is not None:
                for port in BASE_PORTS[1:]:
                    try:
                        relay_sock.sendto(data, ("127.0.0.1", port))
                    except OSError:
                        pass
            try:
                msg = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(msg, dict):
                self.handler(msg)


# --------------------------------------------------------------------------
# Win32 transparent click-through overlay window
# --------------------------------------------------------------------------

def set_dpi_aware():
    """Make Windows report real pixels so overlay coordinates match the screen."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def make_overlay(size=None, pos=(0, 0), title="MCGLM overlay"):
    """Create the overlay window. Returns (screen_surface, (width, height)).

    size=None uses the primary monitor's full size; pos anchors the window
    (multi-monitor: pass the offset of the monitor you play on).
    """
    import ctypes
    import os

    set_dpi_aware()
    pygame.init()
    if size is None:
        size = pygame.display.get_desktop_sizes()[0]
    # SDL reads this env var when the window is created, so set it first
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{pos[0]},{pos[1]}"
    screen = pygame.display.set_mode(size, pygame.NOFRAME)
    pygame.display.set_caption(title)

    user32 = ctypes.windll.user32
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020   # click-through
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080    # keep it off the taskbar
    LWA_COLORKEY = 0x00000001

    hwnd = pygame.display.get_wm_info()["window"]
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                          style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW)
    # pixels exactly MAGENTA become see-through
    user32.SetLayeredWindowAttributes(hwnd, 0x00FF00FF, 0, LWA_COLORKEY)
    # actually raise it above everything and keep it there
    HWND_TOPMOST = ctypes.c_void_p(-1)
    SWP_NOSIZE, SWP_NOMOVE, SWP_SHOWWINDOW = 0x0001, 0x0002, 0x0040
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                        SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW)
    return screen, (size[0], size[1])
