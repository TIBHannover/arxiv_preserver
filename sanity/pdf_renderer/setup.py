import os
from setuptools import setup, Extension
import pkgconfig
import re

libraries = []
flags = []
includes = []

flags.append('-std=c++14')

# includes.append(tf.sysconfig.get_include())

poppler_cflags = pkgconfig.cflags('poppler-glib')
poppler_libs = pkgconfig.cflags('poppler-glib')

includes_re = re.compile(r'-I([\S]*)')
flags_re = re.compile(r'(^|\s)(-[^I](\S*))')
libs_re = re.compile(r'-l([\S]*)')

for x in re.finditer(includes_re, poppler_cflags):
    includes.append(x.group(1))

for x in re.finditer(flags_re, poppler_cflags):
    flags.append(x.group(2))

print(flags)

for x in re.finditer(libs_re, poppler_libs):
    libraries.append(x.group(1))

setup(
    name='Simple Example',
    version='0.0.1',
    ext_modules=[
        Extension(
            name='pdf_renderer',
            sources=['pdf_renderer.cpp'],
            language="c++",
            include_dirs=includes,
            library_dirs=['/'],
            libraries=libraries,
            extra_compile_args=flags)
    ],)
