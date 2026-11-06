# Tietoteekkariyhdistys Website

The website of Tietoteekkariyhdistys ry (TTY), built with [Hugo](https://gohugo.io/), a static site generator. The look is a file-explorer / code-editor theme written for this site; all templates and styles are in this repository. Changes to `main` are built and published automatically.

## Live site

The site is published at <https://tietoteekkariyhdistys.fi/>. The address is set in `hugo.toml` (`baseURL`); `hugo server` ignores it and uses `localhost:1313`.

It is rebuilt on every push to `main` and once a day (so past events drop off the events list).

## Requirements

- [Hugo](https://gohugo.io/installation/) extended, version 0.157 or newer.
- Python 3 with Pillow, only if you want to regenerate the 404 page animation (see below).

## Development

Run `hugo server` and open `localhost:1313`. It is recommended to at least read the [Hugo Quick Start](https://gohugo.io/getting-started/quick-start/) so the basic commands and directory structure become clear.

### Directory structure

- `content/` holds all pages as Markdown files. News items are in `content/news/`.
- `archetypes/` define the front matter (metadata) new pages get when they are created.
- `layouts/` holds the templates. `_default/baseof.html` is the root layout, `_default/list.html` is used for the News page, `index.html` is the home page, and `board/`, `events/` and `news/` have layouts for those page types. `partials/` holds reusable pieces such as the sidebar (`explorer.html`) and the footer.
- `assets/css/main.css` holds all styles. Colours, fonts and sizes are at the top as variables.
- `data/guilds.yaml` lists the member guilds (shown on the home page and the members page).
- `static/` holds files copied as they are (favicons, the share image, the bylaws PDF).
- `tools/404/` holds the scripts that generate the animated 404 page, see below.

### Sidebar and navigation

The file tree in the sidebar is defined in `hugo.toml` under `[[params.tree]]`. Each folder lists its files with a name per language. To add a page to the sidebar, add a `[[params.tree.files]]` entry with the page's path (relative to the language root) and its file name in each language. The "guilds" folder is filled from `data/guilds.yaml` and the "events" folder also lists the event pages.

### Front matter (aka metadata)

- Defined between two sets of `+++` at the beginning of the page file.
- Basically only the `title` front matter is mandatory since it's used to display page titles by the browser.
- Named layouts can be set with the front matter `type`, which makes a page use the layouts in `layouts/<type>/` instead of a default layout.
- As long as a page's front matter has `draft = true`, it will not be included in the production build of the website.
- A news item with `private = true` is left out of the news lists.

### Translations

- For Finnish pages, use `index.fi.md`. For Swedish pages, use `index.sv.md`. For English pages, use `index.en.md`. Place all in the same directory for one page.
- If a language file for the selected language does not exist, links to that page in the selected language will not work.
- News items only appear in lists for the languages they have language files for, so it's possible to make some items only in Finnish and others in all three languages for example.
- Remember to update all existing language files for a page when updating its Finnish version!
- The translated texts used by the templates (home page, labels, descriptions) are in `hugo.toml` under each language's parameters section, e.g. `[languages.sv.params]`. New parameters can be freely added but remember to add them for each language!

### Creating new pages

- Create a new page with `hugo new name-of-page/index.fi.md`. It's also recommended to create the other language versions as well: `hugo new name-of-page/index.sv.md` and `hugo new name-of-page/index.en.md`. This will create a new subdirectory and file in `content/` with the applicable front matter.
- Create a new news item with `hugo new news/name-of-item/index.fi.md`. Also create the `index.sv.md` and `index.en.md` files if you want the item to appear in the Swedish and English versions of the site!
- Add the new page to the sidebar tree as described above.

### The 404 page

`layouts/404.html` is a generated file (about 600 KB): an ASCII-art scene animated with CSS only. **Do not edit it by hand.** The scene is described in `404-scene-script.md`. To change it, edit the scripts in `tools/404/` and regenerate (from inside that folder):

```
python gen5.py
python assemble5.py
```

`gen5.py` draws the frames (`frames5.json`) and `assemble5.py` writes `layouts/404.html`. The fixed styles for the scene are in the `/* 404 */` block of `assets/css/main.css`; the animation times are set by the generated page itself.
