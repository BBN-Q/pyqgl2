#!/usr/bin/env python3

# eyeball test for the debugmsg module
#
# assumes PYTHONPATH includes pyqgl2

from pyqgl2.debugmsg import DebugMsg as d

d.add_tag('foo', d.MEDIUM)
d.set_level(d.ALL)

print('----\nshould print\n' +
        """
"
DEBUG-0: debugmsg.py:14 (<module>) test ALL bar
DEBUG-1: debugmsg.py:16 (<module>) test LOW bar
DEBUG-2: debugmsg.py:17 (<module>) test MED foo
DEBUG-2: debugmsg.py:18 (<module>) test MED bar
DEBUG-3: debugmsg.py:19 (<module>) test HIGH foo
DEBUG-3: debugmsg.py:20 (<module>) test HIGH bar
"
""")


d.debug_msg('test ALL foo', tag='foo')
d.debug_msg('test ALL bar', tag='bar')
d.debug_msg('test LOW foo', level=d.LOW, tag='foo')
d.debug_msg('test LOW bar', level=d.LOW, tag='bar')
d.debug_msg('test MED foo', level=d.MEDIUM, tag='foo')
d.debug_msg('test MED bar', level=d.MEDIUM, tag='bar')
d.debug_msg('test HIGH foo', level=d.HIGH, tag='foo')
d.debug_msg('test HIGH bar', level=d.HIGH, tag='bar')

d.add_tag('foo', d.ALL)
d.set_level(d.NONE)

print('----\nshould print\n' +
        """
"
DEBUG-0: debugmsg.py:37 (<module>) test ALL foo
DEBUG-1: debugmsg.py:39 (<module>) test LOW foo
DEBUG-2: debugmsg.py:41 (<module>) test MED foo
DEBUG-3: debugmsg.py:43 (<module>) test HIGH foo
"
""")

d.debug_msg('test ALL foo', tag='foo')
d.debug_msg('test ALL bar', tag='bar')
d.debug_msg('test LOW foo', level=d.LOW, tag='foo')
d.debug_msg('test LOW bar', level=d.LOW, tag='bar')
d.debug_msg('test MED foo', level=d.MEDIUM, tag='foo')
d.debug_msg('test MED bar', level=d.MEDIUM, tag='bar')
d.debug_msg('test HIGH foo', level=d.HIGH, tag='foo')
d.debug_msg('test HIGH bar', level=d.HIGH, tag='bar')

print('%d %s' % (d.ACTIVE_LEVEL, str(d.ACTIVE_TAGS)))
