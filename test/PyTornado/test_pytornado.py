import os
import shutil
from contextlib import contextmanager
import importlib

PYTORNADO_MAIN_MODULE = 'ceasiompy.PyTornado.runpytornado'
HERE = os.path.dirname(os.path.abspath(__file__))


@contextmanager
def run_module_test_locally(module_name, test_dir):
    """ Context manager which copies a single module

    Args:
        module_name (str): Full 'path' of module which is to be loaded
        test_dir (str): Dictionary in which we run the local test
    """

    module = importlib.import_module(module_name)
    orig_module_file = module.__file__
    local_module_file = os.path.join(test_dir, os.path.basename(orig_module_file))
    shutil.copy(src=orig_module_file, dst=local_module_file)
    try:
        yield local_module_file
    finally:
        os.remove(local_module_file)


def test_basic_run():
    """Make sure that the PyTornado run successfully"""

    shutil.copy(src='cpacs_test_file.xml', dst=os.path.join(HERE, 'ToolInput', 'ToolInput.xml'))

    with run_module_test_locally(PYTORNADO_MAIN_MODULE, HERE) as main:
        os.system(f'python {main}')
