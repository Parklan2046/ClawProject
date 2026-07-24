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

The Web export uses `web_shell.html` for a custom cinematic loading screen. The loader reads Godot's real download progress and shows percentage plus estimated time remaining. Desktop and mobile use separate wuxia artwork so both lead characters remain visible at each aspect ratio.

The login scene renders a real-time procedural 3D town through a Godot `SubViewport`. Buildings, sloped tiled roofs, timber frames, stone paving, lanterns, mountains, moon, lighting, shadows, fog, and moving shader-based clouds are all 3D scene content. No pedestrian layer or flat town backdrop is used. `scripts/wuxia_ost.gd` synthesizes the original pentatonic soundtrack at runtime, so the project does not ship third-party music.
