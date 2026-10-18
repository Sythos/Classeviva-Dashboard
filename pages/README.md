# Pages source and publishing

The public site uses Material for MkDocs. English source files are in `pages/en/docs/`. Italian pages are translations of the English source and are in `pages/it/docs/`.

The release workflow builds both language sites when a version tag is pushed. It then creates the release, creates and verifies a signed provenance attestation for `cvv_dashboard.zip`, and deploys the two sites to GitHub Pages. The HACS archive still contains only `custom_components/cvv_dashboard/`.

## Install the documentation tools

From the repository root, run:

~~~powershell
python -m pip install -r pages/requirements.txt
~~~

## Build the site

To build both languages on your computer, run:

~~~powershell
.\pages\publish-pages.ps1 -BuildOnly
~~~

The combined site is in `.pages-build/site/`. Open `index.html` to check the language links. The local PowerShell helper is ignored by Git and must stay on this computer.

## Publish the first site

1. Set the Pages source to **GitHub Actions** in the repository settings.
2. Open **Actions** and select **Release**.
3. Select **Run workflow** and choose `main`.
4. Wait for the workflow to deploy the site.

This manual run builds and deploys the guide. It does not create a release. Future version tags create a release and deploy the guide in the same workflow. The site URL is `https://sythos.github.io/Classeviva-Dashboard/`.
