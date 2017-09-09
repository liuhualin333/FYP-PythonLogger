import os
import platform


if platform.system() == "Windows":
    req_file = "win-requirements.txt"
else:
    print("This logger only works for Windows")

with open(os.path.join(os.path.dirname(__file__), req_file)) as f:
    requires = list(f.readlines())

print '"%s"' % requires

from setuptools import setup

setup(name='HuaBaLogger',
      version='0.1',
      description='A Logger to record your keyboard and mouse behaviour',
      url='https://github.com/liuhualin333/FYP-PythonLogger',
      author='HuaBa',
      install_requires=requires,
      packages=['HuaBaLogger'],
      entry_points=dict(console_scripts=['HuaBaLog=HuaBaLogger:main']))