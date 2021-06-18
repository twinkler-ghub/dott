# vim: set tabstop=4 expandtab :
###############################################################################
#   Copyright (c) 2019-2021 ams AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################

# Authors:
# - Thomas Winkler, ams AG, thomas.winkler@ams.com

import logging
import struct
import threading
from typing import Union, List

log = logging.getLogger('DOTT')


def log_setup() -> None:
    # suppress log debug/info output on a general basis
    logging.getLogger().setLevel(logging.ERROR)
    # configure DOTT log level
    logging.getLogger('DOTT').setLevel(logging.DEBUG)


# -------------------------------------------------------------------------------------------------
def DOTT_LABEL(name: str) -> str:
    ret = f'DOTT_LABEL_{name}'
    return ret


# -------------------------------------------------------------------------------------------------
# used as decorator to implement singleton pattern
def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


# -------------------------------------------------------------------------------------------------
class DottConvert(object):
    @staticmethod
    def bytes_to_uint32(data: bytes, byte_order: str = 'little') -> Union[int, List[int]]:
        """
        This function takes a bytes variable and converts its content to an int, or if data is longer than four
        bytes, to an int list. The bytes are interpreted as uint32 integers.
        Args:
            data: Bytes to be converted to int / int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
        An int or and int list if data is longer than four bytes.
        """
        if (len(data) % 4) != 0:
            raise ValueError(f'Data shall have a length which is a multiple of 4!')

        if byte_order == 'little':
            ret_val = struct.unpack('<%dI' % (len(data) / 4), data)
        elif byte_order == 'big':
            ret_val = struct.unpack('>%dI' % (len(data) / 4), data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        if len(ret_val) == 1:
            return ret_val[0]
        else:
            return list(ret_val)

    @staticmethod
    def bytes_to_uint16(data: bytes, byte_order: str = 'little')  -> Union[int, List[int]]:
        """
        This function takes a bytes variable and converts its content to an int, or if data is longer than two
        bytes, to and int list. The bytes are interpreted as uint16 integers.
        Args:
            data: Bytes to be converted to int / int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
        An int or an int list if data is longer than two bytes.
        """
        if (len(data) % 2) != 0:
            raise ValueError(f'Data shall have a length which is a multiple of 2!')

        if byte_order == 'little':
            ret_val = struct.unpack('<%dH' % (len(data) / 2), data)
        elif byte_order == 'big':
            ret_val = struct.unpack('>%dH' % (len(data) / 2), data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        if len(ret_val) == 1:
            return ret_val[0]
        else:
            return list(ret_val)

    @staticmethod
    def bytes_to_int32(data: bytes, byte_order: str = 'little')  -> Union[int, List[int]]:
        """
        This function takes a bytes variable and converts its content to an int, or if data is longer than four
        bytes, to an int list. The bytes are interpreted as int32 integers.
        Args:
            data: Bytes to be converted to int / int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
        An int or and int list if data is longer than four bytes.
        """
        if (len(data) % 4) != 0:
            raise ValueError(f'Data shall have a length which is a multiple of 4!')

        if byte_order == 'little':
            ret_val = struct.unpack('<%di' % (len(data) / 4), data)
        elif byte_order == 'big':
            ret_val = struct.unpack('>%di' % (len(data) / 4), data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        if len(ret_val) == 1:
            return ret_val[0]
        else:
            return list(ret_val)

    @staticmethod
    def bytes_to_int16(data: bytes, byte_order: str = 'little') -> Union[int, List[int]]:
        """
        This function takes a bytes variable and converts its content to an int, or if data is longer than two
        bytes, to an int list. The bytes are interpreted as int16 integers.
        Args:
            data: Bytes to be converted to int / int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
        An int or and int list if data is longer than two bytes.
        """
        if (len(data) % 2) != 0:
            raise ValueError(f'Data shall have a length which is a multiple of 2!')

        if byte_order == 'little':
            ret_val = struct.unpack('<%dh' % (len(data) / 2), data)
        elif byte_order == 'big':
            ret_val = struct.unpack('>%dh' % (len(data) / 2), data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        if len(ret_val) == 1:
            return ret_val[0]
        else:
            return list(ret_val)

    @staticmethod
    def uint32_to_bytes(data: Union[int, List[int]], byte_order: str = 'little') -> bytes:
        """
        This function takes either an int or an int list and converts the integer(s) to bytes. The integers are
        are interpreted as uint32 integers.
        Args:
            data: An int or an int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
            A bytes object containing the serialized integer data.
        """
        if isinstance(data, int):
            data = [data]
        if byte_order == 'little':
            ret_val = struct.pack('<%dI' % len(data), *data)
        elif byte_order == 'big':
            ret_val = struct.pack('>%dI' % len(data), *data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        return ret_val

    @staticmethod
    def uint16_to_bytes(data: Union[int, List[int]], byte_order: str = 'little') -> bytes:
        """
        This function takes either an int or an int list and converts the integer(s) to bytes. The integers are
        are interpreted as uint16 integers.
        Args:
            data: An int or an int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
            A bytes object containing the serialized integer data.
        """
        if isinstance(data, int):
            data = [data]
        if byte_order == 'little':
            ret_val = struct.pack('<%dH' % len(data), *data)
        elif byte_order == 'big':
            ret_val = struct.pack('>%dH' % len(data), *data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        return ret_val

    @staticmethod
    def int32_to_bytes(data: Union[int, List[int]], byte_order: str = 'little') -> bytes:
        """
        This function takes either an int or an int list and converts the integer(s) to bytes. The integers are
        are interpreted as int32 integers.
        Args:
            data: An int or an int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns: A bytes object containing the serialized integer data.
        """
        if isinstance(data, int):
            data = [data]
        if byte_order == 'little':
            ret_val = struct.pack('<%di' % len(data), *data)
        elif byte_order == 'big':
            ret_val = struct.pack('>%di' % len(data), *data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        return ret_val

    @staticmethod
    def int16_to_bytes(data: Union[int, List[int]], byte_order: str = 'little') -> bytes:
        """
        This function takes either an int or an int list and converts the integer(s) to bytes. The integers are
        are interpreted as int16 integers.
        Args:
            data: An int or an int list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns: A bytes object containing the serialized integer data.
        """
        if isinstance(data, int):
            data = [data]
        if byte_order == 'little':
            ret_val = struct.pack('<%dh' % len(data), *data)
        elif byte_order == 'big':
            ret_val = struct.pack('>%dh' % len(data), *data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        return ret_val

    @staticmethod
    def float_to_bytes(data: Union[float, List[float]], byte_order: str = 'little') -> bytes:
        """
        This function takes either an float or a float list and converts the float(s) to bytes. The floats are
        are interpreted as 32bit floats.
        Args:
            data: An float or an float list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns: A bytes object containing the serialized float data.
        """
        if isinstance(data, float):
            data = [data]
        if byte_order == 'little':
            ret_val = struct.pack('<%df' % len(data), *data)
        elif byte_order == 'big':
            ret_val = struct.pack('>%df' % len(data), *data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        return ret_val

    @staticmethod
    def bytes_to_float(data: bytes, byte_order: str = 'little') -> Union[float, List[float]]:
        """
        This function takes a bytes variable and converts its content to a float, or if data is longer than four
        bytes, to a float list. The bytes are interpreted as 32bit floats.
        Args:
            data: Bytes to be converted to float / float list.
            byte_order: Either 'little' for little endian (default) or 'big' for big endian.

        Returns:
        A float or and float list if data is longer than four bytes.
        """
        if (len(data) % 4) != 0:
            raise ValueError(f'Data shall have a length which is a multiple of 4!')

        if byte_order == 'little':
            ret_val = struct.unpack('<%df' % (len(data) / 4), data)
        elif byte_order == 'big':
            ret_val = struct.unpack('>%df' % (len(data) / 4), data)
        else:
            raise ValueError(f'Unsupported byte order ({byte_order})!')

        if len(ret_val) == 1:
            return ret_val[0]
        else:
            return list(ret_val)


# -------------------------------------------------------------------------------------------------
def cast_str(data: Union[str, bytes]) -> Union[int, float, bool, str]:
    """
    This function attempts to 'smart-cast' data (received from GDB) as string into Python int, float, bool or, if
    other conversion fail, str types.
    Args:
        data: Data string to the interpreted/casted.

    Returns:
        Returns a Python int, float, bool or str containing the result of the cast operation.
    """
    if type(data) == bytes:
        data = data.decode('ascii')

    # single chars are returned by MI in a format like this: "2 '\\002'"
    # if this format is detected, it is split up such that an int is returned
    if " '" in str(data):
        data = str(data).split(" '")[0]

    if 'false' in str(data).lower():
        return False
    elif 'true' in str(data).lower():
        return True

    try:
        if data.startswith('0x'):
            tmp = data
            if ' <' in tmp:
                # function pointers typically are return in this format '0x0304 <func_name>'
                tmp = tmp.split(' <')[0]
            elif ' "' in tmp:
                # character pointers (char* and sometimes uint8_t*) are return in this format '0x65 ""'
                tmp = tmp.split(' "')[0]
            return int(tmp, 16)
    except Exception:
        # if the data is not just a 'pure' hex value (e.g., more (string) data after the hex value)
        pass

    for fn in (int, float):
        try:
            return fn(data)
        except ValueError:
            pass
        except TypeError:
            pass
    return data  # return as string


# -------------------------------------------------------------------------------------------------
class BlockingDict(object):
    def __init__(self):
        self._items = {}
        self._cv = threading.Condition()

    def put(self, key, value):
        with self._cv:
            self._items[key] = value
            self._cv.notify_all()

    def pop(self, key, timeout: float =None):
        with self._cv:
            while key not in self._items:
                new_item = self._cv.wait(timeout)
                if not new_item:
                    # timeout hit
                    raise TimeoutError

            return self._items.pop(key)
