#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
predictionio interfaces

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from dolmen.builtins import IDict
from dolmen.builtins import ITuple

from nti.utils import schema as nti_schema

class IPredictionIOApp(interface.Interface):
	AppKey = nti_schema.ValidTextLine(title='application key')
	URL = nti_schema.ValidTextLine(title='application URL')

class IProperties(IDict):
	pass

class ITypes(ITuple):
	pass
