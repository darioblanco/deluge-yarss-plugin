# -*- coding: utf-8 -*-
#
# yarss_config.py
#
# Copyright (C) 2012 Bro
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#       The Free Software Foundation, Inc.,
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA.
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

import copy

from deluge.event import DelugeEvent
import deluge.configmanager
import deluge.component as component

from yarss2.util import common
from yarss2.util.common import GeneralSubsConf


DEFAULT_UPDATE_INTERVAL = 120

DUMMY_RSSFEED_KEY = "9999"
CONFIG_FILENAME = "yarss2.conf"

__DEFAULT_PREFS = {
    "email_configurations": {},
    "rssfeeds": {},
    "subscriptions": {},
    "cookies": {},
    "email_messages": {}
    }

def default_prefs():
    return copy.deepcopy(__DEFAULT_PREFS)

class YARSSConfigChangedEvent(DelugeEvent):
    """
    Emitted when the config has been changed.
    """
    def __init__(self, config):
        """
        :param config: the new config
        """
        self._args = [config]

class YARSSConfig(object):

    def __init__(self, logger, config=None, core_config=None, verify_config=True):
        self.log = logger
        self.core_config = core_config
        self.config = config

        # Used for testing
        if config is None:
            self.config = deluge.configmanager.ConfigManager(CONFIG_FILENAME, default_prefs())

        if verify_config:
            self._verify_config()

        if self.core_config is None:
            self.core_config = component.get("Core").get_config()

    def save(self):
        self.config.save()

    def get_config(self):
        "returns the config dictionary"
        config = copy.copy(self.config.config)
        # Add default values from core config
        if self.core_config:
            default_values = {}
            default_values["max_connections"] = self.core_config["max_connections_per_torrent"]
            default_values["max_upload_slots"] = self.core_config["max_upload_slots_per_torrent"]
            default_values["max_upload_speed"] = self.core_config["max_upload_speed_per_torrent"]
            default_values["max_download_speed"] = self.core_config["max_download_speed_per_torrent"]
            default_values["add_torrents_in_paused_state"] = self.core_config["add_paused"]
            default_values["auto_managed"] = self.core_config["auto_managed"]
            default_values["prioritize_first_last_pieces"] = self.core_config["prioritize_first_last_pieces"]
            default_values["sequential_download"] = GeneralSubsConf.DEFAULT
            # Not implemented in 1.3.5
            if "sequential_download" in self.core_config:
                default_values["sequential_download"] = self.core_config["sequential_download"]
            config["default_values"] = default_values
        return config

    def set_config(self, config):
        """Replaces the config data in self.config with the available keys in config"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    def generic_save_config(self, config_name, dict_key=None, data_dict=None, delete=False):
        """Save email message to config.

        If data_dict is None, delete message with key==dict_key
        If data_dict is not None, dict_key is ignored
        If data_dict does not have a key named "key", it's a new config element, so a new key is created.

        config_name must be either of the dictionaries in the main config (See DEFAULT_PREFS):
        """
        if data_dict is not None and type(data_dict) != dict:
            raise ValueError("generic_save_config: data_dict must be a dictionary: '%s'" % str(data_dict))

        if not default_prefs().has_key(config_name):
            raise ValueError("Invalid config key:" + str(config_name))

        config = self.config[config_name]

        # Means delete
        if data_dict is None:
            if dict_key is None:
                raise ValueError("generic_save_config: key and value cannot both be None")
            if not delete:
                raise ValueError("generic_save_config: deleting item requires 'delete' to be True")
           # Value is None, means delete entry with key dict_key
            if config.has_key(dict_key):
                del config[dict_key]
                # Save main config to file
                self.config.save()
                return self.config.config
            else:
                raise ValueError("generic_save_config: Invalid key - "\
                                     "Item with key %s doesn't exist" % dict_key)
        else: # Save config
            # The entry to save does not have an item 'key'. This means it's a new entry in the config
            if not data_dict.has_key("key"):
                dict_key = common.get_new_dict_key(config)
                data_dict["key"] = dict_key
            else:
                dict_key = data_dict["key"]

        config[dict_key] = data_dict
        self.config.save()
        return self.config.config

    def _verify_config(self):
        """Adding missing keys, in case a new version adds more config fields"""
        changed = False

        # Update config
        self.config.run_converter((0, 1), 2, self.update_config_to_version2)
        self.config.run_converter((2, 2), 3, self.update_config_to_version3)
        self.config.run_converter((3, 3), 4, self.update_config_to_version4)
        self.config.run_converter((4, 4), 5, self.update_config_to_version5)

        default_config = get_fresh_subscription_config(key="")
        if self._insert_missing_dict_values(self.config["subscriptions"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["subscriptions"], default_config):
            changed = True

        default_config = get_fresh_rssfeed_config()
        if self._insert_missing_dict_values(self.config["rssfeeds"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["rssfeeds"], default_config):
            changed = True

        default_config = get_fresh_message_config()
        if self._insert_missing_dict_values(self.config["email_messages"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["email_messages"], default_config):
            changed = True

        default_config = get_fresh_cookie_config()
        if self._insert_missing_dict_values(self.config["cookies"], default_config):
            changed = True
        if self._verify_types_config_elements(self.config["cookies"], default_config):
            changed = True

        default_config = get_fresh_email_config()
        if self._insert_missing_dict_values(self.config["email_configurations"], default_config, level=1):
            changed = True
        if self._verify_types(None, self.config["email_configurations"], default_config):
            changed = True

        if changed:
            self.config.save()

    def _verify_types_config_elements(self, config_dict, default_config):
        """Takes a dictinoary and calls _verify_types with each element
        (which is also a dictionary)"""
        changed = False
        for key in config_dict.keys():
            if self._verify_types(key, config_dict[key], default_config):
                changed = True
                # Elements have been removed, so remove from config
                if len(config_dict[key].keys()) == 0:
                    del config_dict[key]
        return changed

    def _verify_types(self, config_key, config, default_config):
        """Takes a dictionary and checks each key/value pair"""
        changed = False
        for key in default_config.keys():
            rssfeed_key_invalid = False
            if not config.has_key(key):
                # We have a problem. Cannot use the default value for a key
                if key == "key":
                    # The key value is missing, so reinsert it.
                    config[key] = config_key
                    changed = True
                elif key == "rssfeed_key":
                    # Cannot insert default value, and cannot know the correct value.
                    rssfeed_key_invalid = True
                else:
                    self.log.warn("Config is missing a dictionary key: '%s'. Inserting "\
                                  "default value ('%s'). Affected config: %s\n" %
                                  (key, str(default_config[key]), str(config)))
                    config[key] = default_config[key]
                changed = True
            else:
                if type(default_config[key]) != type(config[key]):
                    if key == "key":
                        config[key] = config_key
                        changed = True
                    # We have a problem
                    elif key == "rssfeed_key":
                        if type(config[key]) is unicode:
                            try:
                                # Verify it's an integer
                                int(config[key])
                                config[key] = str(config[key])
                            except ValueError:
                                rssfeed_key_invalid = True
                        else:
                            rssfeed_key_invalid = True
                            self.log.warn("The value of the dictionary key '%s' has the wrong type! Value: '%s'."\
                                          "Excpected '%s' but found '%s'. Must be fixed manually."\
                                          "\nAffected config: %s\n" % (key,  str(type(default_config[key])),
                                                                       str(type(config[key])), str(config[key]), str(config)))
                    # If default is unicode, and value is str
                    elif (type(default_config[key]) is unicode and type(config[key]) is str):
                        # Ignore if default is unicode and value is an empty string,
                        # (No point in replacing empty unicode string with ascii string)
                        if config[key] != "":
                            # Try to convert to unicode
                            try:
                                config[key] = config[key].decode("utf8")
                            except:
                                config[key] = default_config[key]
                            changed = True
                    else:
                        self.log.warn("Config value ('%s') is the wrong data type! dictionary key: '%s'. "\
                                 "Expected '%s' but found '%s'. Inserting default value. Affected config: %s" % \
                                 (config[key], key, str(type(default_config[key])), str(type(config[key])), str(config)))
                        config[key] = default_config[key]
                        changed = True
                # Test if key and rssfeed_key are valid
                if key == "key" or (key == "rssfeed_key" and not rssfeed_key_invalid):
                    # Test that they are numbers
                    if not config[key].isdigit():
                        # Replace with config_key
                        if key == "key":
                            config[key] = config_key
                            changed = True
                            # We have a problem
                        else:
                            rssfeed_key_invalid = True
                    else:
                        # Test that rssfeed_key points to a rssfeed that exists in the config
                        if key == "rssfeed_key":
                            # The rsfeed_key is invalid (no rssfeed with that key exists)
                            if not self.config["rssfeeds"].has_key(config[key]):
                                rssfeed_key_invalid = True
            # Must handle missing rssfeed_key in a subscription
            if rssfeed_key_invalid:
                # Check first if the subscription has the default values. In that case, just delete it.
                # If it has the key 'key', use that as key, else None
                default_config = get_fresh_subscription_config(key=None if not config.has_key("key") else config["key"],
                                                               rssfeed_key=None if not config.has_key("rssfeed_key")\
                                                               else config["rssfeed_key"])
                if common.dicts_equals(config, default_config):
                    self.log.warn("Found subscription with missing rssfeed_key. The subscription is empty, so it will be deleted.")
                    for key in config.keys():
                        del config[key]
                    return True
                else:
                    # The subscription has non-default values. Use a dummy rssfeed
                    if self.config["rssfeeds"].has_key(DUMMY_RSSFEED_KEY):
                        dummy_rssfeed = self.config["rssfeeds"][DUMMY_RSSFEED_KEY]
                    else:
                        dummy_rssfeed = get_fresh_rssfeed_config(name=u"Dummy Feed (error in config was detected) "\
                                                                 "Please reassign this subscription to the correct "\
                                                                 "Feed and delete this RSS feed.",
                                                                 active=False, key=DUMMY_RSSFEED_KEY)
                        self.config["rssfeeds"][DUMMY_RSSFEED_KEY] = dummy_rssfeed
                    invalid_rssfeed_key = "Missing" if not config.has_key("rssfeed_key") else config["rssfeed_key"]
                    self.log.warn("Found subscription with missing or invalid rssfeed_key ('%s'). "\
                                  "A dummy rssfeed will be used for this subscription." % invalid_rssfeed_key)
                    config["rssfeed_key"] = DUMMY_RSSFEED_KEY
                    changed = True
        return changed

    def _insert_missing_dict_values(self, config_dict, default_config, key_diff=None, level=2):
        if level == 1:
            return self._do_insert(config_dict, default_config, key_diff)
        else:
            level = level - 1
            for key in config_dict.keys():
                key_diff = self._insert_missing_dict_values(config_dict[key], default_config,
                                                      key_diff=key_diff, level=level)
                if not key_diff:
                    return key_diff
        return key_diff

    def _do_insert(self, config_dict, default_config, key_diff):
        if key_diff is None:
            key_diff = set(default_config.keys()) - set(config_dict.keys())
            # No keys missing, so nothing to do
            if not key_diff:
                return key_diff
        # Set new keys
        for key in key_diff:
            self.log.info("Insert missing config key '%s'" % key)
            config_dict[key] = default_config[key]
        return key_diff

    def update_config_to_version2(self, config):
        """Updates the config values to config file version 2, (YaRSS2 v1.0.1)"""
        self.log.info("Updating config file to version 2 (v1.0.1)")
        default_subscription_config = get_fresh_subscription_config(key="")
        def update_subscription(subscription):
            # It should be there, but just in case
            if "search" in subscription:
                del subscription["search"]
            if not "custom_text_lines" in subscription:
                subscription["custom_text_lines"] = default_subscription_config["custom_text_lines"]
        self.run_for_each_dict_element(config["subscriptions"], update_subscription)
        return config

    def update_config_to_version3(self, config):
        """Updates the config values to config file version 3, (YaRSS2 v1.0.4)"""
        self.log.info("Updating config file to version 3 (tag git v1.0.4)")
        default_subscription_config = get_fresh_subscription_config(key="")
        def update_subscription(subscription):
            if not "download_location" in subscription:
                subscription["download_location"] = default_subscription_config["download_location"]

        self.run_for_each_dict_element(config["subscriptions"], update_subscription)

        default_rssfeed_config = get_fresh_rssfeed_config()
        def update_rssfeed(rssfeed):
            if not "obey_ttl" in rssfeed:
                rssfeed["obey_ttl"] = default_rssfeed_config["obey_ttl"]
        self.run_for_each_dict_element(config["rssfeeds"], update_rssfeed)

        # Convert all str fields to unicode
        default_email_conf = get_fresh_email_config()
        email_conf = config["email_configurations"]
        for key in email_conf.keys():
            if type(email_conf[key]) is str:
                try:
                    config[key] = email_conf[key].decode("utf8")
                except:
                    config[key] = default_email_conf[key]
        return config

    def update_config_to_version4(self, config):
        """Updates the config values to config file version 4, (YaRSS2 v1.1.3)"""
        self.log.info("Updating config file to version 4")
        default_subscription_config = get_fresh_subscription_config(key="")
        def update_subscription(subscription):
            # It should be there, but just in case
            if "last_update" in subscription:
                # Replace 'last_update' with 'last_match'
                subscription["last_match"] = subscription["last_update"]
                del subscription["last_update"]
        self.run_for_each_dict_element(config["subscriptions"], update_subscription)
        return config

    def update_config_to_version5(self, config):
        """Updates the config values to config file version 5, (YaRSS2 v1.2)"""
        self.log.info("Updating config file to version 5")
        default_subscription_config = get_fresh_subscription_config(key="")
        def update_subscription(subscription):
            # Change 'add_torrents_in_paused_state' from boolean to GeneralSubsConf
            if type(subscription["add_torrents_in_paused_state"]) is bool:
                if subscription["add_torrents_in_paused_state"] is True:
                    subscription["add_torrents_in_paused_state"] = GeneralSubsConf.ENABLED
                else:
                    subscription["add_torrents_in_paused_state"] = GeneralSubsConf.DISABLED

            # Adding new fields
            subscription["max_download_speed"] = default_subscription_config["max_download_speed"]
            subscription["max_upload_speed"] = default_subscription_config["max_upload_speed"]
            subscription["max_connections"] = default_subscription_config["max_connections"]
            subscription["max_upload_slots"] = default_subscription_config["max_upload_slots"]
            subscription["auto_managed"] = default_subscription_config["auto_managed"]
            subscription["sequential_download"] = default_subscription_config["sequential_download"]
            subscription["prioritize_first_last_pieces"] = default_subscription_config["prioritize_first_last_pieces"]

        self.run_for_each_dict_element(config["subscriptions"], update_subscription)

        def update_cookie(cookie):
            # Change cookie key/values from list to dict
            value_list = cookie["value"]
            if type(value_list) is not list:
                # Shouldn't really happen, but just in case
                return
            value_dict = {}
            for k, v in value_list:
                value_dict[k] = v
            cookie["value"] = value_dict
        self.run_for_each_dict_element(config["cookies"], update_cookie)
        return config

    def run_for_each_dict_element(self, conf_dict, update_func):
        for key in conf_dict.keys():
            update_func(conf_dict[key])

####################################
# Can be called from outside core
####################################

def get_fresh_email_config():
    """Return the default email_configurations dictionary"""
    config_dict = {}
    config_dict["send_email_on_torrent_events"] = False
    config_dict["from_address"] = u""
    config_dict["smtp_server"] = u""
    config_dict["smtp_port"] = u""
    config_dict["smtp_authentication"] = False
    config_dict["smtp_username"] = u""
    config_dict["smtp_password"] = u""
    config_dict["default_email_to_address"] = u""
    config_dict["default_email_subject"] = u"[YaRSS2]: RSS event ($subscription_title)"
    config_dict["default_email_message"] = u"Hi\n\nThe following torrents have been added:\n$torrentlist\nRegards"
    return config_dict

def get_fresh_rssfeed_config(name=u"", url=u"", site=u"", active=True, last_update=u"",
                             update_interval=DEFAULT_UPDATE_INTERVAL, obey_ttl=False, key=None):
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["name"] = name
    config_dict["url"] = url
    config_dict["site"] = site
    config_dict["active"] = active
    config_dict["last_update"] = last_update
    config_dict["update_interval"] = update_interval
    config_dict["obey_ttl"] = obey_ttl
    if key:
        config_dict["key"] = key
    return config_dict

def get_fresh_subscription_config(name=u"", rssfeed_key="", regex_include=u"", regex_exclude=u"",
                                  active=True, move_completed=u"", download_location=u"", last_match=u"", key=None):
    """Create a new config """
    config_dict = {}
    config_dict["rssfeed_key"] = rssfeed_key
    config_dict["regex_include"] = regex_include
    config_dict["regex_include_ignorecase"] = True
    config_dict["regex_exclude"] = regex_exclude
    config_dict["regex_exclude_ignorecase"] = True
    config_dict["name"] = name
    config_dict["active"] = active
    config_dict["last_match"] = last_match
    config_dict["move_completed"] = move_completed
    config_dict["download_location"] = download_location
    config_dict["custom_text_lines"] = u""
    config_dict["email_notifications"] = {} # Dictionary where keys are the keys of email_messages dictionary
    config_dict["max_download_speed"] = -2
    config_dict["max_upload_speed"] = -2
    config_dict["max_connections"] = -2
    config_dict["max_upload_slots"] = -2
    config_dict["add_torrents_in_paused_state"] = GeneralSubsConf.DEFAULT
    config_dict["auto_managed"] = GeneralSubsConf.DEFAULT
    config_dict["sequential_download"] = GeneralSubsConf.DEFAULT
    config_dict["prioritize_first_last_pieces"] = GeneralSubsConf.DEFAULT

    if key is not None:
        config_dict["key"] = key
    return config_dict

def get_fresh_message_config():
    """Create a new config (dictionary) for a email message"""
    config_dict = {}
    config_dict["name"] = u""
    config_dict["to_address"] = u""
    config_dict["subject"] = u""
    config_dict["message"] = u""
    config_dict["active"] = True
    return config_dict

def get_fresh_cookie_config():
    """Create a new config (dictionary) for a feed"""
    config_dict = {}
    config_dict["site"] = u""
    config_dict["value"] = {}
    config_dict["active"] = True
    return config_dict
