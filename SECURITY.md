# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| 0.1.x   | No        |

Only the latest release receives security fixes.

## Report a vulnerability

Do not open a public issue for a security problem.

Use the private reporting form of GitHub:

1. Open the **Security** tab of this repository.
2. Select **Report a vulnerability**.
3. Describe the problem.

Include this information in your report:

- The affected version.
- The steps to reproduce the problem.
- The impact, for example exposure of credentials or personal data.
- A fix or a workaround, if you know one.

## What to expect

- We acknowledge your report within 7 days.
- We give you a plan for a fix within 30 days.
- We publish the fix in a new release and we credit you, if you agree.

## Scope

This project handles the credentials and the school data of ClasseViva accounts.
These items are in scope:

- Storage and handling of the user name, the password, and the session tokens.
- The signed download URLs and the download view.
- The data that the integration sends to the Home Assistant frontend.
- The workflows in this repository.

These items are out of scope:

- The ClasseViva service. Report problems in the service to Gruppo Spaggiari.
- Home Assistant and HACS. Report these problems to their own projects.

## Safe use

- The integration stores the credentials in Home Assistant only.
- Do not post logs that contain credentials or tokens in a public issue.
- The API key in `const.py` is the public key of the official mobile application.
  It is not a secret of the user.
- Too many wrong login attempts block the ClasseViva account for about 60 minutes.
