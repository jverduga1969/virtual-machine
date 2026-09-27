
import logging
import vnc_widget.rfbconstants as c

from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt

class RFBPixelformat:
    def __init__(self,
        bpp=32, depth=24, bigendian=False, truecolor=True,
        redmax=255, greenmax=255, bluemax=255,
        redshift=0, greenshift=0, blueshift=16):

        self.bitspp = bpp
        self.depth = depth
        self.bigendian = 1 if bigendian else 0
        self.truecolor = 1 if truecolor else 0

        self.redmax = redmax
        self.greenmax = greenmax
        self.bluemax = bluemax
        
        self.redshift = redshift
        self.greenshift = greenshift
        self.blueshift = blueshift

    @staticmethod
    def getRGB32():
        return RFBPixelformat(
            bpp=32, depth=32,
            redshift=16, greenshift=8, blueshift=0
        )

    @staticmethod
    def getRGB24():
        return RFBPixelformat(
            bpp=32, depth=24,
            redshift=16, greenshift=8, blueshift=0
        )

    @staticmethod
    def getRGB16():
        return RFBPixelformat(
            bpp=16, depth=16,
            redmax=31, greenmax=63, bluemax=31,
            redshift=11, greenshift=5, blueshift=0
        )

    @staticmethod
    def getRGB555():
        return RFBPixelformat(
            bpp=16, depth=15,
            redmax=31, greenmax=31, bluemax=31,
            redshift=10, greenshift=5, blueshift=0
        )

    @staticmethod
    def getRGB444():
        return RFBPixelformat(
            bpp=16, depth=12,
            redmax=15, greenmax=15, bluemax=15,
            redshift=8, greenshift=4, blueshift=0
        )

    def asTuple(self) -> tuple:
        return (
            self.bitspp, self.depth, self.bigendian, self.truecolor,
            self.redmax, self.greenmax, self.bluemax,
            self.redshift, self.greenshift, self.blueshift
        )

    def __str__(self) -> str:
        return ";".join(str(x) for x in self.asTuple())

class RFBRectangle:
    def __init__(self, xPos: int, yPos: int, width: int, height: int):
        self.xPos = xPos
        self.yPos = yPos
        self.width = width
        self.height = height

    def asTuple(self) -> tuple:
        return (self.xPos, self.yPos, self.width, self.height)

    def __str__(self) -> str:
        return f"x: {self.xPos} y: {self.yPos} width: {self.width} height: {self.height}"

class RFBInput:

    # thanks to ken3 (https://github.com/ken3) for this
    # Mapa de botones: usamos int() como clave para que coincida
    # independientemente de si PyQt6 devuelve Qt.LeftButton o
    # Qt.MouseButton.LeftButton (ambos tienen el mismo valor).
    # Usamos int() porque PyQt6 no expone .value directamente
    # para los enums de MouseButton; int() sí funciona.
        # Valores numéricos estándar de Qt para los botones del ratón:
    #   LeftButton   = 1
    #   RightButton  = 2
    #   MiddleButton = 4
    # En PyQt6 los enums MouseButton no se pueden convertir a int()
    # ni tienen .value, así que usamos los literales directamente.
    # Estos valores coinciden con los bits del protocolo RFB.
    MOUSE_MAPPING = {
        1: 1 << 0,   # LeftButton   -> bit 0
        4: 1 << 1,   # MiddleButton -> bit 1
        2: 1 << 2,   # RightButton  -> bit 2
    }

    @staticmethod
    def fromQKeyEvent(eventID, eventStr: str) -> int:
        # En PyQt6, eventID es un enum Qt.Key. El diccionario
        # KEY_TRANSLATION_SPECIAL está indexado por esos mismos enums,
        # así que el lookup es directo (sin convertir a int).
        rfbKey = c.KEY_TRANSLATION_SPECIAL.get(eventID)

        if rfbKey is None:
            # Teclas imprimibles: eventStr contiene el carácter.
            # En PyQt6 eventStr es str (unicode).
            if eventStr and len(eventStr) == 1:
                try:
                    rfbKey = ord(eventStr)
                except TypeError:
                    logging.warning(f"Unknown keytype: {eventID} | {eventStr}")
                    return 0
            else:
                # Sin traducción especial ni texto: tecla desconocida.
                logging.debug(f"Unhandled key: {eventID!r} | {eventStr!r}")
                return 0

        # Log específico para teclas modificadoras
        if rfbKey in (0xFFE1, 0xFFE2, 0xFFE3, 0xFFE4, 0xFFE7, 0xFFE8, 0xFFE9, 0xFFEA, 0xFFEB, 0xFFEC):
            names = {
                0xFFE1: "Shift_L", 0xFFE2: "Shift_R",
                0xFFE3: "Control_L", 0xFFE4: "Control_R",
                0xFFE7: "Meta_L", 0xFFE8: "Meta_R",
                0xFFE9: "Alt_L", 0xFFEA: "Alt_R",
                0xFFEB: "Super_L", 0xFFEC: "Super_R",
            }
            import logging as _log
            _log.getLogger("RFBClient").info(f"MODIFIER: {names.get(rfbKey, hex(rfbKey))} = {hex(rfbKey)}")

        # Log específico para teclas modificadoras
        if rfbKey in (0xFFE1, 0xFFE2, 0xFFE3, 0xFFE4, 0xFFE7, 0xFFE8, 0xFFE9, 0xFFEA, 0xFFEB, 0xFFEC):
            names = {
                0xFFE1: "Shift_L", 0xFFE2: "Shift_R",
                0xFFE3: "Control_L", 0xFFE4: "Control_R",
                0xFFE7: "Meta_L", 0xFFE8: "Meta_R",
                0xFFE9: "Alt_L", 0xFFEA: "Alt_R",
                0xFFEB: "Super_L", 0xFFEC: "Super_R",
            }
            import logging as _log
            _log.getLogger("RFBClient").info(f"MODIFIER: {names.get(rfbKey, hex(rfbKey))} = {hex(rfbKey)}")

        return int(rfbKey)

    def fromQMouseEvent(eventID: QMouseEvent, pressEvent: bool, mask) -> int:
        # Convertir el enum MouseButton a int de forma robusta.
        # PyQt6 no permite int() ni .value en MouseButton, así que
        # usamos repr() y extraemos el número del string.
        _btn = eventID.button()
        try:
            _btn_int = int(_btn)
        except (TypeError, ValueError):
            # Fallback: parsear el repr tipo "<MouseButton.LeftButton: 1>"
            import re as _re
            m = _re.search(r":\s*(\d+)>", repr(_btn))
            _btn_int = int(m.group(1)) if m else 0
        _mask = RFBInput.MOUSE_MAPPING.get(_btn_int)

        # FIXME: return previous bitmask in case unknown key is pressed
        # TODO: implement all RFB supported buttons
        if not _mask: return mask
        
        if pressEvent:
            return mask | _mask
        else:
            return mask & ~_mask
