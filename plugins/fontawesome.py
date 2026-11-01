# https://github.com/kura/pelican-fontawesome


from __future__ import unicode_literals

from docutils import nodes
from docutils.parsers.rst import roles


def fa(name, rawtext, text, lineno, inliner, options={}, content=[]):
    html = '<i class="{text}"></i>'.format(text=text)
    return [nodes.raw('', html, format='html')], []


def register():
    roles.register_local_role('fa', fa)