# London Unified Prayer Times for Home Assistant

An alternative Islamic Prayer Times integration for Home Assistant, that uses times sourced from the London Unified Prayer Timetable via the excellent London Unified Prayer Timetable Python library at https://github.com/sshaikh/london_unified_prayer_times. For more background and information please see the library's README, but in short this is an opinionated and curated timetable - that is, not wholly based on calculation and so is always subject to at least an initial remote download.

## Installation

Right now the best way to install this is to clone the repo and get the code into the custom_components folder in the relevant configuration folder (I use a symlink). Perhaps if more than two people use this I'll look into putting this in HACS. Or maybe even directly into the Home Assistant tree.

## Setup

Once installed, you should be able to add the integration via the UI - search for `London` or `lupt` to filter the integration.

The options are as follows:

- `URL` (required): The URL to a resource that contains the prayer time data (not provided but you should be able to guess it)

- `CSS Class` (optional): Please leave this blank (which will use the default) unless you know what it's for.

- `Zawaal Mins`: The number of minutes before Zuhr that you wish Zawaal to start. Please note that this should be a positive number ie 10 (the default) will set Zawaal to ten minutes before Zuhr.

- `When to change the Islamic date`: If checked, the Islamic date will be updated at Maghrib instead of midnight

- `Which Mithl to use for Asr`: If checked, the integration will use Mithl 2 (otherwise known as Hanafi Asr)

Once you've decided your configuration, click `Submit` to close the window and trigger a database initialisation.

## Usage

Once running there's not much else to do. You should now see a card in Lovelace that has the current state and some attributes you may find useful. If your dashboard isn't automatically updated then you may have to create a card manually. The domain for this integration is `lupt`.  For more details on states and events see the next section.

The integration will trigger a database update every night at a quarter past midnight (local time). However the initial database load will have at times at least till the end of the year, so this isn't strictly necessary but implemented in case Islamic dates change.

If this update (or even initialisation after a re-add) fails, the integration will fall back to the last version of the database - effectively meaning you should be able to use this integration without a persistent internet connection. You'd probably want to update it at least once a year, either by allowing it access to the internet overnight or by manually forcing an update by removing and readding the integration.

## Automation

Unlike the Prayer Times integration built into HA, LUPT uses state to indicate what "prayer section" of the day it is. This means you can use state changes to automate on. Generally, the state uses the prayer name, apart from Zawaal and the Sunrise-Zuhr window. The order of states cycles like this:

```
Fajr
Duha
Zawaal
Zuhr
Asr
Maghrib
Ishā
Fajr
```

Also provided are state attributes that hold things like next times for particular prayers or events, as well as the Islamic date and some other diagnostic data.

As well as state changes, you can also create automation triggers. Although similar to automating on states, these expose access to the full range of LUPT events, as well as allowing an offset to be provided in order to, for example, set an alert 30 mins before Maghrib each day. The downside is that there is no built in UI support for custom component triggers.

To create a trigger, while creating your new automation, pick an existing trigger (I use Sun), and use the menu button to "Edit in YAML". Then use the following code:

```
platform: lupt
event: Fajr Begins
offset: '-00:30:00'
```

This will trigger 30 mins before Fajr Begins. Events are taken from the underlying library and will be one of the following:

```
Fajr Begins
Fajr Jamā'ah
Sunrise
Zuhr Begins
Zuhr Jamā'ah
Asr Mithl 1
Asr Mithl 2
Asr Jamā'ah
Maghrib Begins
Maghrib Jamā'ah
Ishā Begins
Ishā Jamā'ah
```

## Support and Known Issues

- Please email me at sshaikh@users.noreply.github.com if you need any help or want to report a bug (this Github repo is just a mirror so your issues will be wasted here).

- Configuration can not be changed once the integration is added. To change options, remove and re-add the integration.

- Any trigger based automations will still trigger after the integration is removed, until the HA instance is rebooted.
