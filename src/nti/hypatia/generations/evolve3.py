#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 3.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 3

# import BTrees
# 
# from zope import component
# 
# from zope.component.hooks import site
from zope.component.hooks import setHooks

# from hypatia.field import FieldIndex
# 
# from nti.contentsearch.constants import creator_
#  
# from nti.contentsearch.discriminators import get_creator
# 
# from nti.hypatia.interfaces import ISearchCatalog
# 
# from nti.hypatia.utils import all_indexable_objects_iids

def do_evolve(context):
	setHooks()
# 	conn = context.connection
# 	root = conn.root()
# 	ds_folder = root['nti.dataserver']
# 
# 	lsm = ds_folder.getSiteManager()
# 	catalog = lsm.getUtility(provided=ISearchCatalog)
# 
# 	if creator_ in catalog:
# 		return 0
# 
# 	total = 0
# 	with site(ds_folder):
# 		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
# 				"Hooks not installed?"
# 
# 		index = FieldIndex(discriminator=get_creator,
# 						   family=BTrees.family64)
# 		catalog[creator_] = index
# 
# 		logger.info('Hypatia evolution gen 3 started')
# 
# 		for iid, obj in all_indexable_objects_iids():
# 			index.index_doc(iid, obj)
# 			total += 1
# 
# 		logger.info('Hypatia evolution gen 3 done; %s object(s) processed' % total)
# 
# 	return total

def evolve(context):
	"""
	Evolve to generation 3 by indexing the creator field
	"""
	do_evolve(context)
