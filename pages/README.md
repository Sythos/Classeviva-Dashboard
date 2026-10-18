# Pages source and manual publishing

The public site uses Material for MkDocs. English source files are in pages/en/docs/. Italian pages are translations of the English source and are in pages/it/docs/.

The release workflow creates cvv_dashboard.zip from custom_components/cvv_dashboard/. The documentation source and the Pages build are outside this folder. They do not enter the HACS release archive.

## Install the documentation tools

From the repository root, run:

~~~powershell
python -m pip install -r pages/requirements.txt
~~~

## Build and preview

To build both languages without a push, run:

~~~powershell
.\pages\publish-pages.ps1 -BuildOnly
~~~

The combined site is in .pages-build/site/. Open index.html to check the language links.

## Publish by hand

1. Edit the English pages first.
2. Translate each change in the matching Italian page.
3. Commit and push the changes to main.
4. Wait for main to contain the commit. Keep the working tree clean.
5. Run this command from the repository root:

~~~powershell
.\pages\publish-pages.ps1
~~~

The script builds both sites and pushes the combined output to gh-pages. It does not create a GitHub Actions workflow. A push to main or a release does not publish the site.

For the first publish, set the repository Pages source to branch gh-pages and folder / in Settings > Pages. GitHub Pages then serves the files from that branch. The site URL is https://sythos.github.io/Classeviva-Dashboard/.
