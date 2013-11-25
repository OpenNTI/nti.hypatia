# -*- coding: utf-8 -*-
"""
schema generation installation.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 1

from zope.generations.generations import SchemaManager

import BTrees

import zope.intid

from hypatia.text import TextIndex
from hypatia.catalog import Catalog
from hypatia.keyword import KeywordIndex
from hypatia.text.cosineindex import CosineIndex
from hypatia import interfaces as hypatia_interfaces

from nti.contentsearch import discriminators

from .. import lexicon

class _HypatiaSearchSchemaManager(SchemaManager):
	"""
	A schema manager that we can register as a utility in ZCML.
	"""
	def __init__(self):
		super(_HypatiaSearchSchemaManager, self).__init__(generation=generation,
														  minimum_generation=generation,
														  package_name='nti.hypatia.generations')
def evolve(context):
	install(context)

def create_catalog(lexicon, index):
	result = Catalog(family=BTrees.family64)

	result['content'] = TextIndex(lexicon=lexicon,
								  index=index,
								  discriminator=discriminators.get_object_content,
								  family=BTrees.family64)

	result['ngrams'] = TextIndex(lexicon=lexicon,
								 index=index,
								 discriminator=discriminators.get_object_ngrams,
								 family=BTrees.family64)

	result['title'] = TextIndex(lexicon=lexicon,
								index=index,
								discriminator=discriminators.get_title_and_ngrams,
								family=BTrees.family64)

	result['acl'] = KeywordIndex(discriminator=discriminators.get_acl,
								 family=BTrees.family64)
	return result

def install(context):
	conn = context.connection
	root = conn.root()

	dataserver_folder = root['nti.dataserver']
	lsm = dataserver_folder.getSiteManager()
	intids = lsm.getUtility(zope.intid.IIntIds)

	lexicon = lexicon.defaultLexicon()
	index = CosineIndex(lexicon=lexicon, family=BTrees.family64)
	
	catalog = create_catalog(lexicon, index)
	catalog.__parent__ = dataserver_folder
	catalog.__name__ = '++etc++hypatia++catalog'
	intids.register(catalog)
	lsm.registerUtility(catalog, provided=hypatia_interfaces.ICatalog)

	return catalog