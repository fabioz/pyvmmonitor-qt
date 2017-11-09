import os

from invoke import Collection, task

ns = Collection()


@task
def codegen(ctx):
    print('pyvmmonitor-qt codegen')
    from pyvmmonitor_qt.gen_resources import generate_resources
    resources_dir = os.path.join(os.path.dirname(__file__), 'resources')

    print('pyvmmonitor-qt codegen: dark resources')
    generate_resources(
        os.path.join(resources_dir, 'dark'),
        os.path.join(os.path.dirname(__file__), 'pyvmmonitor_qt', 'stylesheet', 'dark_resources.py')
    )
    print('pyvmmonitor-qt codegen: light resources')
    generate_resources(
        os.path.join(resources_dir, 'light'),
        os.path.join(os.path.dirname(__file__), 'pyvmmonitor_qt', 'stylesheet', 'light_resources.py')
    )


ns.add_task(codegen, 'codegen')
