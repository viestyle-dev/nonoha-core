"""Binary sample frames.

Layout (big-endian):

    0x21 | version u8 | watch_id u16 | frame_seq u32 | sample_seq u32 |
    dispatch_count u32 | t f64 | flags u8 | slot_count u8 |
    per slot: n u8, step u16 * n |
    PortValues (the same encoding as graph endpoints use)

A frame always carries values: a sample too large to send is reported as an
``error`` message (code ``too_large``) instead. Flags: see
:mod:`nonoha_core.inspection.reduce`.
"""

from __future__ import annotations

import struct

from ..port import SHAPE_STRUCTS, port_values_to_bytes
from .reduce import Reduced

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
) -> bytearray:
    # Returned as the bytearray it is built in: converting it to bytes would
    # copy the whole frame once more (WebSocket sends take any bytes-like)
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
        n = len(step)
        out.append(n)
        out += (SHAPE_STRUCTS[n] if n < 8 else struct.Struct(f">{n}H")).pack(*(s if s <= 0xFFFF else 0xFFFF for s in step))
    port_values_to_bytes(reduced.values, reduced.types, out)
    return out


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
