import os, sys, platform


if platform.system() == "Windows":
    req_file = "win-requirements.txt"
elif platform.system() == "Darwin":
    req_file = "osx-requirements.txt"
else:
    print("This logger only works for Windows and Mac")
    sys.exit(0)

with open(os.path.join(os.path.dirname(__file__), req_file)) as f:
    requires = list(f.readlines())

print ('"%s"' % requires)

from setuptools import setup

if platform.system() == "Windows":
    setup(name='HBLogger',
          version='0.1',
          description='A Python Logger used to record your keyboard and mouse behaviour',
          url='https://github.com/liuhualin333/HBLogger',
          author='Liu Hualin',
          setup_requires=['pyHook==1.5.1', 'pywin32==221'],
          #Hard coded value for dependencies which cannot be downloaded through pypi
          dependency_links=['https://sourceforge.net/projects/pyhook/files/pyhook/1.5.1/pyHook-1.5.1.win32-py2.7.exe/download', \
                            'https://sourceforge.net/projects/pywin32/files/pywin32/Build%20221/pywin32-221.win32-py2.7.exe/download'],
          install_requires=requires,
          packages=['HBLogger'],
          entry_points=dict(console_scripts=['HBLogger=HBLogger:main']))
elif platform.system() == 'Darwin':
    setup(name='HBLogger',
          version='0.1',
          description='A Python Logger used to record your keyboard and mouse behaviour',
          url='https://github.com/liuhualin333/HBLogger',
          author='Liu Hualin',
          install_requires=requires,
          packages=['HBLogger'],
          entry_points=dict(console_scripts=['HBLogger=HBLogger:main']))
else:
    pass

