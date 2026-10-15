# Changelog

All important changes to this project are in this file.
Each section has the version number and the date of the release.

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
