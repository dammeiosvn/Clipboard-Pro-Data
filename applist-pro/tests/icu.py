"""ICU regex adapter for host-side parity checks with Apple's regex dialect.

Uses the system ICU C ABI (libicu on Linux or icucore on macOS). No pip modules.
This validates regex behavior, not iOS action execution or Apple's ICU version.
"""
import ctypes as c
import ctypes.util
import re

path = ctypes.util.find_library('icui18n') or ctypes.util.find_library('icucore')
if not path:
    raise RuntimeError('ICU library is required for the workflow interpreter tests')
lib = c.CDLL(path)
suffix = re.search(r'(?:\.so\.|\.)(\d+)(?:\.dylib)?$', path)
suffix = '_' + suffix.group(1) if suffix else ''


def fn(name, args, result):
    try:
        f = getattr(lib, name + suffix)
    except AttributeError:
        f = getattr(lib, name)
    f.argtypes, f.restype = args, result
    return f


U = c.POINTER(c.c_uint16)
E = c.POINTER(c.c_int32)
open_re = fn('uregex_open', [U, c.c_int32, c.c_uint32, c.c_void_p, E], c.c_void_p)
close_re = fn('uregex_close', [c.c_void_p], None)
set_text = fn('uregex_setText', [c.c_void_p, U, c.c_int32, E], None)
find_next = fn('uregex_findNext', [c.c_void_p, E], c.c_int8)
start_re = fn('uregex_start', [c.c_void_p, c.c_int32, E], c.c_int32)
end_re = fn('uregex_end', [c.c_void_p, c.c_int32, E], c.c_int32)
replace_all = fn('uregex_replaceAll', [c.c_void_p, U, c.c_int32, U, c.c_int32, E], c.c_int32)


def utf16(s):
    raw = s.encode('utf-16-le')
    return (c.c_uint16 * (len(raw) // 2 + 1)).from_buffer_copy(raw + b'\0\0'), len(raw) // 2


class Pattern:
    def __init__(self, pattern):
        self.pattern = pattern
        buf, n = utf16(pattern)
        status = c.c_int32(0)
        self.handle = open_re(buf, n, 0, None, c.byref(status))
        if status.value > 0:
            raise ValueError('ICU regex error %d: %r' % (status.value, pattern))

    def __del__(self):
        if getattr(self, 'handle', None):
            close_re(self.handle)

    def matches(self, text):
        buf, n = utf16(text)
        status = c.c_int32(0)
        set_text(self.handle, buf, n, c.byref(status))
        raw, result = text.encode('utf-16-le'), []
        while find_next(self.handle, c.byref(status)):
            lo = start_re(self.handle, 0, c.byref(status))
            hi = end_re(self.handle, 0, c.byref(status))
            result.append(raw[lo * 2:hi * 2].decode('utf-16-le'))
        if status.value > 0:
            raise ValueError('ICU matching error %d' % status.value)
        return result

    def replace(self, text, replacement):
        buf, n = utf16(text)
        rep, rn = utf16(replacement)
        status = c.c_int32(0)
        set_text(self.handle, buf, n, c.byref(status))
        required = replace_all(self.handle, rep, rn, None, 0, c.byref(status))
        if status.value > 0 and status.value != 15:
            raise ValueError('ICU replacement error %d' % status.value)
        status = c.c_int32(0)
        out = (c.c_uint16 * (required + 1))()
        size = replace_all(self.handle, rep, rn, out, required + 1, c.byref(status))
        if status.value > 0:
            raise ValueError('ICU replacement error %d' % status.value)
        return bytes(out)[:size * 2].decode('utf-16-le')


def matches(pattern, text):
    return Pattern(pattern).matches(text)


def replace(pattern, text, replacement):
    return Pattern(pattern).replace(text, replacement)
