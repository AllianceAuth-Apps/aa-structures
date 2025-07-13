# Operations Manual

## Installation

### Step 0 - Prerequisites

1. Structures is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)

2. Structures needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed, before before installing the app.

### Step 1 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-structures
```

### Step 2 - Update Eve Online app

Update the Eve Online app used for authentication in your AA installation to include the following scopes:

```text
esi-assets.read_corporation_assets.v1
esi-characters.read_notifications.v1
esi-corporations.read_starbases.v1
esi-corporations.read_structures.v1
esi-planets.read_customs_offices.v1
esi-universe.read_structures.v1
```

### Step 3 - Configure AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'structures'` to `INSTALLED_APPS`
- Add below lines to your settings file:

```python
CELERYBEAT_SCHEDULE['structures_update_all_structures'] = {
    'task': 'structures.tasks.update_all_structures',
    'schedule': 1800,
}
CELERYBEAT_SCHEDULE['structures_fetch_all_notifications'] = {
    'task': 'structures.tasks.fetch_all_notifications',
    'schedule': 300,
}
```

- Optional: Add additional settings if you want to change any defaults. See [Settings](#settings) for the full list.

### Step 4 - Celery worker configuration

This app uses celery for critical functions like refreshing data from ESI. We strongly recommend to configure celery for high performance operations.

Please see this guide for details: [Configuring celery workers](https://aa-memberaudit.readthedocs.io/en/latest/operations.html#configuring-celery-workers)

### Step 5 - Finalize installation into AA

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for AA

### Step 6 - Preload Eve Universe data

In order to see structure fits you need to preload some data from ESI once.
If you already have run those commands previously you can skip this step.

Load Eve Online structure types

```bash
python manage.py structures_load_eve
```

### Step 7 - Setup permissions

Now you can setup permissions in Alliance Auth for your users.

See section [Permissions](#permissions) below for details.

### Step 8 - Setup notifications to Discord

The setup and configuration for Discord webhooks is done on the admin page under **Structures**.

To setup notifications you first need to add the Discord webhook that point to the channel you want notifications to appear to **Webhooks**. We would recommend that you also enable `is_default` for your main webhook, so that newly added structure owners automatically use this webhook. Alternatively you need to manually assign webhooks to existing owners after they have been added (see below).

Finally to verify that your webhook is correctly setup you can send a test notification. This is one of the available actions on Webhooks page.

### Step 9 - Add structure owners

Next you need to add your first structure owner with the character that will be used for fetching structures. Just open the Structures app and click on "Add Structure Owner". Note that only users with the appropriate permission will be able to see and use this function and that the character needs to be a director.

Once a structure owner is set the app will start fetching the corporation structures and related notifications. Wait a minute and then reload the structure list page to see the result.

You will need to add every corporation as Structure Owner to include their structures and notifications in the app.

```{hint}
As admin you can review all structures and notifications on the admin panel.
```

## Updating

To update your existing installation of Structures first enable your virtual environment.

Then run the following commands from your AA project directory (the one that contains `manage.py`).

```bash
pip install -U aa-structures
```

```bash
python manage.py migrate
```

```bash
python manage.py collectstatic
```

Finally restart your AA supervisor services.

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your AA settings file (`local.py`).

```{note}
All settings are optional and the app will use the documented default settings if they are not used.
```

```{eval-rst}
.. automodule:: structures.app_settings
    :members:
```

## Permissions

This is an overview of all permissions used by this app. Note that all permissions are in the "general" section.

Name | Purpose | Code
-- | -- | --
Can access public views | User can access this app and view public pages, e.g. public POCO view |  <https://i.imgur.com/BK3MadZ.png>
Can view corporation structures | User can see structures belonging to corporations of his characters only. |  `general.view_corporation_structures`
Can view alliance structures | User can view all structures belonging to corporation in the alliance of the user. |  `general.view_alliance_structures`
Can view all structures | User can see all structures in the system |  `general.view_all_structures`
Can add new structure owner | User can add a corporation with it's structures |  `general.add_structure_owner`
Can view unanchoring timers for all structures the user can see | User can view unanchoring timers for all structures the user can see based on other permissions |  `general.view_all_unanchoring_status`
Can view structure fittings | User can view structure fittings |  `general.view_structure_fittings`

## Admin tools

### Admin site

Most admin tools are accessible on the admin site through actions. e.g. you can sent specific notifications or force a sync with the eve server for an owner.

See the respective actions list on the admin site for details.

### Management commands

Some admin tools are available only as Django management command:

- **structures_load_eve**: Preload static eve objects from ESI to speed up the app
