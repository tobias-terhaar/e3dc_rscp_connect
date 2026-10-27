import py3rijndael
import logging

logger = logging.getLogger(__name__)


class NoPadding(py3rijndael.ZeroPadding):
    def encode(self, source: bytes) -> bytes:  # pragma: nocover
        raise NotImplementedError

    def decode(self, source: bytes) -> bytes:  # pragma: nocover
        return source


class RscpEncryption:
    KEY_SIZE = 32
    BLOCK_SIZE = 32

    def __init__(self, key):
        if len(key) > RscpEncryption.KEY_SIZE:
            log.error(f"Key must be smaller keysize ({RscpEncryption.KEY_SIZE})")
            raise ValueError(f"Key must be smaller keysize ({RscpEncryption.KEY_SIZE})")

        self.__key = key.encode() + b"\xff" * (RscpEncryption.KEY_SIZE - len(key))
        self.reset()

    def encrypt(self, plaintext: bytes) -> bytes:
        cipher = py3rijndael.RijndaelCbc(
            self.__key,
            self.__encryptionIV,
            padding=py3rijndael.ZeroPadding(RscpEncryption.BLOCK_SIZE),
            block_size=RscpEncryption.BLOCK_SIZE,
        )
        ciphertext = cipher.encrypt(plaintext)
        # store last block as IV for next encryption:
        self.__encryptionIV = ciphertext[(RscpEncryption.BLOCK_SIZE * -1) :]
        return ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        logger.debug(f"ciphertext: {ciphertext}")
        # if ciphertext length is not multiple of BLOCK_SIZE we cannot decrypt
        if len(ciphertext) % RscpEncryption.BLOCK_SIZE != 0:
            # TODO: do not simple discard the decryption here! Try to decrypt a part of the blokc if
            # len(ciphertext) > block size or try to receive some more data!
            return None

        cipher = py3rijndael.RijndaelCbc(
            self.__key,
            self.__decryptionIV,
            padding=NoPadding(RscpEncryption.BLOCK_SIZE),
            block_size=RscpEncryption.BLOCK_SIZE,
        )
        plaintext = cipher.decrypt(ciphertext)
        logger.debug(f"Plaintext ({len(plaintext)} bytes): {plaintext}")
        self.__decryptionIV = ciphertext[(RscpEncryption.BLOCK_SIZE * -1) :]
        return plaintext

    def reset(self):
        logger.debug("set IV vectors")
        self.__encryptionIV = b"\xff" * RscpEncryption.BLOCK_SIZE
        self.__decryptionIV = b"\xff" * RscpEncryption.BLOCK_SIZE
