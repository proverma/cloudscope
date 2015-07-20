from setuptools import setup

setup(
    name='cloudscope',
    version='0.1',
    py_modules=['cloudscope'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        cloudscope=cloudscope.clic:clic
    ''',
)
