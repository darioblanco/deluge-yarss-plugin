## YaRSS2 : Yet another RSS 2, a RSS plugin for Deluge ##

Forked from https://bitbucket.org/bendikro/deluge-yarss-plugin/downloads

My motivation for that fork is addressing the urllib3 issues that this plugin has, as the urllib3 package is inside the repo, and has to be updated in order to support connections to servers discarding old ciphers, like the ones using Cloudflare's default SSL certificate.

As the project seems abandoned, I would like to address any further issues from now on.

Author -  Darío Blanco <dario@darioblanco.com>

Original Authors

Bro <bro.development@gmail.com>
Camillo Dell'mour <cdellmour@gmail.com>

License: GPLv3

## Building the plugin ##

```
#!bash

$ python setup.py bdist_egg
```


## Running the tests ##
The directory containing yarss2 must be on the PYTHONPATH

e.g.

```
#!bash

yarss2$ export PYTHONPATH=$PYTHONPATH:$PWD/..
```


Run the tests with:

```
#!bash

yarss2$ trial tests
```


## Changelog ##

v1.3.4 - 2015-08-01

* Updated urllib3 package

v1.3.3 - 2014-07-25

* Updated feedparser to 5.1.3
* Fix Libtorrent error when adding magnet links in Deluge 1.3.3

v1.3.2 - 2013-12-10

 + Features
    * Now handles RSS url's that have spaces
    * Added right click option to copy a cookie

 + Bug Fix
     * Fix log window causing crash of Deluge.

v1.3.1 - 2013-10-06

 * Fix incorrect handler in exclude regex textbox (Bart Nagel)
 * Included missing file for Windows. (gtk.keysyms)

v1.3.0 - 2013-09-27

* Added new path chooser to settings.
* If an error occurs when fetching RSS feeds it should no longer stop the
  scheduler from running.

v1.2.1 - 2013-01-12

* Fixed bug causing running subscriptions manually to fail.

v1.2.0 - 2012-12-10

 + Features
    * Added new options in the subscription dialog (Bandwidth, General).
    * Added support for the enclosure tag in RSS feeds.
    * Using the requests library to handle redirects properly so that non-direct
      torrent links work.
    * Added "Copy link to clipboard" button to the right click menu in the
      subscription panel.
    * When failing to download a torrent in the dialog subscription, the page
      content is now shown in a message pane at the bottom.
    * Removed GTK (client) dependency on libtorrent-python


 + Bug Fix:
    * Fixed bug crashing Deluge when adding torrents
    * The checkbox ("On torrent added") to enable a notification in the list of
      notifications
      for a subscription was not working.
    * Tooltips were displayed on the wrong row.

v1.1.3 - 2012-10-17

* Fixed bug that caused sending emails to fail.
* The 'From email address' field value in configurations was not loaded.
* Improved verification of the config on startup. (Fix errors)

v1.1.2 - 2012-10-05

* Fixed error where ComboBox.get_active_text would return None.
* The current value in "Move completed" and "Download location" was added twice.

v1.1.1 - 2012-10-03

* Fixed import error when running YaRSS2 on daemon without gtk installed.
* feedparser library was unable to parse some timestamps.
* The order of the torrents in the torrent list in the subscription dialog was incorrect.

v1.1.0 - 2012-09-12

* Added panel for log messages.
* Added functionality to reset the last matched timestamp for subscriptions. (Options tab in subscription dialog)
* Fixed bug where RSS feeds with no proper tag for the timestamp when the torrent was published would crash YaRSS2.
* Fixed bug where the 'Published' column in matching panel for subscriptions wasn't properly populated.
* Hopefully fixed bug in GUI that could result in Deluge crashing.

v1.0.4 - 2012-06-27

* Added support for magnet links.
* Running RSS feed fetches in separate thread to avoid having the deluge daemon being busy for too long.
* Added option "Obey TTL" in RSS Feed dialog. With this checked the "Update Interval" will be updated with the TTL value of the RSS Feed.
* Added option "Download location" in subscription dialog.
* Fixed bug where it was possible to delete an email message used by subscriptions for notifications.

v1.0.3 - 2012-05-17

* When adding a RSS Feed or changing the RSS Feed update interval the RSS Feed is now properly (re)schedules with the (new) update interval.
  (Previously a restart of deluge was required)
* After deleting a RSS Feed it is properly stopped from running.
* Added timeout for 10 seconds on feedparser so deluge won't hang in case the server doesn't respond properly.
* "Last update" field in RSS Feeds is now updated properly.
* Added "Last matched" field in Subscriptions list with the timestamp for when the subscription last matched a torrent.
* No longer allow deleting RSS Feeds with subscriptions registered.
* Fixed issue in feedparser where '&' in torrent URLs was converted to &amp.

v1.0.2 - 2012-04-07

* Added mime modules for sending email (required on Windows).

v1.0.1 - 2012-04-01

* Unicode characers can now be used to search.
* Added tests to test some of the most important functionality

v1.0 - 2012-03-27

* First release

(Tested with Deluge 1.3.5)
