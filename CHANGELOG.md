# Changelog

All important changes to this project are in this file.
Each section has the version number and the date of the release.

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
