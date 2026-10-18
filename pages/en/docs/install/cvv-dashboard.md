# Install CVV Dashboard

Use HACS to install CVV Dashboard. The integration also installs the Lovelace card. You do not need to add a separate card resource.

## Add the repository to HACS

1. Open **HACS** in Home Assistant.
2. Open the menu in the top right and select **Custom repositories**.
3. Enter this repository address:

   `https://github.com/Sythos/Classeviva-Dashboard`

4. Select **Integration** as the category.
5. Add the repository. Search for **CVV Dashboard**.
6. Open the item and select **Download**.
7. Restart Home Assistant.

You can also use the [My Home Assistant link](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sythos&repository=Classeviva-Dashboard&category=integration) to open the repository in HACS.

## Add the integration

1. Open **Settings > Devices & services**.
2. Select **Add integration**.
3. Search for **CVV Dashboard**.
4. Enter the ClasseViva user name and password.
5. Keep the year set to **Ultimo** to use the latest year with data. You can change it later.
6. Submit the form and wait for Home Assistant to check the account.

Home Assistant stores the user name and password. CVV Dashboard keeps the access token in memory. It renews the token when it expires. Data refreshes every 30 minutes.

## Show the student panel

To add **CVV Dashboard** to the Home Assistant sidebar:

1. Open **Settings > Devices & services**.
2. Select **CVV Dashboard**.
3. Open **Configure**.
4. Turn on **Mostra nel menu laterale**.

Turn this option on for one instance only. The panel can show all configured students.

## Update the integration

Open HACS, select **CVV Dashboard**, and install the offered update. Restart Home Assistant when HACS asks you to do so.

Some releases can show a yellow **!** before a student name when HACS reports an update for this repository. Select the symbol to open the CVV Dashboard item in HACS. The symbol does not install the update.

## If the repository is already listed

If HACS finds CVV Dashboard in its normal list, you can install it from that list. If you cannot find it, use the custom repository steps above.
