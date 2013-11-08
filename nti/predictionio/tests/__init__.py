#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import uuid

import nti.dataserver as dataserver

import nti.predictionio as predictionio

from nti.dataserver.tests.mock_dataserver import SharedConfiguringTestBase as DSSharedConfiguringTestBase

DEFAULT_URI = u'http://localhost:7474/db/data/'

def _random_username(self):
    splits = unicode(uuid.uuid4()).split('-')
    username = "%s@%s" % (splits[-1], splits[0])
    return username

class ConfiguringTestBase(DSSharedConfiguringTestBase):
    set_up_packages = (dataserver, predictionio,)
    DEFAULT_URI = DEFAULT_URI
