from setuptools import setup, find_packages
import codecs

VERSION = '0.0.0'

entry_points = {
}

TESTS_REQUIRE = []

setup(
	name='nti.graphdb',
	version='0.0',
	keywords='Experimental Code',
	author='NTI',
	author_email='jason.madden@nextthought.com',
	description='NextThought Clients',
	classifiers=[
		"Development Status :: 4 - Alpha",
		"Intended Audience :: Developers :: Education",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 2.7",
		"Internet :: WWW/HTTP",
		"Natural Language :: English"
		],

	tests_require=TESTS_REQUIRE, # Needed for e.g., tox
	install_requires=[
		'setuptools',
		'py2neo >= 1.6.0'
	],
	extras_require={
		'test': TESTS_REQUIRE,
		'tools': [ ]
	},
	packages=find_packages('src'),
	package_dir={'': 'src'},
	include_package_data=True,
	namespace_packages=['nti'],
	zip_safe=False,
	entry_points=entry_points
	)
