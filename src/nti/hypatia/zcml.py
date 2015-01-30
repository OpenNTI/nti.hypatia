#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Directives to be used in ZCML

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component
from zope.component.zcml import utility

from .interfaces import ISearchCatalogQueue
from .interfaces import ISearchCatalogQueueFactory

from . import process_queue

@interface.implementer(ISearchCatalogQueue)
class ImmediateQueueRunner(object):

	buckets = 1
	
	def add( self, val ):
		# Process immediately
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			queue.add( val )
			process_queue( queue=queue )

	def update(self, val):
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			queue.update( val )
			process_queue( queue=queue )

	def remove(self, val):
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			queue.remove( val )
			process_queue( queue=queue )
			
	def syncQueue(self):
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			queue.syncQueue()
		
	def eventQueueLength(self):
		return len(self)
	
	def changeLength(self, *args, **kwargs):
		pass

	def process(self, *args, **kwargs):
		pass

	def __getitem__(self, idx):
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			return queue[idx]
		raise IndexError()		
		
	def __len__(self):
		queue = component.queryUtility(ISearchCatalogQueue)
		if queue is not None:
			return len(queue)
		return 0

@interface.implementer(ISearchCatalogQueueFactory)
class _ImmediateQueueFactory(object):

	__slots__ = ()
	
	def get_queue( self ):
		return ImmediateQueueRunner()

@interface.implementer(ISearchCatalogQueueFactory)
class _ProcessingQueueFactory(object):

	__slots__ = ()
	
	def get_queue( self ):
		queue = component.queryUtility(ISearchCatalogQueue)
		return queue

def registerImmediateProcessingQueue(_context):
	logger.info( "Registering immediate processing queue" )
	factory = _ImmediateQueueFactory()
	utility(_context, provides=ISearchCatalogQueueFactory, component=factory)

def registerProcessingQueue(_context):
	logger.info( "Registering processing queue" )
	factory = _ProcessingQueueFactory()
	utility(_context, provides=ISearchCatalogQueueFactory, component=factory)
