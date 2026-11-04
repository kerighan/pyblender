"""Ready-made motions as functions: ``motion.pop_in(title, ...)``.

They are the :class:`~pyblender.base.Group` methods of the same name, applied to a
split :class:`~pyblender.text.Text`, a ``Group`` or any list of objects. See the Group
class for the parameters; ``start`` defaults to the group playhead.
"""

from .base import Group

__all__ = ["pop_in", "pop_out", "slide_in", "slide_out", "flip_in", "flip_out",
           "typewriter", "wave", "shake", "as_group"]


def as_group(items):
    """A :class:`Group` from a split text, a group or any iterable of objects."""
    if isinstance(items, Group):
        return items
    if hasattr(items, "parts") and len(items.parts):
        return items.parts
    return Group(items)


def _delegate(name):
    def motion(items, *args, **kwargs):
        group = as_group(items)
        getattr(group, name)(*args, **kwargs)
        return items
    motion.__name__ = name
    motion.__doc__ = getattr(Group, name).__doc__
    return motion


pop_in = _delegate("pop_in")
pop_out = _delegate("pop_out")
slide_in = _delegate("slide_in")
slide_out = _delegate("slide_out")
flip_in = _delegate("flip_in")
flip_out = _delegate("flip_out")
typewriter = _delegate("typewriter")
wave = _delegate("wave")
shake = _delegate("shake")
