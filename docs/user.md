# User manual

The user manual explains how to use Structure's key features.

## Localization

Structures has full localization for languages support by Alliance Auth. This chapter describes how to set the language for different parts of the app:

### UI

To switch the UI to your preferred language simply use the language switcher from Auth.

### Notifications on Discord

The language for notifications on Discord can be chosen by configuring the language property for the respective Webhook. The default language will be used if no language is configured for a Webhook.

### Default language

The default language will be used when no specific language have been configured or no language can be determined. The default language can be defined with the setting `STRUCTURES_DEFAULT_LANGUAGE`.

The following parts of the app will use localization with the default language:

- Timers
- Name of Custom Offices

## Notifications

### Message rendering and pinging on Discord

All notification types are classified in into one of four semantic categories. These categories determine the color of the notification on Discord and whether default pings are created.

Category | Color | Ping
-- | -- | --
success | green | None
info | blue | None
warning | yellow | @here
danger | red | @everyone

The mapping between notification types and semantic categories is predefined and can at the moment not be individually configured.

But it is possible to turn off default pings for all notifications per webhook and/or per owner on the admin site.

### Group pings

You can also define groups to be pinged for notifications on Discord per webhook and/or per owner. All users belonging to that group will then be receive that ping on Discord if they have access to the respective channel.

Groups defined per webhook will be added to groups defined per owner and group pings are independent from default pings.

Note that you need to have Auth's Discord service enabled for group pings to work.

## Power Modes

Structures will display the current power mode of an Upwell structure if it can be determined.

Current supported power modes are:

- Full Power
- Low Power
- Abandoned

Note that the power modes are inferred, since ESI does not provide the current power mode of structures. So they may not be 100% accurate.

If it is unclear wether a structure is "Low Power" or "Abandoned", the power mode will be shown as "Abandoned?". This usually happens if a structure already was on "Low Power" before this update has been installed, so the app has no information when it was last online. As mitigation you can manually update the field "last online at" for a structure on the admin site.

## Structure tags

Structure tags are colored text labels that can be attached to individual structures. Their main purpose is to provide an easy way to organize structures. Tags are shown below the name on the structure list and you can filter the structure list by tags.

For example you might be responsible for fueling structures in your alliance and there are a couple structures that you do not need to care about. With structure tags you can just apply a tag like "fueling" to those structures that you need to manage and then filter the structure list to only see those.

There are two kinds of structure tags: Custom tags and generated tags

### Custom tags

Custom tags are created by users. You can created them on the admin panel under Structure tags, give them any name, color and define its order. Existing structure tags can be assigned to a structure on the structures page within the admin panel.

You can also define custom tags as default. Default tags are automatically added to every newly added structure. Furthermore you enable default tags to be your default tag filter to be active when opening the structure list (see [](operations.md#settings))

### Generated tags

Generated tags are automatically created by and added to structures by the system. These tags are calculated based on properties of a structure. The purpose of generated tags is to provide additional information and filter options for structures in the structure list.

There are currently two types of generated tags:

- space type: Shows which space type the structure is in, e.g. null sec or low sec
- sov: Shows that the owner of that structures has sovereignty in the respective solar system

## Timers

**Structures** will automatically create friendly timers from  notifications for Alliance Auth's Structure Timers app. This feature can be configured via [](operations.md#settings).

Timers can be created from the following notification types:

- OrbitalReinforced
- MoonminingExtractionStarted
- SovStructureReinforced
- StructureAnchoring (excluding structures anchored in null sec)
- StructureLostArmor
- StructureLostShields

## Multiple sync characters

It is possible to add multiple sync characters for a structure owner / corporation. This serves two purposes:

- Improved reaction time for notifications
- Improved resilience against character becoming invalid

### Improved reaction time for notifications

One of the most popular features of Structures is it's ability to automatically forward notifications from the Eve server to Discord. However, there is a significant delay between the time a notification is create in game and it appearing on Discord, which on average is about 10 minutes.

That delay is caused by the API of the Eve Server (ESI), which is caching all notification requests for 10 minutes.

You can reduce the reaction time by adding multiple sync characters for every owner. Structures will automatically rotate through all configured sync characters when updating notifications. Please also remember to reduce the update time of the related periodic task (`structures_fetch_all_notifications`) accordingly. E.g. if you have 5 sync characters you want to run the periodic update task every 1-2 minutes.

Every added sync character will reduce the delay up to a maximum of 10, which brings the average reaction time down to about 1 minute.

### Improved resilience against character becoming invalid

Another benefit of having multiple sync characters is that it increases the resilience of the update process against failures. E.g. it can happen that a sync character becomes invalid, because it has been moved to another corporation or it's token is no longer valid. If you only have one sync character configured then all updates will stop for the tower until a new character is provided. However, if you have more then one sync character configured, then Structures will ignore the invalid character (but notify admins about it) and use any of the remaining valid characters to complete the update.

### Measuring notification delay

Structures has the ability to measure the average notification delay of your system. You can find that information on the admin site / owners / [Your owner] / Sync status / Avg. turnaround time. This will show the current average delay in seconds between a notification being created in game and it being received by Structures for the last 5, 15 and 50 notifications.

## Admin status notifications

Many alliances are relying that the structure services - i.e. getting attack and fuel notifications on Discord. However, outages can occur, e.g. when tokens become invalid or the Eve Online API server (ESI) has issues. To give alliances the ability to fix outages quickly, Structures has a build in service monitoring capability. Should an issue occur it will automatically send an Auth notification to admins. When combined with the app [Discord Notify](https://gitlab.com/ErikKalkoken/aa-discordnotify), those notifications will be forwarded immediately to Discord, allowing admins to take quick action to resolve any issues.

There are currently two types of issue related admin notifications:

- Sync character no longer valid
- Services are down

### Sync character no longer valid

When a character that us used to sync an owner from ESI becomes invalid, it is automatically removed and both the related user and the admins are informed. Characters can become invalid e.g. when the token is no longer valid or the character lost permissions to use Structures.

### Services are down

In addition Structures is constantly monitoring that all updates from ESI are running. Should a service fail to update within the alloted time the services for that owner will be reported as down and the admins will be notified. Once that service has resumed updating another notification is issued informing the admins that the services for that owner are back up.

```{hint}
You can adjust maximum time since it's last successful sync before a service is reported as down with the following [](operations.md#settings):

- `STRUCTURES_STRUCTURE_SYNC_GRACE_MINUTES`
- `STRUCTURES_NOTIFICATION_SYNC_GRACE_MINUTES`.
```

## Public Customs Offices

PI can be a lucrative income source, both for alliances and characters. But your alliance mates need to know where your alliances' customs offices are in order to use them. To help you with that you can choose to show the customs offices of any owner on a special page. In addition to the exact location that page will also show the current tax rates and the planet type.

Here is an example:

![example](https://i.imgur.com/5kd20QZ.png)

To enable this feature you need to do 2 things: First, you need to enable the "public" showing of customs offices for an owner. You will find that option on the admin site for Owners:

![Poco options](https://i.imgur.com/BK3MadZ.png)

Second, you need to give your users access to the Structures app with the basic access permission. e.g. by adding that permission to the Member state. The pages with the full structures list are hidden behind additional permissions. For details please see [](operations.md#permissions).

## Fuel Alerts

Structures can generate additional notifications that help keep track of fueling levels for your structures:

- Refueled notification
- Structure fuel alerts
- Jump fuel alerts

All of these notifications can be enabled for webhooks, just like any of the standard notifications from the Eve Server.

```{hint}
All notifications are generated based on the structure and asset information that is usually updated hourly from the Eve server due to caching. However, you can get more timely updates by adding multiple characters to your owners. e.g. with 2 characters you get fresh data every 30 minutes.
```

### Refueled notification

Refueled notification are generated once a structure has been refueled and will help you coordinate refueling efforts. i.e. when the refueled notification appears in your Discord channel, you know that someone else has taken care of refuelling that particular structures.

Refueled notifications are available for Upwell structures and POSes, however the POS version is currently experimental.

To enable getting refueled notifications you need to activate this feature with a setting:

```python
STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS = True
```

### Structure fuel alerts

Structure fuel alerts can be configured to provide additional alert notification about low fuel levels of your structures. They are highly customizable to accommodate all kinds of use cases. You can configure one ore multiple structure fuel alerts. All configuration is done through the admin site.

Here are some examples:

#### First configuration

When fuel is down to 3 days, send a warning notification every 12 hours. For this the configuration would be:

- start: 72
- end: 24
- interval: 12
- channel pings: @here
- color: warning

#### Second configuration

When fuel is down to 24 hours, send a danger notification every 6 hours and ping everybody. For this the configuration would be:

- start: 24
- end: 0
- interval: 6
- channel pings: @everyone
- color: danger

### Jump fuel alerts

Jump fuel alerts are similar to structure fuel alerts, but made specifically to deal with Liquid Ozone levels of jump gates. They have many of the same customization options and you also configure them on the admin site. They are triggered by the current fuel level measured in units of Liquid Ozone in a jump gate.

## Service monitoring

Alliances may want to rely on getting prompt notifications on Discord to keep their assets save. However, an app like Structures is fully dependant on external services like the Eve API (ESI) to stay operational.

In order stay alliance apprised about any potential service outages, this app has a simple HTTP interface that enables monitoring of it's service status by a 3rd party monitoring application. (e.g. [Uptimerobot](https://www.uptimerobot.com)).

The monitoring route is: `[your AA URL]/structures/service_status`

To make this page accessible for monitoring tools you need to enable public views for the structures app in your local settings. Example:

```Python
APPS_WITH_PUBLIC_VIEWS = [
    "structures"
]

```

Status | HTTP code | Text | Condition
-- | -- | -- | --
Up | `200` | `service is up` | Tasks for updating of structures, <br>updating of notifications and forwarding to webhooks <br>have completed within the configured grace period <br>and there are no errors
Down | `500` |`service is down` | Above condition for "up" not met

By default the status of all existing owners will be included in determining the overall status. However, it's also possible to manually exclude owners by setting the property "Is included in service status".

```{note}
Inactive owners are not included in determining the service status
```
