"""Binary sample frames.

Layout (big-endian):

    0x21 | version u8 | watch_id u16 | frame_seq u32 | sample_seq u32 |
    dispatch_count u32 | t f64 | flags u8 | slot_count u8 |
    per slot: n u8, step u16 * n |
    PortValues (the same encoding as graph endpoints use)

When FLAG_TRUNCATED is set the PortValues part is a single zero byte (no
values) and the client only learns shapes from ``watch_ack``/activity.
"""

from __future__ import annotations

import struct

from ..port import port_values_to_bytes
from .reduce import FLAG_TRUNCATED, Reduced

FRAME_SAMPLE = 0x21
FRAME_VERSION = 1
_HEADER = struct.Struct(">BBHIIIdBB")


def encode_sample(
    watch_id: int,
    frame_seq: int,
    sample_seq: int,
    dispatch_count: int,
    t: float,
    reduced: Reduced,
) -> bytes:
    out = bytearray(
        _HEADER.pack(
            FRAME_SAMPLE,
            FRAME_VERSION,
            watch_id & 0xFFFF,
            frame_seq & 0xFFFFFFFF,
            sample_seq & 0xFFFFFFFF,
            dispatch_count & 0xFFFFFFFF,
            t,
            reduced.flags,
            len(reduced.steps),
        )
    )
    for step in reduced.steps:
        out += bytes([len(step)])
        out += struct.pack(f">{len(step)}H", *(min(s, 0xFFFF) for s in step))
    if reduced.flags & FLAG_TRUNCATED:
        out += b"\x00"
    else:
        port_values_to_bytes(reduced.values, reduced.types, out)
    return bytes(out)


def decode_header(frame: bytes) -> dict:
    """Parse the fixed header (used by tests and Python clients)."""
    kind, version, watch_id, frame_seq, sample_seq, count, t, flags, slots = _HEADER.unpack_from(frame)
    offset = _HEADER.size
    steps = []
    for _ in range(slots):
        n = frame[offset]
        offset += 1
        steps.append(struct.unpack_from(f">{n}H", frame, offset))
        offset += 2 * n
    return {
        "kind": kind,
        "version": version,
        "watch_id": watch_id,
        "frame_seq": frame_seq,
        "sample_seq": sample_seq,
        "dispatch_count": count,
        "t": t,
        "flags": flags,
        "steps": steps,
        "payload_offset": offset,
    }
