"""Protocolo RFB: endianness de longitud y DES con bits invertidos (Fase 0)."""

from vnc_widget import easystruct as es
from vnc_widget.rfbdes import RFBDes, pyDes


def test_uint32_de_length_es_big_endian():
    datos = b"\x00\x00\x01\x02"

    assert es.return_uint32_val(datos, True) == 258
    assert es.return_uint32_val(b"\x02\x01\x00\x00") == 258


def test_rfb_des_invierte_los_bits_de_la_clave():
    reto = bytes(range(8))
    rfb_des = RFBDes(b"password")

    cifrado = rfb_des.encrypt(reto)

    assert rfb_des.decrypt(cifrado) == reto
    # RFB difiere del DES estándar precisamente por la inversión de bits.
    assert cifrado != pyDes.des(b"password").encrypt(reto)
