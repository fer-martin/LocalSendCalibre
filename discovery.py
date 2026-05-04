import socket
import struct
import json
import time
import uuid

MULTICAST_GROUP = '224.0.0.167'
MULTICAST_PORT = 53317


def discover_devices(timeout=4):
    """Descubre dispositivos LocalSend en la red local vía multicast UDP.
    
    Devuelve un dict {ip: info_dict}.
    """
    devices = {}
    fingerprint = str(uuid.uuid4())

    announcement = {
        "alias": "Calibre",
        "version": "2.0",
        "deviceModel": "Calibre",
        "deviceType": "desktop",
        "fingerprint": fingerprint,
        "port": MULTICAST_PORT,
        "protocol": "http",
        "download": False,
        "announce": True,
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # SO_REUSEPORT no existe en Windows
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass

    try:
        sock.bind(('', MULTICAST_PORT))
    except OSError as e:
        sock.close()
        raise RuntimeError(
            f"No se pudo enlazar al puerto {MULTICAST_PORT}: {e}. "
            "¿Hay otra app LocalSend corriendo en este PC?"
        )

    # Unirse al grupo multicast
    mreq = struct.pack('=4sl', socket.inet_aton(MULTICAST_GROUP),
                       socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    sock.settimeout(0.5)

    # Enviar nuestro anuncio para provocar respuestas inmediatas
    payload = json.dumps(announcement).encode('utf-8')
    try:
        sock.sendto(payload, (MULTICAST_GROUP, MULTICAST_PORT))
    except OSError:
        pass

    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            data, addr = sock.recvfrom(8192)
        except socket.timeout:
            continue
        except OSError:
            break

        try:
            info = json.loads(data.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue

        # Ignorar nuestro propio mensaje
        if info.get('fingerprint') == fingerprint:
            continue

        ip = addr[0]
        # Mantener la primera info que recibimos (o actualizar siempre)
        devices[ip] = info

        # Si el otro pidió anuncio, le respondemos con announce=False
        if info.get('announce'):
            response = dict(announcement)
            response['announce'] = False
            try:
                sock.sendto(json.dumps(response).encode('utf-8'),
                            (MULTICAST_GROUP, MULTICAST_PORT))
            except OSError:
                pass

    sock.close()
    return devices