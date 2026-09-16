# boat-manager-content

Public content repo for the Boat Manager app. One file: `help.json`.

## What help.json is

The app's built-in help: a flat JSON array of entries with
`question`, `answer`, `category`, `order`, `imageName`, `isSysImg`.

- `category` carries its own sort prefix — `1. About`, `2. First Use`, …
  `5. Boats` with sub-categories `5.1 Expenses` … `5.4 Upkeep`, `10. Safety`.
- `order` sorts within a category, and is **not unique** — duplicates exist
  (16,16 in First Use; 1,1 in Maintenance; 3,3 in Settings), so any renderer
  needs a tie-break.
- `answer` is plain text: `\n` is a real line break, lines starting with `•`
  are bullets, and `**bold**` appears in a few of them.
- `imageName` is an SF Symbol when `isSysImg` is true, otherwise an app asset.

## Two ways it gets edited

1. The app's in-app help editor commits straight to `main` via the GitHub API
   ("Update help.json via in-app editor", author `…@users.noreply.github.com`).
2. Hand-authored release passes from a checkout, e.g. "Help for 1.5.0".

## It is published on the website too

`docs/help.html` in **TatterRi/Boat-Manager** fetches this file from
raw.githubusercontent (5-minute cache; jsDelivr as fallback) and renders all
of it client-side. That site is GitHub Pages, served from the **`website`
branch's `/docs` folder** of that repo, live at `boatmanager.app`.

So an in-app help edit reaches the public website on its own, with no site
commit — and a change to the field names, the category numbering, or the
`•` / `**bold**` conventions will change what the website renders. Check
`docs/help.html` before changing the shape of this file.
