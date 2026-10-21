# Add the card to Lovelace

CVV Dashboard adds its card to Home Assistant when the integration loads. Do not add a manual resource under **Settings > Dashboards > Resources**.

## Add one card

1. Open the dashboard where you want the card.
2. Enter edit mode.
3. Select **Add card**.
4. Select the CVV Dashboard card, or open the manual YAML editor.
5. Use this minimum configuration:

~~~yaml
type: custom:cvv-dashboard-card
~~~

With no other options, the card shows all views for the detected student account.

## Set one view

Use the `vista` option to show one view:

~~~yaml
type: custom:cvv-dashboard-card
vista: agenda
~~~

Valid values are `medie`, `voti`, `bacheca`, `agenda`, `note`, `scrutini`, `compiti`, `colloqui`, and `combo`.

## Use a full-width view

For a view that has one card across the full width, set its type to **Panel**. In YAML, use `type: panel` for the view:

~~~yaml
views:
  - title: School
    type: panel
    cards:
      - type: custom:cvv-dashboard-card
        vista: combo
~~~

For a view with Sections, set the card width with `grid_options`:

~~~yaml
type: custom:cvv-dashboard-card
grid_options:
  columns: 12
~~~

## Show more than one student

Use a Grid card to place one CVV Dashboard card for each student. See [Two or more students](../guide/multiple-students.md) for a full example.

## Change the card options

The visual editor can set the school year and show or hide the year selector. Use YAML to set the account, view, title, animations, or other card options. See [Views and symbols](../guide/features.md) and [School year](../guide/school-year.md).

To show every student in one full-screen page, use the sidebar panel. See [Two or more students](../guide/multiple-students.md).
