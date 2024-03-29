import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
		"nti_hypatia_indexer = nti.hypatia.utils.indexer:main",
	],
	"z3c.autoinclude.plugin": [
		'target = nti.dataserver'
	],
}

import platform
py_impl = getattr(platform, 'python_implementation', lambda: None)
IS_PYPY = py_impl() == 'PyPy'

setup(
	name='nti.hypatia',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="NTI search hypatia",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='Search indexing',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'License :: OSI Approved :: Apache Software License',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython'
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	install_requires=[
		'setuptools',
		'hypatia',
		'zc.catalogqueue',
		'zopyx.txng3.ext' if not IS_PYPY else ''
	],
	entry_points=entry_points
)
