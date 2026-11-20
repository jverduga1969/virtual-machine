import logging

log = logging.getLogger(__name__)

try:
    # pyDes es la librería original del proyecto; si está instalada se prefiere.
    import pyDes
except ImportError:
    # Fallback autocontenido: implementación DES (FIPS 46-3) idéntica a la que
    # usa el reto de autenticación VNC (DES-ECB, bloques de 8 bytes).
    from vnc_widget._des import des as _FallbackDes

    class _PydesCompat:
        """Módulo mínimo compatible con pyDes cuando no está instalado."""

        class des(_FallbackDes):
            def __init__(self, key, *_args, **_kwargs):
                super().__init__(key)

    pyDes = _PydesCompat


class RFBDes(pyDes.des):
    """El protocolo RFB invierte el orden de los bits de cada byte de la
    contraseña antes de usarla como clave DES."""

    def setKey(self, key):
        newkey = list()
        for bsrc in key:
            btgt = 0
            for i in range(8):
                if bsrc & (1 << i):
                    btgt = btgt | (1 << 7 - i)
            newkey.append(btgt)
        super(RFBDes, self).setKey(bytes(newkey))