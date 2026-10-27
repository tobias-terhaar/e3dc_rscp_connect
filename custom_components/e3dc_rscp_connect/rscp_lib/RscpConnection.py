import asyncio
import logging
import socket

from .RscpEncryption import RscpEncryption
from .RscpFrame import RscpFrame
from .RscpValue import RscpValue

log = logging.getLogger(__name__)


class RscpConnectionException(Exception):
    pass


class RscpConnection:
    def __init__(
        self,
        host,
        port: int = 5033,
        ciphersuite: RscpEncryption = None,
        username=None,
        password=None,
    ):
        self.__host = host
        self.__port = port
        self.__ciphersuite = ciphersuite
        self.__username = username
        self.__password = password
        self.__auth_level = 0
        self.__clientsock = None

    async def connect(self):
        if self.is_connected():
            log.error("Cannot connect a already connected socket")
            return False

        self.__auth_level = 0

        log.debug(f"connecting to device: {self.__host} on port {self.__port}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(False)

        loop = asyncio.get_running_loop()

        try:
            await asyncio.wait_for(
                loop.sock_connect(client_socket, (self.__host, self.__port)), timeout=5
            )
        except TimeoutError as e:
            log.info("Connection timed out")
            client_socket.close()
            raise RscpConnectionException(str(e)) from e
        except OSError as e:
            log.info(f"Error while connecting to device {self.__host}: {str(e)}")
            client_socket.close()
            raise RscpConnectionException(str(e)) from e

        self.__clientsock = client_socket
        log.info("Connection established")

        if self.__ciphersuite:
            self.__ciphersuite.reset()

        return True

    def is_connected(self):
        if self.__clientsock is not None:
            return True
        return False

    def disconnect(self):
        if self.__clientsock is not None:
            self.__clientsock.close()
            self.__clientsock = None
            self.__auth_level = 0
            log.info("Connection closed")

    async def send(self, buffer):
        if self.__ciphersuite:
            buffer = self.__ciphersuite.encrypt(buffer)

        return await self._send(buffer)

    async def _send(self, buffer):
        if not self.is_connected():
            log.info(f"You cannot send data to a closed socket! ({self.__host})")
            return False
        try:
            log.debug(f"sending {len(buffer)} bytes of data")
            loop = asyncio.get_running_loop()
            await loop.sock_sendall(self.__clientsock, buffer)
            log.debug(f"sending done")
            return True
        except (TimeoutError, BrokenPipeError, ConnectionResetError, OSError) as e:
            log.error(f"Error while sending data to device {self.__host}: {str(e)}")
            self.disconnect()
            raise RscpConnectionException(
                "Peer disconnected, perpare reconnect!"
            ) from e
        except socket.error as e:
            log.error(f"Error while sending data to device {self.__host}: {str(e)}")
            raise RscpConnectionException(str(e))

    async def receive(self, timeout=1000):
        """Receive one RSCP response.

        TCP is a byte stream, so one ``sock_recv`` call is not guaranteed to
        contain a complete encrypted RSCP frame.  The first encrypted block
        contains the complete RSCP header; decrypt it to learn the frame
        length, then collect and decrypt the remaining cipher blocks.
        """
        if not self.__ciphersuite:
            return await self._receive(timeout)

        block_size = RscpEncryption.BLOCK_SIZE
        encrypted = b""
        while len(encrypted) < block_size:
            chunk = await self._receive(timeout)
            if not chunk:
                self.disconnect()
                raise RscpConnectionException(
                    "Peer closed the connection before the RSCP frame header arrived"
                )
            encrypted += chunk

        # CBC can only decrypt complete blocks.  The header is 18 bytes and
        # therefore always fits into the first Rijndael block.
        first_block = encrypted[:block_size]
        plaintext = self.__ciphersuite.decrypt(first_block)
        if plaintext is None:
            raise RscpConnectionException("Could not decrypt the RSCP frame header")

        try:
            frame_length = RscpFrame.getFrameLength(plaintext)
        except ValueError as err:
            raise RscpConnectionException(
                "Could not read the RSCP frame header"
            ) from err

        encrypted_frame_length = (
            (frame_length + block_size - 1) // block_size
        ) * block_size
        while len(encrypted) < encrypted_frame_length:
            chunk = await self._receive(timeout)
            if not chunk:
                self.disconnect()
                raise RscpConnectionException(
                    "Peer closed the connection before the complete RSCP frame arrived"
                )
            encrypted += chunk

        remaining_ciphertext = encrypted[block_size:encrypted_frame_length]
        if remaining_ciphertext:
            remaining_plaintext = self.__ciphersuite.decrypt(remaining_ciphertext)
            if remaining_plaintext is None:
                raise RscpConnectionException("Could not decrypt the RSCP frame body")
            plaintext += remaining_plaintext

        return plaintext

    async def _receive(self, timeout):
        try:
            log.debug(f"start data receiption")
            loop = asyncio.get_running_loop()
            buffer = await loop.sock_recv(self.__clientsock, 4096)
            log.debug(f"received {len(buffer)} bytes of data")
            return buffer
        except (TimeoutError, BrokenPipeError, ConnectionResetError, OSError) as e:
            log.error(f"Error while sending data to device {self.__host}: {str(e)}")
            self.disconnect()
            raise RscpConnectionException(
                "Peer disconnected, perpare reconnect!"
            ) from e
        except socket.error as e:
            log.error(f"Error while receiving data from device {self.__host}: {str(e)}")
            raise RscpConnectionException(str(e))

    async def authorize(self, username=None, password=None):
        if username:
            self.__username = username

        if password:
            self.__password = password

        auth_user = RscpValue().withTagName(
            "TAG_RSCP_AUTHENTICATION_USER", self.__username
        )
        auth_pw = RscpValue().withTagName(
            "TAG_RSCP_AUTHENTICATION_PASSWORD", self.__password
        )
        auth_container = auth_user = RscpValue().withTagName(
            "TAG_RSCP_REQ_AUTHENTICATION", [auth_user, auth_pw]
        )

        await self.send(RscpFrame().packFrame(auth_container))
        responseData = await self.receive()
        responseFrame = RscpFrame()
        responseFrame.unpack(responseData)

        response = responseFrame.getRscpValues()
        if response[0].isTag("TAG_RSCP_AUTHENTICATION"):
            log.info(f"Auth successfull, Level: {response[0].getValue()}")
            self.__auth_level = response[0].getValue()
            return self.__auth_level > 0

        return False

    def is_authorized(self):
        return self.__auth_level > 0
