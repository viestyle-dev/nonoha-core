"""Runtime inspection of port values (transport-agnostic, opt-in).

Hosts create an :class:`Inspector` with a graph resolver, open a session per
client with a non-blocking ``send``, and pass control operations (dicts) and
acknowledgements in. Nothing is observed and no task runs until a session
asks for something. See :mod:`nonoha_core.inspection.hub` for the protocol
and the safety rules, :mod:`nonoha_core.inspection.frames` for the binary
sample layout.
"""

from .frames import FRAME_SAMPLE, decode_header, encode_sample
from .hub import PROTOCOL_VERSION, Inspector, InspectorFull, Limits, Session
from .probe import PortRef
from .reduce import ReduceSpec, effective_type, reduce_values

__all__ = [
    "FRAME_SAMPLE",
    "PROTOCOL_VERSION",
    "Inspector",
    "InspectorFull",
    "Limits",
    "PortRef",
    "ReduceSpec",
    "Session",
    "decode_header",
    "effective_type",
    "encode_sample",
    "reduce_values",
]
