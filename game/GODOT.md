# 逆命大郎 Godot web prototype

This folder is now also a Godot 4.7 project. The first migrated scene is the login page.

## Run locally

Open `project.godot` with Godot 4.7.1 and run the project.

## Export for the web

Install the matching Godot export templates, then run:

```powershell
godot --headless --path . --export-release Web web/index.html
```

The Web preset is single-threaded and uses the Compatibility renderer for Mobile Safari support. Serve the `web/` directory through HTTP or HTTPS. Opening the export directly with `file://` is unsupported.

The Web export uses `web_shell.html` for a custom cinematic loading screen branded for 逆命大郎. The loader reads Godot's real download progress and shows percentage plus estimated time remaining. Desktop and mobile use separate artwork so both lead characters remain visible at each aspect ratio.

The login scene uses a hybrid environment: an original 2560×1440 painted Chinese fantasy city provides the distant world, while a transparent Godot `SubViewport` renders one detailed left-side foreground building, tiled roofs, timber brackets, balconies, lattice windows, stone paving, vermilion lanterns, animated fire braziers, shader materials, fog, banners, and moving cloud layers in real time. The right side stays open for the city artwork and login panel. No pedestrians are used. `scripts/wuxia_ost.gd` synthesizes the original pentatonic soundtrack at runtime, so the project does not ship third-party music.
