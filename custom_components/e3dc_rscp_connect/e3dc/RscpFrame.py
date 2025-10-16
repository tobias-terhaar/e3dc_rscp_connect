import logging
import struct
import time

from .RscpValue import RscpValue


log = logging.getLogger(__name__)


class RscpFrame:
    """The format of the header:
    | MAGIC 16bit | CTRL 16 bit | Time Sec 64 bit | Time Nanoseconds 32 bit | data_length 16 bit |
    """

    frame_header_fmt = f"<HHQIH"

    def __init__(self):
        log.debug("created frame")
        self.__values = None
        pass

    def getRscpValues(self):
        return self.__values

    @classmethod
    def getFrameLength(self, buffer):
        """returns the length of the frame, including header and data
        The function reads the data_length field from the buffer and calculates the frame length.
        """
        frame_header_size = struct.calcsize(RscpFrame.frame_header_fmt)
        if len(buffer) < frame_header_size:
            raise ValueError("buffer is to small to calculate header size!")

        magic, ctrl, time_seconds, time_nanoseconds, data_length = struct.unpack(
            RscpFrame.frame_header_fmt, buffer[0:frame_header_size]
        )

        return frame_header_size + data_length

    def packFrame(self, values):
        if isinstance(values, list):
            # raise NotImplementedError("list support not finished")
            value_data = b""
            for value in values:
                data = value.pack()
                value_data += data

            value_data_length = len(value_data)

        elif isinstance(values, RscpValue):
            value_data = values.pack()
            value_data_length = len(value_data)

        frame_fmt = f"<HHQIH{value_data_length}s"
        data = 0xDCE3, 0x0100, int(time.time()), 0, value_data_length, value_data

        return struct.pack(frame_fmt, *data)

    def unpack(self, buffer):
        frame_header_size = struct.calcsize(RscpFrame.frame_header_fmt)
        if len(buffer) < frame_header_size:
            raise ValueError("buffer is to small to calculate header size!")

        magic, ctrl, time_seconds, time_nanoseconds, data_length = struct.unpack(
            RscpFrame.frame_header_fmt, buffer[0:frame_header_size]
        )

        if magic != 0xDCE3:
            raise ValueError("buffer is not a valid frame!")

        total_frame_size = data_length + frame_header_size

        if len(buffer) < total_frame_size:
            raise ValueError("buffer to small, read more data")

        if len(buffer) > total_frame_size:
            log.info("buffer to big, cut of rest")

        buffer_rest = buffer[total_frame_size:]
        buffer = buffer[:total_frame_size]

        log.debug(f"RscpFrame data length: {data_length}")
        data_position = frame_header_size

        values = []
        while data_position < len(buffer):
            value = RscpValue().withBuffer(buffer[data_position:])
            values.append(value)
            data_position += value.getPackedDataSize()

        log.debug(f"received {len(values)} rscp values")
        self.__values = values
