# Use CVV Dashboard for one student

For one student, add one CVV Dashboard integration entry and one card.

## Set up the student

Follow [Install CVV Dashboard](../install/cvv-dashboard.md). Enter the student's ClasseViva account. Home Assistant creates the sensors and calendars for that account.

To show the full-screen student panel, turn on **Mostra nel menu laterale** in the integration options. Open **CVV Dashboard** in the sidebar.

## Add the card

Use the card in any Lovelace dashboard:

~~~yaml
type: custom:cvv-dashboard-card
~~~

The card finds the account when only one student is set up. Set `vista` to show one view, such as `voti` or `agenda`.

## Choose a school year

Use **Automatico** to follow the current year. Use the year menu to open another year that ClasseViva makes available. Read [School year](school-year.md) for the date rules and card options.

## What you can do

- Review averages, marks, notices, homework, events, and teacher notes.
- Download published report cards.
- Use the four Home Assistant calendars for this student.
- Refresh data or load notice text without marking it as read.

The [Views and symbols](features.md) page explains each view and control.
