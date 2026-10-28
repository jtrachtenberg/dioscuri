# Copied from cyberware-override/tools/wkhandles.py (2026-10-28) for mesh-work/finish_moving_parts.py.
"""WolvenKit JSON handles as shared Python objects, and back.

WolvenKit's serialized CR2W JSON writes a handle's object once, as
{"HandleId": "N", "Data": {...}}, and every later use as {"HandleRefId": "N"}.
Editing a graph (a quest phase's nodes and socket connections) by hand means
renumbering every handle, and `convert deserialize` fails if the ids are not
in document-encounter order (CLAUDE.md, "WolvenKit JSON authoring gotcha").

load(path) resolves every handle into ONE shared dict (its Data), wrapped as
Handle; dump(obj, path) writes it back, numbering handles in document order
and emitting a ref for every encounter after the first. So a new node is added
by building dicts and appending Handle wrappers where they belong.
"""
import json


class Handle:
    """One handle: the same Data dict wherever the handle appears."""
    __slots__ = ('data',)

    def __init__(self, data):
        self.data = data


def _resolve(o, table):
    if isinstance(o, dict):
        if 'HandleId' in o and 'Data' in o:
            h = table.setdefault(o['HandleId'], Handle(None))
            h.data = _resolve(o['Data'], table)
            return h
        if 'HandleRefId' in o and len(o) == 1:
            return table.setdefault(o['HandleRefId'], Handle(None))
        return {k: _resolve(v, table) for k, v in o.items()}
    if isinstance(o, list):
        return [_resolve(v, table) for v in o]
    return o


def load(path):
    with open(path, encoding='utf-8') as f:
        return _resolve(json.load(f), {})


def _emit(o, ids):
    if isinstance(o, Handle):
        if id(o) in ids:
            return {'HandleRefId': ids[id(o)]}
        ids[id(o)] = str(len(ids))
        return {'HandleId': ids[id(o)], 'Data': _emit(o.data, ids)}
    if isinstance(o, dict):
        return {k: _emit(v, ids) for k, v in o.items()}
    if isinstance(o, list):
        return [_emit(v, ids) for v in o]
    return o


def dump(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(_emit(obj, {}), f, indent=2, ensure_ascii=False)
