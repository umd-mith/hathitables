import sys

from setuptools import setup, Command

class PyTest(Command):
    """
    A command to convince setuptools to run pytests.
    """
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import pytest
        errno = pytest.main("test.py")
        sys.exit(errno)

if sys.version_info[0] < 3:
    dependencies = open('requirements/python2.txt').read().split()
else:
    dependencies = open('requirements/python3.txt').read().split()

setup(
    name = 'hathitables',
    version = '0.0.1',
    url = 'http://github.com/umd_mith/hathitables',
    author = 'Ed Summers',
    author_email = 'ehs@pobox.com',
    py_modules = ['hathitables'],
    description = 'Turn HathiTrust Collections into CSV',
    cmdclass = {'test': PyTest},
    tests_require=['pytest'],
    scripts = ['hathitables.py'],
    install_requires = dependencies
)
