# 俠客行 Godot web prototype

This folder is now also a Godot 4.7 project. The first migrated scene is the login page.

## Run locally

Open `project.godot` with Godot 4.7.1 and run the project.

## Export for the web

Install the matching Godot export templates, then run:

```powershell
godot --headless --path . --export-release Web web/index.html
```

The Web preset is single-threaded and uses the Compatibility renderer for Mobile Safari support. Serve the `web/` directory through HTTP or HTTPS. Opening the export directly with `file://` is unsupported.

