import os
import subprocess

resources_dir = os.path.join(os.path.dirname(__file__), 'resources')

template = '''
<RCC>
  <qresource>
%(files)s
  </qresource>
</RCC>
'''


def generate(target_name):

    target = os.path.join(resources_dir, target_name)
    files = []
    for f in sorted(os.listdir(target)):
        if f.endswith('.png'):
            files.append('    <file>%s</file>' % f)

    resources_xml = template % dict(files='\n'.join(files))
    resources_xml_file = os.path.join(target, 'resources.xml')
    with open(resources_xml_file, 'w') as stream:
        stream.write(resources_xml)

    import PySide
    pyrcc = os.path.join(os.path.dirname(PySide.__file__), 'pyside-rcc.exe')
    assert os.path.exists(pyrcc), 'Expected: %s to exist.' % (pyrcc, )
    p = subprocess.Popen(
        [pyrcc, resources_xml_file],
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = p.communicate()
    assert not stderr, stderr

    f = os.path.join(
        os.path.dirname(resources_dir),
        'pyvmmonitor_qt',
        'stylesheet',
        '%s_resources.py' %
        (target_name,
         ))
    stdout = stdout.replace('from PySide import QtCore', 'from pyvmmonitor_qt.qt import QtCore')
    stdout = stdout.replace('"\\', 'b"\\')
    with open(f, 'w') as stream:
        stream.write(stdout)

if __name__ == '__main__':
    generate('dark')
    generate('light')

# <!-- Gen with:
# C:\bin\Anaconda\Lib\site-packages\PySide\pyside-rcc.exe X:\pyvmmonitor\pyvmmonitor-qt\resources\dark\resources.xml > X:\pyvmmonitor\pyvmmonitor-qt\pyvmmonitor_qt\stylesheet\dark_resources.py
#
# Some resources (locally: pyvmmonitor/iconsets - not committed to git due to size)
#
# http://www.creativebloq.com/web-design/free-icon-sets-10134829
# http://modernuiicons.com/
# -->
