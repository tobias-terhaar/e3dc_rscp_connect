from __future__ import annotations

import logging
import re
import struct

from . import RscpTags

log_error_tags = False

RscpTypes = {
    "None": {"name": "None", "identifier": 0x00, "fmt": ""},
    "Bool": {"name": "Bool", "identifier": 0x01, "fmt": "?"},
    "Char8": {"name": "Char8", "identifier": 0x02, "fmt": "b"},
    "UChar8": {"name": "UChar8", "identifier": 0x03, "fmt": "B"},
    "Int16": {"name": "Int16", "identifier": 0x04, "fmt": "h"},
    "UInt16": {"name": "UInt16", "identifier": 0x05, "fmt": "H"},
    "Int32": {"name": "Int32", "identifier": 0x06, "fmt": "i"},
    "Uint32": {"name": "Uint32", "identifier": 0x07, "fmt": "I"},
    "Int64": {"name": "Int64", "identifier": 0x08, "fmt": "q"},
    "Uint64": {"name": "Uint64", "identifier": 0x09, "fmt": "Q"},
    "Float32": {"name": "Float32", "identifier": 0x0A, "fmt": "f"},
    "Double64": {"name": "Double64", "identifier": 0x0B, "fmt": "d"},
    "Bitfield": {"name": "Bitfield", "identifier": 0x0C, "fmt": "h"},
    "CString": {
        "name": "CString",
        "identifier": 0x0D,
        "fmt": "s",
        "variable_length": True,
    },
    "Container": {
        "name": "Container",
        "identifier": 0x0E,
        "fmt": "s",
        "variable_length": True,
    },
    "Timestamp": {"name": "Timestamp", "identifier": 0x0F, "fmt": "QI"},
    "ByteArray": {
        "name": "ByteArray",
        "identifier": 0x10,
        "fmt": "s",
        "variable_length": True,
    },
    "Container_compressed": {
        "name": "Container_compressed",
        "identifier": 0x11,
        "fmt": "",
    },
    "Error8": {
        "name": "Error8",
        "identifier": 0xFF,
        "fmt": "B",
    },  # TODO: Bug in implemenation? data len in case of ERROR is 4 but inside is only 1 byte! BUt only for AuthError
    "Error32": {
        "name": "Error32",
        "identifier": 0xFF,
        "fmt": "I",
    },  # this is the correct error value!
}

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class RscpValue:
    """The format of a RscpValue inside a RscpFrame is:
    32bit Tag | 8 bit Type | 16 bit Length | x byte Data |
    """

    rscpValueHeaderFmt = "IBH"

    @classmethod
    def getDataLength(self, buffer):
        return self.readHeader(buffer)[0]

    @classmethod
    def readHeader(self, buffer):
        header_size = self.getHeaderSize()
        tag_code, type, data_length = struct.unpack(
            "<{}".format(self.rscpValueHeaderFmt), buffer[0:header_size]
        )
        return tag_code, type, data_length

    @classmethod
    def getHeaderSize(self):
        return struct.calcsize(f"<{self.rscpValueHeaderFmt}")

    @staticmethod
    def construct_rscp_value(tag_name, value) -> RscpValue:
        """Helper function to construct a rscp container value from nested lists."""
        if isinstance(value, list):
            rscp_value = []
            for _value in value:
                rscp_value.append(RscpValue.construct_rscp_value(_value[0], _value[1]))
            return RscpValue().withTagName(tag_name, rscp_value)

        return RscpValue().withTagName(tag_name, value)

    @staticmethod
    def get_RscpValue_by_filter(_values, filter_string):
        # check if filter_string contains a tag, filtered by a subtag, eg. TAG_PVI_DATA(TAG_PVI_INDEX==0)
        log.debug("filtering for %s", filter_string)
        _re = re.compile(r"(.*)\((.*)==(.*)\)")
        match = _re.findall(filter_string)
        if match:
            interested_tag, filter_tag, filter_value = match[0]
            log.debug(
                "searching for %s, %s, %s", interested_tag, filter_tag, filter_value
            )
            for x in _values:
                log.debug(
                    f"searching tag name {interested_tag}, current:{x.getTagName()} "
                )
                if x.getTagName() == interested_tag:
                    log.debug(f"found matching tag: {x.getTagName()}")
                    for y in x.getValue():
                        log.debug(
                            f"searching filter tag: {filter_tag}, current: {y.getTagName()}"
                        )
                        if (
                            y.getTagName() == filter_tag
                            and str(y.getValue()) == filter_value
                        ):
                            log.debug("found filter tag, with matching value!")
                            return x
        else:
            if isinstance(_values, list):
                for x in _values:
                    if x.getTagName() == filter_string:
                        return x
        return None

    @staticmethod
    def get_tag_by_path(_value, filter_string_complete) -> RscpValue:
        """Tries to find an RscpTag by the given path.

        The path has the following format:

        TAG_1/TAG_2/TAG_3: Search for TAG_3 in a container of TAG_2 in a container of TAG_1
        TAG_1(TAG_INDEX==0): search for a container named TAG_1 which contains a tag TAG_INDEX with value0!
            The container TAG_1 is returned then!
        TAG_1(TAG_INDEX==3)/TAG_2(TAG_INDEX==1)/TAG_3": The path can also be chained! This example will return
            TAG_3 which is a container named TAG_2 which contains also a TAG_INDEX with value 1 and is in a container
            TAG_1 which also contains a TAG_INDEX tag with value 3.
        """
        searched_rscp_value = None
        splitted_filter_string = filter_string_complete.split("/")
        search_values = _value
        for x, filter_string in enumerate(splitted_filter_string):
            found_tag = RscpValue.get_RscpValue_by_filter(search_values, filter_string)
            if found_tag:
                if x == len(splitted_filter_string) - 1:
                    searched_rscp_value = found_tag
                    break
                search_values = found_tag.getValue()

        return searched_rscp_value

    def withTagName(self, tagname, value):
        self.__tagname = tagname
        self.__value = value
        self.__tag_description = RscpTags.rscpTags[tagname]
        self.__type = self.__tag_description["type"]
        return self

    def withBuffer(self, buffer):
        self.unpack(buffer)
        return self

    def getTagName(self):
        return self.__tagname

    def isTag(self, tagname):
        return self.__tagname == tagname

    def is_container(self):
        "Returns true if this RscpValue is a container."
        return self.__type == "Container"

    def has_child_tag(self, tag_name: str) -> bool:
        "Checks if this tag has a child of name tag_name."
        if self.__type != "Container":
            return False

        return any(x.isTag(tag_name) for x in self.getValue())

    def get_child(self, tag_name) -> RscpValue | None:
        "Returns the first found child of tag_name in the container!"
        if not self.is_container():
            return None

        for x in self.getValue():
            if x.isTag(tag_name):
                return x
        return None

    def get_childs(self, tag_name) -> list[RscpValue]:
        "Returns all found childs of tag_name in the container!"
        if not self.is_container():
            return []

        return [x for x in self.getValue() if x.isTag(tag_name)]

    def getValue(self):
        return self.__value

    def getPackedDataSize(self) -> int:
        """will return the length the data would have if it is packed to frame format"""

        header_size = self.getHeaderSize()
        data_size = 0
        if self.__type == "Container":
            # container needs special handling, because it has nested RscpValues!
            for x in self.__value:
                data_size += x.getPackedDataSize()
        else:
            data_fmt = RscpTypes[self.__type]["fmt"]
            if data_fmt == "s":
                # if the data format is a string, we need to calculate the string length
                data_fmt = f"{len(self.__value)}s"
            data_size = struct.calcsize(data_fmt)

        return header_size + data_size

    def pack(self) -> bytes:
        """packs the data to raw bytes so that it can be transferred over the line"""
        tag_type = RscpTypes[self.__tag_description["type"]]
        type_identifier = tag_type["identifier"]
        type_name = tag_type["name"]
        tag_code = self.__tag_description["tagvalue"]

        data_fmt = tag_type["fmt"]
        if data_fmt == "":
            data_length = 0
            data = tag_code, type_identifier, data_length
        elif data_fmt == "s":
            if type_name == "CString":
                data_length = len(self.__value)
                data_fmt = "{}s".format(data_length)
                data = tag_code, type_identifier, data_length, self.__value.encode()
            elif type_name == "Container":
                if not isinstance(self.__value, list):
                    raise ValueError("container requires list of RscpValues as value")

                containerdata = b""
                for value in self.__value:
                    data = value.pack()
                    containerdata += data

                data_length = len(containerdata)
                data_fmt = "{}s".format(data_length)
                data = tag_code, type_identifier, data_length, containerdata
            else:
                raise NotImplementedError(f"{type_name} support not yet finished")
        else:
            data_length = struct.calcsize(data_fmt)
            data = tag_code, type_identifier, data_length, self.__value

        # concat value header fmt and data fmt
        fmt = "<{}{}".format(self.rscpValueHeaderFmt, data_fmt)
        return struct.pack(fmt, *data)

    def unpack(self, buffer):
        """unpacks a raw bytes stream and constructs an RscpValue"""
        self.isError = False

        header_size = struct.calcsize(self.rscpValueHeaderFmt)
        tag_code, type, data_length = self.readHeader(buffer)

        tag = RscpTags.findTagValue(tag_code)
        if tag is None:
            raise ValueError(f"Tag 0x{tag_code:08X} not found!")

        self.__tagname = list(tag.keys())[0]
        self.__tag_description = tag[self.__tagname]

        if type == 0xFF:
            # special error type handling
            if data_length == 1:
                self.__type = "Error8"
            elif data_length == 4:
                self.__type = "Error32"
            else:
                raise ValueError(f"unknown length ({data_length}) of error tag!")
            if log_error_tags:
                log.error(f"received ERROR Tag: {tag_code:08X} {self.__tagname}!")
            expected_tag_type = RscpTypes[self.__type]
            self.isError = True
        else:
            try:
                expected_tag_type = RscpTypes[self.__tag_description["type"]]
            except KeyError:
                raise ValueError(
                    f"received an unknown rscp type: {self.__tag_description['type']}"
                )

        # special workaround for TAG_RSCP_AUTHENTICATION:
        # if authentifaction fails, the level is send back as Int32 value
        if (
            tag_code == RscpTags.rscpTags["TAG_RSCP_AUTHENTICATION"]["tagvalue"]
            and type == 0x06
        ):
            expected_tag_type = RscpTypes["Int32"]

        type_variable = self.__tag_description.get("type_variable", False)
        if type_variable == False:
            if type != expected_tag_type["identifier"]:
                raise ValueError(
                    f"Data Type identifier not matching for tag: {self.__tagname} (0x{tag_code:08X})! ({type} != {expected_tag_type['identifier']})"
                )
        else:
            # search correct expected format:
            for key, value in RscpTypes.items():
                if value["identifier"] == type:
                    expected_tag_type = value

        data_fmt = "{}".format(expected_tag_type["fmt"])
        data_type_name = expected_tag_type["name"]
        if data_fmt == "":
            self.__value = None
            return
        elif data_fmt == "s":
            if data_type_name == "CString":
                data_fmt = f"{data_length}s"
                # if data_length + header_size > len(buffer):
                #    raise ValueError("corrupt datalength field!")
            elif data_type_name == "Container":
                self.__type = data_type_name
                self.__value = self.__unpackContainer(
                    buffer[header_size - 1 : header_size - 1 + data_length]
                )
                return
            else:
                raise NotImplementedError(f"{data_type_name} support not yet finished")
        else:
            # add endian
            data_fmt = f"<{data_fmt}"

        data_size = struct.calcsize(data_fmt)

        self.__value = struct.unpack(
            data_fmt, buffer[header_size - 1 : header_size - 1 + data_size]
        )[0]

        if data_type_name == "CString":
            self.__value = self.__value.decode()

        self.__type = data_type_name

        if self.isError and log_error_tags:
            log.error(f"Error Data {self.__value}")

    def __unpackContainer(self, buffer):
        values = []
        data_position = 0
        while data_position < len(buffer):
            value = RscpValue().withBuffer(buffer[data_position:])
            values.append(value)
            data_position += value.getPackedDataSize()

        return values

    def toString(self, prefix=""):
        retVal: str = ""
        if self.__type == "Container":
            retVal = "{} {}: ==>>\n".format(prefix, self.__tagname)
            prefix = "+" + prefix
            for x in self.__value:
                retVal += x.toString(prefix) + "\n"
            return retVal

        retVal = "{} {}: {}".format(prefix, self.__tagname, self.__value)
        return retVal

    def print(self):
        if self.__type == "Container":
            print(f"Container: {self.__tagname}")
            for x in self.__value:
                x.print()
            return

        print("{}: {}".format(self.__tagname, self.__value))
