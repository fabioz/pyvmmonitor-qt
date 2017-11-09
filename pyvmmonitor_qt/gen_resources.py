# Some resources (locally: pyvmmonitor/iconsets - not committed to git due to size)
#
# http://www.creativebloq.com/web-design/free-icon-sets-10134829
# http://modernuiicons.com/

import os
import subprocess

template = '''
<RCC>
  <qresource>
%(files)s
  </qresource>
</RCC>
'''


def generate_resources(resources_dir, output_file):
    files = []
    for f in sorted(os.listdir(resources_dir)):
        if f.endswith('.png') or f.endswith('.svg'):
            files.append('    <file>%s</file>' % f)

    resources_xml = template % dict(files='\n'.join(files))
    resources_xml_file = os.path.join(resources_dir, 'resources.xml')
    with open(resources_xml_file, 'w') as stream:
        stream.write(resources_xml)

    is_pyside1 = True
    try:
        import PySide
        pyrcc = os.path.join(os.path.dirname(PySide.__file__), 'pyside-rcc.exe')
    except ImportError:
        is_pyside1 = False
        import PySide2 as PySide
        for p in os.environ['PATH'].split(os.pathsep):
            pyrcc = os.path.join(p, 'pyside2-rcc')
            if os.path.exists(pyrcc):
                break
            pyrcc = os.path.join(p, 'pyside2-rcc.exe')
            if os.path.exists(pyrcc):
                break
            pyrcc = os.path.join(p, 'pyside2-rcc.sh')
            if os.path.exists(pyrcc):
                break
        else:
            raise AssertionError('Could not find pyrcc.')

    assert os.path.exists(pyrcc), 'Expected: %s to exist.' % (pyrcc,)
    p = subprocess.Popen(
        [pyrcc, resources_xml_file],
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = p.communicate()
    assert not stderr, stderr

    replacement = 'from pyvmmonitor_qt.qt import QtCore, QtSvg, QtXml, load_plugin_dirs;load_plugin_dirs()'
    stdout = stdout.replace('from PySide import QtCore', replacement)
    stdout = stdout.replace('from PySide2 import QtCore', replacement)
    import sys
    if is_pyside1 and not sys.version_info[0] >= 3:
        stdout = stdout.replace('"\\', 'b"\\')
    with open(output_file, 'w') as stream:
        stream.write(stdout)
