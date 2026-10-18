# Troubleshooting

## CVV Dashboard is not in HACS

Add `https://github.com/Sythos/Classeviva-Dashboard` as a custom repository. Select **Integration** as the category. Then search for **CVV Dashboard**.

## The integration does not load

1. Confirm that Home Assistant runs version 2024.7.0 or later.
2. Open **Settings > System > Logs** and look for a CVV Dashboard error.
3. Confirm that HACS completed the download.
4. Restart Home Assistant after installation or an update.
5. Open **Settings > Devices & services** and check the integration entry.

## Login fails

- Check the user name and password in the ClasseViva app or website.
- If the password changed, open the Home Assistant re-authentication prompt and enter the new password.
- Do not repeat failed logins. Many failed attempts can block the account for about 60 minutes.
- A connection or API key error can require a newer CVV Dashboard release. Check HACS for an update.

## The card shows a configuration error

Update CVV Dashboard to the latest version that HACS offers, then reload the browser page. Version 0.4.3 added a fix for early or partial Home Assistant data during the first page load.

If you use a manual `panel_custom` entry, update the version value in `module_url` and reload Home Assistant. The old `panel_custom` entry can conflict with the automatic sidebar option when both use the same path.

## A card view is empty

- Confirm that the selected student has data for the selected year.
- Set the correct `account` value when more than one student is configured.
- Select **Aggiorna** to request new data.
- Some data appears only after the school publishes it.

## No yellow HACS alert appears

The alert needs HACS, a Home Assistant administrator account, and an update for CVV Dashboard in HACS. The alert is available only in a version that includes this function. Older releases may not show it.

## Get more help

Read the [Home Assistant logs](https://www.home-assistant.io/docs/configuration/troubleshooting/) and create a [GitHub issue](https://github.com/Sythos/Classeviva-Dashboard/issues) if the problem remains. Remove user names, passwords, tokens, student names, and school data before you share logs or screenshots.
