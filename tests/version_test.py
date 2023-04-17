# vim:fenc=utf-8
#
# Copyright © 2023 n3xtchen <echenwen@gmail.com>
#
# Distributed under terms of the GPL-2.0 license.

"""
version.py
"""

from a190rithm.version import version

def test_version():
    """
    验证版本
    """
    assert isinstance(version, str)
