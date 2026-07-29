# 逆命大郎 — Unity Web

This is the parallel Unity 6 Web build of the game entrance experience. The
existing Godot project remains the production reference while the Unity
loading screen and login scene are rebuilt and validated.

## Scope

- Custom browser loading screen with real Unity download progress and ETA
- Responsive desktop/mobile login
- Hybrid painted town and lightweight real-time foreground VFX
- Traditional Chinese UI and Cantonese-flavoured copy
- Web audio unlock on the first valid browser interaction
- Reproducible command-line Web build

## Required editor

Unity `6000.0.65f1` with Web Build Support. The version is pinned in
`ProjectSettings/ProjectVersion.txt`.

Unity must have an activated Personal, Pro, or Enterprise license before a
batch build can run. If this computer has no active Unity license, sign in and
activate it once through Unity Hub before using the CLI build.

The verified Windows editor installer used for this migration is:

```text
C:\tmp\UnitySetup64-6000.0.65f1.exe
SHA-256: 81171EE02147079675B3CDF0FD6622AA32579465B8B983B20B3449E7786E872C
```

Windows administrator approval is required by the Unity installer. Web Build
Support must also be installed for this exact editor version.

## Generate scenes and build

```powershell
.\build-web.ps1
```

Pass `-UnityPath` if the editor is installed somewhere else, and `-OutputPath`
to override the default `dist` output folder.

The editor build method creates `Assets/Scenes/Login.unity`, applies the
required Web settings, and then produces a static Web build.

## Local preview

Serve `dist/` through HTTP. Do not open `index.html` through `file://`.
