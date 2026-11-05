"""
RFB protocol implementation, client side

(c) zocker-160 2024
licensed under GPLv3

References:
- http://www.realvnc.com/docs/rfbproto.pdf
- https://github.com/rfbproto/rfbproto/blob/master/rfbproto.rst
"""

from vnc_widget.rfbhelpers import RFBPixelformat, RFBRectangle
from vnc_widget.rfbdes import RFBDes
import vnc_widget.rfbconstants as c
import vnc_widget.easystruct as es

from threading import Thread
import logging
import socket
from socket import SHUT_RDWR
import struct as s
import time

class RFBUnexpectedResponse(Exception):
    pass
class RFBNoResponse(Exception):
    pass
class RFBUnknownVersion(Exception):
    pass
class RFBHandshakeFailed(Exception):
    pass
class VNCAuthentificationFailed(Exception):
    pass

SUPPORTED_VERSIONS = [
    (3,3)
]
KNOWN_VERSIONS = [
    (3,3), (3,6), (3,7), (3,8),
    (4,0), (4,1),
    (5,0)
]
"""
3.3: official minimum version
3.6: UltraVNC
3.7: official
3.8: official
4.0: Intel AMT KVM
4.1: RealVNC 4.6
5.0: RealVNC 5.3
"""

SUPPORTED_ENCODINGS = [
    c.ENC_RAW,
    # vnc_desktopsize_v1: pseudo-encoding que el servidor usa
    # para notificar cambios de resolucion del framebuffer sin
    # que el cliente tenga que reconectar.
    c.ENC_DESKTOPSIZE,
]

MAX_BUFF_SIZE: int = 10*1024*1024 # 10MB

class RFBClient:

    log = logging.getLogger("RFB Client")
    logc = logging.getLogger("RFB -> Server")
    logs = logging.getLogger("RFB Client <-")

    pixformat: RFBPixelformat
    numRectangles = 0
    #rectanglePositions = list() # list[RFBRectangle]

    _stop = False
    _connected = False
    _requestFrameBufferUpdate = False
    _incrementalFrameBufferUpdate = True

    def __init__(self, host, port = 5900,
                password: str = None, 
                sharedConnection = True,
                keepRequesting = True,
                requestIncremental = True):
        self.host = host
        self.port = port
        self.password = password
        self.sharedConn = sharedConnection
        self._requestFrameBufferUpdate = keepRequesting
        self._incrementalFrameBufferUpdate = requestIncremental

        # vnc_desktopsize_v2: cuando el servidor notifica un cambio de
        # resolucion via la pseudo-encoding DesktopSize, el protocolo
        # RFB exige que el cliente pida un framebuffer update NO
        # incremental a continuacion. Sin esto, QEMU se queda
        # esperando y no envia el siguiente frame (el widget se ve
        # congelado en el ultimo frame recibido).
        self._forceNonIncremental = False

        self._mainLoop: Thread = None

    def __recv(self, expectedSize: int = None, maxSize=MAX_BUFF_SIZE) -> bytes:
        if expectedSize == 0:
            return b""

        if not expectedSize:
            buffer = self.connection.recv(4096)
        else:
            buffer = self.connection.recv(expectedSize, socket.MSG_WAITALL)    

        if not buffer:
            return buffer

        if len(buffer) <= 50:
            self.logs.debug(f"len: {len(buffer)} | {buffer.hex()}")
        else:
            self.logs.debug(f"{len(buffer)} Bytes | {len(buffer)//1024} KB")

        return buffer

    def __send(self, data: bytes):
        try:  # vnc_broken_pipe_fix_v1
            self.connection.send(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            try:
                self.connection.close()
            except Exception:
                pass
            for _attr in ("connected", "is_connected", "_connected", "running"):
                if hasattr(self, _attr):
                    try:
                        setattr(self, _attr, False)
                    except Exception:
                        pass
            return
        self.logc.debug(data.hex())

    def __start(self):
        # Detectar si el host es una ruta a un Unix socket (empieza con /)
        # o un hostname/IP para TCP/IP. QEMU en Linux usa sockets Unix para
        # VNC cuando arranca con -vnc unix:/ruta/al/socket, que es más seguro
        # que un puerto TCP expuesto.
        #
        # vnc_desktopsize_v6: capturar FileNotFoundError y
        # ConnectionRefusedError aqui. Antes salia un traceback feo
        # en el hilo cuando la VM se apagaba y el socket desaparecia.
        try:
            if isinstance(self.host, str) and self.host.startswith("/"):
                self.connection = socket.socket(
                    socket.AF_UNIX, socket.SOCK_STREAM)
                self.connection.connect(self.host)
            else:
                self.connection = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.host, self.port))
        except FileNotFoundError:
            self.log.info(
                f"Socket VNC no existe ({self.host}); VM apagada?")
            self._dead = True
            return
        except ConnectionRefusedError:
            self.log.info(
                f"Conexion VNC rechazada ({self.host}:{self.port})")
            self._dead = True
            return
        self._handleInitial()

    def __close(self):
        self.log.debug("Closing connection")

        if self.connection:
            try:
                self.connection.shutdown(SHUT_RDWR)
                self.connection.close()
            except OSError:
                self.log.debug("TCP Connection already closed")

    def _handleInitial(self):
        try:
            buffer = self.__recv(12)

            if b'\n' in buffer and buffer.startswith(b'RFB'):
                maj, min = [int(x) for x in buffer[3:-1].split(b'.')]
                self.log.info(f"RFB from server: {maj}.{min}")

                if (maj, min) not in KNOWN_VERSIONS:
                    raise RFBUnknownVersion(f"Unknown RFB version by server: {maj}.{min}")

                if (maj, min) not in SUPPORTED_VERSIONS:
                    # request highest supported version

                    # TODO: requested version must not be higher than
                    # the one offered by the server
                    maj, min = SUPPORTED_VERSIONS[-1]

            else:
                self.__close()
                raise RFBUnknownVersion(buffer)

            self.version_maj, self.version_min = maj, min

            # request supported RFB version
            self.log.debug(f"Requesting RFB {maj}.{min}")
            self.__send(f"RFB 00{maj}.00{min}\n".encode())

            self.log.info("connected to VNC server")

            if (maj, min) == (3,3):
                self._handleAuth33(self.__recv(4))

            else:
                self.log.error(f"Missing AUTH implementation for {maj}.{min}")
        except ConnectionError:
            self._dead = True
            return
        except Exception:
            self._dead = True
            return


    def _handleAuth33(self, data: bytes):
        """
        Handle security handshake for protocol version 3.3.
        In this version, the server decides the protocol (failed, none or VNCAuth)
        """
        auth = es.return_uint32_val(data, True)

        if auth == c.AUTH_FAIL:
            self._handleConnFailed(self.__recv(4))
        elif auth == c.AUTH_NONE:
            self._doClientInit()
        elif auth == c.AUTH_VNCAUTH:
            self._handleVNCAuth(self.__recv(16))
        else:
            self.__close()
            raise RFBUnexpectedResponse(f"Unknown auth response {auth}")

    def _doClientInit(self):
        shared = 1 if self.sharedConn else 0
        self.__send(es.return_uint8_bytes(shared, True))
        self._handleServerInit(self.__recv(24))

    def _handleServerInit(self, data: bytes):
        try:
            self.vncWidth, self.vncHeight, pixformat, namelen = s.unpack("!HH16sI", data)
        except s.error as e:
            self.log.error("Handshake failed")
            self.__close()
            raise RFBHandshakeFailed(e)

        self.desktopname = self.__recv(namelen).decode()
        self.log.debug(f"Connecting to \"{self.desktopname}\"")

        pixformatData = s.unpack("!BBBBHHHBBBxxx", pixformat)
        self.pixformat = RFBPixelformat(*pixformatData)

        self.log.debug(f"Server Pixelformat: {self.pixformat}")
        self.log.debug(f"Resolution: {self.vncWidth}x{self.vncHeight}")

        # not actually part of RTB proto, but some VNC servers (like QT QPA VNC)
        # require this to send FramebufferUpdate
        self.setEncodings(SUPPORTED_ENCODINGS)

        self.onConnectionMade()
        self._connected = True

        # enter main request loop
        self._mainRequestLoop()

    def _handleVNCAuth(self, data: bytes):
        self._VNCAuthChallenge = data

        self.log.info("Requesting password")
        self.vncRequestPassword()
        self._handleVNCAuthResult(self.__recv(4))

    def _handleVNCAuthResult(self, data: bytes):
        try:
            result = es.return_uint32_val(data)
        except s.error as e:
            raise VNCAuthentificationFailed(f"Authentication failed ({str(e)})")
        self.log.debug(f"Auth result {result}")

        if result == c.SMSG_AUTH_OK:
            self._doClientInit()
        elif result == c.SMSG_AUTH_FAIL:
            if self.version_min > 7:
                self._handleVNCAuthError(self.__recv(4))
            else:
                raise VNCAuthentificationFailed("Authentication failed")
        elif result == c.SMSG_AUTH_TOOMANY:
            raise VNCAuthentificationFailed("Too many login attempts")
        else:
            self.log.error(f"Unknown Auth response ({result})")

    def _handleVNCAuthError(self, data: bytes):
        waitfor = es.return_uint32_val(data)
        raise VNCAuthentificationFailed(
            f"Authentication failed ({self.__recv(waitfor)})")

    def _handleConnFailed(self, data: bytes):
        waitfor = es.return_uint32_val(data)
        resp = self.__recv(waitfor)

        self.__close()
        raise RFBHandshakeFailed(resp)

    # ------------------------------------------------------------------
    ## Main request loop
    # ------------------------------------------------------------------

    def _mainRequestLoop(self):
        try:
            time.sleep(0.2)
            # first request is non incremental
            self.framebufferUpdateRequest(incremental=False)

            while not self._stop and self.connection:
                try:
                    dType = self.__recv(1)

                    # vnc_desktopsize_v5: si recv devuelve vacio,
                    # el socket esta cerrado (peer cerro la conexion
                    # o lo cerramos nosotros). Antes haciamos
                    # 'continue', lo que provocaba un busy-loop al
                    # 100% CPU cuando el peer cerraba limpiamente.
                    # Ahora salimos del loop: el hilo termina y el
                    # health tick del widget se encarga de reconectar
                    # si procede.
                    if len(dType) == 0:
                        if not self._stop:
                            self.log.info(
                                "Socket VNC cerrado por el peer")
                        break

                    start = time.time()
                    self._handleConnection(dType)

                    self.log.debug(f"processing update took: {(time.time() - start)*1e3} ms")
                except socket.timeout:
                    self.log.debug("timeout triggered")
                    continue
                except s.error as e:
                    self.log.exception(str(e))
                    continue
                except Exception as e:
                    self.onFatalError(e)

                #print("AAA")
                if self._requestFrameBufferUpdate:
                    # vnc_desktopsize_v2: si el ultimo frame traia un
                    # DesktopSize, forzar el proximo request a
                    # NO-incremental. El servidor (QEMU) solo manda el
                    # frame completo despues de un DesktopSize cuando
                    # el cliente lo pide explicitamente.
                    _inc = self._incrementalFrameBufferUpdate
                    if getattr(self, "_forceNonIncremental", False):
                        _inc = False
                        self._forceNonIncremental = False
                    self.framebufferUpdateRequest(incremental=_inc)
                #print("BBB")

            self.log.debug("loop exit")

        # ------------------------------------------------------------------
        ## Server -> Client messages
        # ------------------------------------------------------------------
        except ConnectionError:
            # El widget VNC fue destruido o la conexión se cerró.
            # Salir sin propagar la excepción: el hilo termina en
            # silencio, sin tumbar el proceso.
            self._dead = True
            return
        except Exception as _outer_e:
            # vnc_desktopsize_v6: loguear el motivo real.
            self.log.warning(
                f"RFB loop termino: {type(_outer_e).__name__}: {_outer_e}")
            self._dead = True
            return


    def _handleConnection(self, data: bytes):
        msgid = es.return_uint8_val(data)

        if msgid == c.SMSG_FBUPDATE:
            # Framebuffer Update
            self._handleFramebufferUpdate(self.__recv(3))
        elif msgid == c.SMSG_BELL:
            # bell
            self.onBell()
        elif msgid == c.SMSG_SERVERCUTTEXT:
            # server cut text
            self._handleServerCutText(self.__recv(7))
        elif msgid == c.SMSG_SETCOLORMAP:
            # set color map entries
            pass
        else:
            self.log.warning(f"Unknown message type recieved (id {msgid})")
            raise RFBUnexpectedResponse

    def _handleServerCutText(self, data: bytes):
        datalength = s.unpack("!xxxI", data)[0]
        data = self.__recv(datalength)

        self.log.debug(f"Server clipboard: {data}")
        # TODO: create callback

    def _handleFramebufferUpdate(self, data: bytes):
        numRectangles = s.unpack("!xH", data)[0]
        self.log.debug(f"numRectangles: {numRectangles}")

        self.onBeginUpdate()

        for _ in range(numRectangles):
            self._handleRectangle(self.__recv(12))

        self.onFramebufferUpdateFinished()

    def _handleRectangle(self, data: bytes):
        # vnc_desktopsize_v7: encoding como SIGNED int. Las pseudo-encodings de RFB
        # (DesktopSize = -223, Cursor = -239, etc.) son negativas. Si se
        # deserializan con "I" (unsigned), llegan como 4294967073 y la
        # comparacion con las constantes negativas falla.
        xPos, yPos, width, height, encoding = s.unpack("!HHHHi", data)

        # vnc_desktopsize_v3: deteccion implicita de cambio de
        # resolucion. Si el rectangulo excede el framebuffer que
        # tenemos, el servidor crecio sin avisarnos (bien porque no
        # manda la pseudo-encoding DesktopSize, bien porque la manda
        # pero se perdio). Tratamos el rect como si fuera la nueva
        # resolucion y recreamos el backbuffer.
        if encoding != c.ENC_DESKTOPSIZE:
            _needed_w = xPos + width
            _needed_h = yPos + height
            if _needed_w > self.vncWidth or _needed_h > self.vncHeight:
                _new_w = max(self.vncWidth, _needed_w)
                _new_h = max(self.vncHeight, _needed_h)
                self.log.info(
                    f"Rect {xPos}+{width}x{yPos}+{height} excede "
                    f"framebuffer {self.vncWidth}x{self.vncHeight}; "
                    f"recreando a {_new_w}x{_new_h}"
                )
                self.vncWidth = _new_w
                self.vncHeight = _new_h
                try:
                    self.onDesktopResize(_new_w, _new_h)
                except Exception as _e:
                    self.log.warning(f"onDesktopResize fallo: {_e}")

        # vnc_desktopsize_v1: pseudo-encoding. xPos/yPos se
        # ignoran; width/height llevan la nueva resolucion del
        # framebuffer del servidor. NO hay pixel data detras de
        # esta pseudo-rectangulo: el servidor mandara a
        # continuacion un framebuffer update con el contenido
        # nuevo. Se notifica al widget via onDesktopResize(),
        # que ya sabe recrear su backbuffer al tamano correcto.
        if encoding == c.ENC_DESKTOPSIZE:
            self.log.info(f"DesktopSize: {width}x{height}")
            self.vncWidth = width
            self.vncHeight = height
            # vnc_desktopsize_v2: obligar al siguiente request a ser
            # NO incremental. Sin esto, QEMU no envia el frame nuevo.
            self._forceNonIncremental = True
            try:
                self.onDesktopResize(width, height)
            except Exception as _e:
                self.log.warning(f"onDesktopResize fallo: {_e}")
            return

        rect = RFBRectangle(xPos, yPos, width, height)
        self.log.debug(f"RECT: {rect}")

        if encoding == c.ENC_RAW:
            size = (width*height*self.pixformat.bitspp) // 8
            self.log.debug(f"expected size: {size}")

            start = time.time()
            data = self.__recv(expectedSize=size)
            self.log.debug(f"fetching data took: {(time.time() - start)*1e3} ms")

            self._decodeRAW(data, rect)
            del data
        else:
            raise TypeError(f"Unsupported encoding received ({encoding})")


    # ------------------------------------------------------------------
    ## Image decoding stuff
    # ------------------------------------------------------------------        

    def _decodeRAW(self, data: bytes, rectangle: RFBRectangle):
        self.onRectangleUpdate(*rectangle.asTuple(), data)

    # ------------------------------------------------------------------
    ## Client -> Server messages
    # ------------------------------------------------------------------

    def setPixelFormat(self, pixelformat: RFBPixelformat):
        self.log.debug(f"Requesting pixelformat: {pixelformat}")

        self.pixformat = pixelformat
        pformat = s.pack("!BBBBHHHBBBxxx", *pixelformat.asTuple())
        self.__send(s.pack("!Bxxx16s", c.CMSG_SETPIXELFORMAT, pformat))

    def setEncodings(self, encodings: list):
        self.log.debug(f"Requesting encodings: {encodings}")

        self.__send(s.pack("!BxH", c.CMSG_SETENCODINGS, len(encodings)))
        for encoding in encodings:
            self.__send(es.return_sint32_bytes(encoding, True))

    def framebufferUpdateRequest(self,
            xPos=0, yPos=0,
            width=None, height=None,
            incremental=False):

        if not width: width = self.vncWidth - xPos
        if not height: height = self.vncHeight - yPos
        inc = 1 if incremental else 0

        self.__send(s.pack(
            "!BBHHHH",
            c.CMSG_FBUPDATEREQ, inc,
            xPos, yPos, width, height))

    def keyEvent(self, key, down=1):
        """
        For most ordinary keys, the "keysym" is the same as the corresponding ASCII value.
        Other common keys are shown in the KEY_ constants
        """
        self.log.debug(f'keyEvent: {key}, {"down" if down else "up"}')

        self.__send(s.pack("!BBxxI", c.CMSG_KEYEVENT, down, key))

    def pointerEvent(self, x: int, y: int, buttommask=0):
        """
        Indicates either pointer movement or a pointer button press or release. The pointer is
           now at (x-position, y-position), and the current state of buttons 1 to 8 are represented
           by bits 0 to 7 of button-mask respectively, 0 meaning up, 1 meaning down (pressed)
        """
        if not self._connected: return

        self.log.debug(f"pointerEvent: {x}, {y}, {buttommask}")
        self.__send(s.pack("!BBHH", c.CMSG_POINTEREVENT, buttommask, x, y))

    # ------------------------------------------------------------------
    ## Direct Calls
    # ------------------------------------------------------------------

    def startConnection(self):
        # vnc_desktopsize_v4: resetear _stop. Sin esto, tras un
        # reconnect() (que llama a closeConnection y deja _stop=True),
        # el nuevo hilo saldria inmediatamente al comprobar la
        # condicion del main loop. Es la causa de que "Forzar
        # reconexión" a veces no funcionase a la primera.
        self._stop = False
        self._dead = False
        self._mainLoop = Thread(target=self.__start)
        self._mainLoop.start()
    
    def sendPassword(self, password):
        if type(password) is str:
            password = password.encode("ascii")
        password = (password + bytes(8))[:8]
        des = RFBDes(password)
        self.__send(des.encrypt(self._VNCAuthChallenge))

    def reconnect(self):
        self.closeConnection()
        self.startConnection()

    def is_alive(self) -> bool:
        """vnc_desktopsize_v4: True si el hilo RFB esta corriendo."""
        if self._mainLoop is None:
            return False
        return self._mainLoop.is_alive()

    def closeConnection(self):
        self._stop = True
        self._connected = False
        self.__close()

        if self._mainLoop and self._mainLoop.is_alive():
            self.log.debug("waiting for main loop to exit")
            self._mainLoop.join()

    # ------------------------------------------------------------------
    ## Callbacks
    # ------------------------------------------------------------------

    def onConnectionMade(self):
        """
        connection is initialized and ready
        the pixel format and encodings can be set here using

        setPixelFormat() and setEncodings()

        the RFB main update loop will start after this function is done
        """

    def onBeginUpdate(self):
        """
        called before a series of updateRectangle(),
        copyRectangle() or fillRectangle().
        """

    def onRectangleUpdate(self,
            x: int, y: int, width: int, height: int, data: bytes):
        """
        new bitmap data. data are bytes in the pixel format set
        up earlier.
        """

    def onFramebufferUpdateFinished(self):
        """
        called after a series of updateRectangle(), copyRectangle()
        or fillRectangle() are finished.
        """

    def onDesktopResize(self, width: int, height: int):
        """
        vnc_desktopsize_v1: el servidor notifico un cambio de
        resolucion del framebuffer (DesktopSize pseudo-encoding).
        Las subclases que quieran redimensionar su buffer deben
        sobrescribir este metodo. La base no hace nada.
        """

    def onBell(self):
        """
        a bell, yes that's right a BELL
        """

    def vncRequestPassword(self):
        """
        a password is needed to log on, use sendPassword() to
        send one.
        """
        if not self.password:
            raise VNCAuthentificationFailed("No password specified")
        else:
            self.sendPassword(self.password)

    def onFatalError(self, error: Exception):
        """
        called when fatal error occurs
        which caused the main loop to crash

        you can try to reconnect here with reconnect()
        """
        # vnc_desktopsize_v8: distinguir errores benignos de cierre.
        # Cuando el widget se destruye (cambio de pestana, cambio
        # de VM, cierre), PyQt borra el objeto C++ subyacente. Si el
        # hilo RFB todavia esta vivo y toca el widget, lanza
        # RuntimeError. Eso NO es un error real: es un cierre que no
        # esperabamos. Lo logueamos como INFO y no disparamos
        # reconexion.
        msg = f"{type(error).__name__}: {error}"
        if (isinstance(error, RuntimeError)
                and "has been deleted" in str(error)):
            self.log.info(f"Widget destruido; cerrando RFB ({msg})")
            self._stop = True
            self._dead = True
            return
        # console_cleanup_v1: desconexiones del peer (VM apagada,
        # socket cerrado, red cortada) son cierres limpios, no
        # errores. Log INFO, no ERROR, y sin disparar reconexión.
        if isinstance(error, (ConnectionError, ConnectionResetError,
                              ConnectionAbortedError, BrokenPipeError)):
            self.log.info(f"Conexion VNC cerrada por el peer ({msg})")
            self._stop = True
            self._dead = True
            return
        # vnc_desktopsize_v6: loguear la causa antes de propagar.
        # Sin esto, el hilo RFB moria silenciosamente y era muy
        # dificil diagnosticar por que.
        self.log.error(f"RFB fatal error: {msg}")
        raise error


# vnc_desktopsize_v1_rfb_applied


# vnc_desktopsize_v2_applied


# vnc_desktopsize_v3_rfb_applied


# vnc_desktopsize_v4_rfb_applied


# vnc_desktopsize_v5_rfb_applied


# vnc_desktopsize_v6_rfb_applied


# vnc_desktopsize_v7_applied


# vnc_desktopsize_v8_rfb_applied


# console_cleanup_v1_rfb_applied
