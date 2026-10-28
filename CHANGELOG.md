# Changelog

All important changes to this project are in this file.
Each section has the version number and the date of the release.

## 0.4.8 - 2026-10-28

### Changed

- The Compiti view shows the homework from the family portal session.
- The list starts from today. It uses ascending due-date order.
- Each task shows the due time, description, subject, teacher, and assignment date.
- The Agenda view does not change.
- A failed request keeps the last valid list.
- The Agenda sensor has a revision hash of the homework list. The card reloads its data when the homework changes.

## 0.4.7 - 2026-10-28

### Changed

- The HACS update alert opens the Home Assistant Updates page, `/config/updates`, on the active Home Assistant origin.
- The alert does not start an update. Home Assistant controls the access and the installation.
- The alert is still visible only to a signed-in user who can manage the update.
- The integration uses `asyncio.timeout` in place of `async_timeout`.
- The release workflow deploys the Pages only from `main`. The release archive holds only the integration folder.

## 0.4.6 - 2026-10-21

### Added

- The card has a new tab, Assenze e Ritardi, after Compiti. It shows absences, late arrivals, and early exits.
- The list shows the newest record first. Green text means justified. Red text means the record needs justification.
- Each record has a text status and an icon. The tab shows the number of records that need justification.
- The view is read-only. It has no control to justify, edit, or delete a record.
- A new sensor, Assenze e ritardi, holds the number of records that need justification.
- The integration reads the records with the route `absences/details`. This route is not yet confirmed on a live register.
- A failed request keeps the last good list.
- The card has a new last tab, Colloqui. It shows the teacher meeting slots for today and the next 27 days.
- The view is read-only. It has no control to book, cancel, or change a meeting.
- The slots use ascending date and time order. A booked slot is bold and green and has the text status Prenotato.
- Select a booked slot to open or close its details: room, mode, meeting link, and notes.
- A new sensor, Colloqui, holds the number of booked meetings.
- The sensor does not send a request for a student account.
- The routes and the field names of the register are not confirmed on a live account. Check them before a release.

### Changed

- The spacing between the tabs of the card becomes smaller before the tab row uses a scroll bar.
- The student bar of the sidebar page uses the same rule.

## 0.4.5 - 2026-10-18

### Added

- The card and the menu panel show a yellow "!" before the student name when HACS reports an update for this repository.
- The "!" is visible only to a Home Assistant administrator.
- A click on the "!" opens the HACS page of this repository. The "!" does not install the update.
- The "!" changes when the state of a HACS update entity changes. The card does not poll HACS.

## 0.4.4 - 2026-10-18

### Changed

- The Agenda shows all events from today, then the events of the future dates, in ascending date order. It hides the earlier dates.
- The Agenda calculates the date again when the data refreshes.
- The Agenda sorts the events of one day by time.
- The Agenda of a past school year stays complete.

## 0.4.3 - 2026-10-18

### Fixed

- The card no longer shows "Errore di configurazione" when the page gives the Home Assistant data to the card early or in part. This can happen on the first direct load of a dashboard.
- The card keeps the Home Assistant data that arrives before the configuration. It uses the data again after the configuration is set.
- The card handles a data request that fails at once, when the connection is not ready. It shows the normal error and tries again.

## 0.4.2 - 2026-10-16

### Fixed

- A notice that you open in the notice board loses the "Da Leggere" label. Before this fix, the label stayed after the register marked the notice as read.
- The card keeps the opened notice in the "only unread" list until you change the view. You can read the text before the notice leaves the list.

## 0.4.1 - 2026-10-16

### Fixed

- The card, the data command, and the download view are now registered when Home Assistant starts, before the integration loads data from the register. Before this fix, a page that the browser loaded during the start could show "Errore di configurazione" in place of the cards. A reload of the page cleared the error.

## 0.4.0 - 2026-10-15

### Added

- The options of the integration have a new switch: "Show in the sidebar".
- When you turn it on, the integration adds the CVV Dashboard page to the Home Assistant sidebar. It shows every student. You do not need to edit `configuration.yaml` and you do not need to restart.
- The switch is valid for all instances. The sidebar entry stays while at least one instance has the switch on.
- If a page with the path `cvv-dashboard` already exists, for example from `configuration.yaml`, the integration does not change it and does not add its own entry.

### Changed

- The integration depends on the Home Assistant component `panel_custom`.
- The brand images are smaller. The four files go from 965 KB to 262 KB.

## 0.3.0 - 2026-10-15

### Added

- Home Assistant asks for a new password when the register rejects the saved password. You do not need to delete the integration.
- The options of the integration change the password and the school year of one student.
- When you change the school year, the entities and the device keep their ids. Dashboards and automations keep working.
- The integration tests the new password before it saves the password. It refuses the login of a different student.

## 0.2.3 - 2026-10-15

### Changed

- The repository has a new name: Classeviva-Dashboard. HACS does not accept "HACS" in the name of a repository.
- The links in the integration manifest and in the README use the new name. GitHub redirects the old links.

## 0.2.2 - 2026-10-15

### Changed

- The HACS manifest lists Italy as the country of the project.
- The validation workflow runs every day.

## 0.2.1 - 2026-10-15

### Fixed

- The year menu shows when the card loads for the first time. Before this fix, the menu showed only after a change of tab.

## 0.2.0 - 2026-10-15

### Added

- The card has a menu to change the school year.
- The automatic choice follows the current school year. A school year starts on 1 September.
- The browser remembers the choice. In the side menu page, the choice is the same for all students.
- The integration downloads a past school year when you ask for it. It uses the login that is already active, so no new login is necessary.
- The new option `selettore_anno` shows or hides the menu.

### Changed

- The version badge and the license badge in the README use new addresses, to show the correct values.

## 0.1.0 - 2026-10-15

### Added

- First release.
- The integration shows grades, averages, noticeboard, agenda, notes, report documents, and homework from the ClasseViva register.
- Home Assistant has four calendars for each student: agenda, homework, teacher notes, and room bookings.
- The Lovelace card has seven tabs. The integration loads the card automatically.
- A full-screen page for the side menu shows one student at a time.
- Services refresh the data and read a notice.
- Signed links download the attachments.
- The repository has a security policy and private vulnerability reporting.
