# net_utils.py
import socket
import urllib.request

def is_online(timeout: int = 3) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
        return True
    except Exception:
        pass

    try:
        with urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=timeout) as r:
            return r.status == 204 or bool(r.status)
    except Exception:
        pass

    return False
