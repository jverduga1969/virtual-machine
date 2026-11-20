"""DES (FIPS 46-3) de autocontención.

Se usa como reemplazo mínimo de la dependencia externa `pyDes`, que solo se
necesitaba para cifrar el desafío de autenticación VNC (DES-ECB, 8 bytes por
bloque). Implementa exactamente el mismo algoritmo; si `pyDes` está instalado
tendremos prioridad sobre esta implementación (ver vnc_widget/rfbdes.py).
"""

# Permutación inicial / final
IP = [
    58, 50, 42, 34, 26, 18, 10, 2,
    60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6,
    64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9, 1,
    59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5,
    63, 55, 47, 39, 31, 23, 15, 7,
]
FP = [
    40, 8, 48, 16, 56, 24, 64, 32,
    39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30,
    37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28,
    35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26,
    33, 1, 41, 9, 49, 17, 57, 25,
]

# Permutación de expansión E (32 -> 48 bits)
E = [
    32, 1, 2, 3, 4, 5,
    4, 5, 6, 7, 8, 9,
    8, 9, 10, 11, 12, 13,
    12, 13, 14, 15, 16, 17,
    16, 17, 18, 19, 20, 21,
    20, 21, 22, 23, 24, 25,
    24, 25, 26, 27, 28, 29,
    28, 29, 30, 31, 32, 1,
]

# Permutación P (tras los S-boxes)
P = [
    16, 7, 20, 21,
    29, 12, 28, 17,
    1, 15, 23, 26,
    5, 18, 31, 10,
    2, 8, 24, 14,
    32, 27, 3, 9,
    19, 13, 30, 6,
    22, 11, 4, 25,
]

# PC-1: 64 -> 56 bits (descarta cada 8º bit de paridad)
PC1 = [
    57, 49, 41, 33, 25, 17, 9,
    1, 58, 50, 42, 34, 26, 18,
    10, 2, 59, 51, 43, 35, 27,
    19, 11, 3, 60, 52, 44, 36,
    63, 55, 47, 39, 31, 23, 15,
    7, 62, 54, 46, 38, 30, 22,
    14, 6, 61, 53, 45, 37, 29,
    21, 13, 5, 28, 20, 12, 4,
]

# PC-2: 56 -> 48 bits
PC2 = [
    14, 17, 11, 24, 1, 5,
    3, 28, 15, 6, 21, 10,
    23, 19, 12, 4, 26, 8,
    16, 7, 27, 20, 13, 2,
    41, 52, 31, 37, 47, 55,
    30, 40, 51, 45, 33, 48,
    44, 49, 39, 56, 34, 53,
    46, 42, 50, 36, 29, 32,
]

# Desplazamientos circulares por ronda
SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

# S-boxes (8 x 4 x 16, codificadas como 8 listas de 64 entradas, fila*16+col)
SBOXES = [
    [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
     0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
     4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
     15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
    [15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
     3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
     0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
     13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],
    [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
     13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
     13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
     1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],
    [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
     13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
     10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
     3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],
    [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
     14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
     4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
     11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],
    [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
     10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
     9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
     4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],
    [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
     13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
     1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
     6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],
    [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
     1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
     7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
     2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11],
]


def _permute_int(value: int, table, in_bits: int) -> int:
    out = 0
    for pos in table:
        out = (out << 1) | ((value >> (in_bits - pos)) & 1)
    return out


def _make_subkeys(key64: int):
    key56 = _permute_int(key64, PC1, 64)
    c = (key56 >> 28) & 0x0FFFFFFF
    d = key56 & 0x0FFFFFFF
    subkeys = []
    for shift in SHIFTS:
        c = ((c << shift) | (c >> (28 - shift))) & 0x0FFFFFFF
        d = ((d << shift) | (d >> (28 - shift))) & 0x0FFFFFFF
        subkeys.append(_permute_int((c << 28) | d, PC2, 56))
    return subkeys


def _feistel(half: int, subkey: int) -> int:
    x = _permute_int(half, E, 32) ^ subkey
    out = 0
    for i in range(8):
        shift = 48 - 6 * (i + 1)
        chunk = (x >> shift) & 0x3F
        row = (((chunk >> 5) & 1) << 1) | (chunk & 1)
        col = (chunk >> 1) & 0x0F
        out = (out << 4) | SBOXES[i][row * 16 + col]
    return _permute_int(out, P, 32)


def _crypt(block_int: int, subkeys) -> int:
    b = _permute_int(block_int, IP, 64)
    left, right = (b >> 32) & 0xFFFFFFFF, b & 0xFFFFFFFF
    for key in subkeys:
        left, right = right, left ^ _feistel(right, key)
    pre = ((right << 32) | left)
    return _permute_int(pre, FP, 64)


def _decrypt(block_int: int, subkeys) -> int:
    # v = IP(cifrado) = R16 || L16; se separa y se intercambia para
    # deshacer las rondas con la clave invertida.
    v = _permute_int(block_int, IP, 64)
    right16, left16 = (v >> 32) & 0xFFFFFFFF, v & 0xFFFFFFFF
    left, right = left16, right16
    for key in reversed(subkeys):
        left, right = (right ^ _feistel(left, key)), left
    u = (left << 32) | right
    return _permute_int(u, FP, 64)


class des:
    """API compatible con `pyDes.des` (ECB, sin padding)."""

    def __init__(self, key, *_args, **_kwargs):
        self.setKey(key)

    def setKey(self, key):
        raw = bytes(key)[:8].ljust(8, b"\x00")
        self._key_bytes = raw
        self._subkeys = _make_subkeys(int.from_bytes(raw, "big"))
        return True

    def encrypt(self, data: bytes) -> bytes:
        return self._process(data, self._subkeys)

    def decrypt(self, data: bytes) -> bytes:
        out = bytearray()
        for offset in range(0, len(data), 8):
            block = data[offset:offset + 8]
            if len(block) < 8:
                block = block.ljust(8, b"\x00")
            cipher = _decrypt(int.from_bytes(block, "big"), self._subkeys)
            out += cipher.to_bytes(8, "big")
        return bytes(out)

    @staticmethod
    def _process(data: bytes, subkeys) -> bytes:
        out = bytearray()
        for offset in range(0, len(data), 8):
            block = data[offset:offset + 8]
            if len(block) < 8:
                block = block.ljust(8, b"\x00")
            cipher = _crypt(int.from_bytes(block, "big"), subkeys)
            out += cipher.to_bytes(8, "big")
        return bytes(out)


__all__ = ["des"]
