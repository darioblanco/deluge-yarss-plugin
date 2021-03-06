# -*- coding: utf-8 -*-
#
# common.py
#
# Copyright (C) 2012 Bro
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from twisted.trial import unittest
import datetime

import deluge.config
import tempfile
import deluge.configmanager
import deluge.core.preferencesmanager

import yarss2.util.common
from yarss2 import yarss_config

import deluge.log
deluge.log.setupLogger("none")
import pkg_resources, sys
from deluge.log import LOG as log
from yarss2 import load_libs
load_libs()

def get_default_subscriptions(count):
    subscriptions = {}
    for i in range(count):
        subscriptions[str(i)] = yarss_config.get_fresh_subscription_config(
            name="Non-matching subscription",
            last_match=yarss2.util.common.get_default_date().isoformat(),
            rssfeed_key="0", key=str(i), regex_include=None, regex_exclude=None)
    return subscriptions

def get_default_rssfeeds(count):
    d = {}
    for i in range(count):
        d[str(i)] = yarss_config.get_fresh_rssfeed_config(key=str(i))
    return d

def get_test_config(config_filename="yarss_test.conf", config_dir=None, verify_config=True):
    """Creates a YaRSS2 config with a reference to a proper deluge config"""
    if config_dir is None:
        config_dir = get_tmp_dir()
    deluge_config = deluge.config.Config(config_filename,
                                         yarss2.yarss_config.default_prefs(), config_dir=config_dir)
    core_config = deluge.config.Config("core.conf", defaults=deluge.core.preferencesmanager.DEFAULT_PREFS, config_dir=config_dir)
    config = yarss2.yarss_config.YARSSConfig(log, config=deluge_config, core_config=core_config, verify_config=verify_config)
    return config

def get_tmp_dir():
    config_directory = tempfile.mkdtemp()
    deluge.configmanager.set_config_dir(config_directory)
    return config_directory

import deluge.common
json = deluge.common.json

# http://torrents.freebsd.org:8080/rss.xml
test_data_dir = "data"
testdata_rssfeed_filename = "%s/freebsd_rss.xml" % test_data_dir
testdata_rss_itmes_json_filename = "%s/freebsd_rss_items_dump.json" % test_data_dir

def load_json_testdata():
    return json_load(testdata_rss_itmes_json_filename, dict_int_keys=True)

def json_load(filename, dict_int_keys=False):
    def datetime_parse(dct):
        if "updated_datetime" in dct:
            dct["updated_datetime"] = yarss2.util.common.isodate_to_datetime(dct["updated_datetime"])
        return dct

    filename = yarss2.util.common.get_resource(filename, path="tests")
    f = open(filename, "r")
    d = json.load(f, object_hook=datetime_parse)
    f.close()

    # Must change keys from string to int
    if dict_int_keys:
        for key in d.keys():
            d[int(key)] = d[key]
            del d[key]
    return d

def json_dump(obj, filename):
    filename = yarss2.util.common.get_resource(filename, path="tests")
    f = open(filename, "wb")
    json.dump(obj, f, indent=2, cls=DatetimeEncoder)
    f.flush()
    f.close()

class DatetimeEncoder(json.JSONEncoder):
     def default(self, obj):
         if isinstance(obj, datetime.datetime):
             return obj.isoformat()
         return json.JSONEncoder.default(self, obj)



####################################
## Helper methods for test data
####################################

def get_test_config_dict():
    config =  yarss2.yarss_config.default_prefs()
    file_url = yarss2.util.common.get_resource(testdata_rssfeed_filename, path="tests")
    rssfeeds = get_default_rssfeeds(3)
    subscriptions = get_default_subscriptions(5)

    rssfeeds["0"]["name"] = "Test RSS Feed"
    rssfeeds["0"]["url"] = file_url
    rssfeeds["1"]["name"] = "Test RSS Feed2"
    rssfeeds["1"]["active"] = False

    subscriptions["0"]["name"] = "Matching subscription"
    subscriptions["0"]["regex_include"] = "sparc64"
    subscriptions["1"]["name"] = "Non-matching subscription"
    subscriptions["1"]["regex_include"] = None
    subscriptions["2"]["name"] = "Inactive subscription"
    subscriptions["2"]["active"] = False
    subscriptions["3"]["name"] = "Update_time too new"
    subscriptions["3"]["last_match"] = datetime.datetime.now().isoformat()
    subscriptions["4"]["name"] = "Wrong rsskey subscription"
    subscriptions["4"]["rssfeed_key"] = "1"

    config["rssfeeds"] = rssfeeds
    config["subscriptions"] = subscriptions
    return config
