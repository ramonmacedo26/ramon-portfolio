# Ramon Macedo Portfolio

Static portfolio site prepared for GitHub Pages.

## What is inside

- `index.html`: main portfolio landing page
- `styles.css`: portfolio styling
- `assets/`: public files used by the site
- `industrial-data-ai-copilot/`: flagship case
- `fabric-ops-analytics-platform/`: Fabric-focused analytics case
- `document-ai-ops-intake/`: document automation case
- `og.png`: social preview image

## Ready for GitHub Pages

This folder is already structured to work as a static site on GitHub Pages.

Key points:

- all main links are relative
- public assets live inside this folder
- no build step is required
- `.nojekyll` is included to avoid GitHub Pages processing quirks

## Recommended publishing path

Option 1: project site

Use a normal repository such as:

- `ramon-portfolio`
- `ramonmacedo-portfolio`

Your URL will look like:

- `https://YOUR-USERNAME.github.io/REPOSITORY-NAME/`

Option 2: user site

Use a repository named exactly:

- `YOUR-USERNAME.github.io`

In that case, the portfolio will open directly at:

- `https://YOUR-USERNAME.github.io/`

## Simple publish steps

1. Create a GitHub repository.
2. Upload the contents of this `portfolio` folder as the repository root.
3. In GitHub, open `Settings` -> `Pages`.
4. Under `Build and deployment`, choose:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main`
   - `Folder`: `/ (root)`
5. Save and wait for GitHub Pages to publish.

## Important note

If you publish this as a project site, keep the whole contents of this folder at the repository root.

Do not upload the parent folder `carreira` as the Pages root, otherwise the links will not match the intended site structure.

## Suggested first public version

The cleanest first release is:

- homepage
- flagship dashboard
- Fabric dashboard
- document automation dashboard
- public CV

That is already enough for a strong first online portfolio.
