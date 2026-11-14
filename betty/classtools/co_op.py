"""
Tools to create classes combining all other cooperative classtools APIs.

Unlike most other :py:mod:`classtools <betty.classtools>`, this module MUST NOT be used for type hints.
"""

from __future__ import annotations

from abc import ABCMeta

from betty.classtools.init import Init, InitClassVar, InitMeta, init


class CoOp(Init):
    """
    A fully cooperative class.
    """


class CoOpClassVar[OwnerT: Init](InitClassVar[OwnerT]):
    """
    A fully cooperative class variable.
    """


def co_op[T](cls: type[T]) -> type[T]:
    """
    Make a class fully cooperative.

    Subclasses will have to reapply this decorator.
    """
    if issubclass(cls, Init):
        cls = init(cls)
    return cls


class CoOpMeta(InitMeta):
    """
    Force all subclasses to be fully cooperative.
    """


class CoOpABCMeta(CoOpMeta, ABCMeta):
    """
    Force all abstract subclasses to be fully cooperative.
    """
