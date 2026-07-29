# 逆命大郎 — Unity Web

This folder is the parallel Unity 6 Web version of the game entrance
experience. It contains the custom loading screen, responsive login scene,
hybrid painted/3D town, foreground VFX, and browser audio handling.

The existing Godot project outside this folder remains independent. Do not
mix Godot export files with this Unity build.

## What gets deployed

Unity source code cannot be served directly as a website. A successful build
creates the following static site:

```text
dist/
├── index.html
├── Build/
└── TemplateData/
```

Upload the **contents of `dist/`** to the web root. Do not deploy `Assets/`,
`Packages/`, `ProjectSettings/`, or the repository root as the public site.

The recommended production workflow is:

```text
Unity build machine or CI → dist/ artifact → Linux web server → HTTPS → Chrome
```

The Linux production server does not need Unity when it only hosts a
previously built `dist/` artifact.

## Project requirements

- Unity Editor `6000.0.65f1`
- Web Build Support module for that exact Editor version
- An activated Unity Personal, Pro, or Enterprise license
- 64-bit Windows or supported 64-bit Linux build machine
- Enough free disk space for the Editor, imports, cache, and Web build

The required Editor version is pinned in
`ProjectSettings/ProjectVersion.txt`. Do not silently upgrade the project on a
server. Upgrade and validate it in a separate branch first.

Official references:

- [Unity CLI and module installation](https://docs.unity.com/en-us/hub/use-unity-cli)
- [Unity Hub installation on Linux](https://docs.unity.com/en-us/hub/install-hub-linux)
- [Unity 6 browser requirements](https://docs.unity3d.com/6000.0/Documentation/Manual/system-requirements.html)

## Option A — build on Windows

From this `unity` directory:

```powershell
.\build-web.ps1
```

The script looks for Unity in these locations:

```text
C:\tmp\unity-6000.0.65f1\Editor\Unity.exe
C:\Program Files\Unity\Hub\Editor\6000.0.65f1\Editor\Unity.exe
C:\Program Files\Unity\Editor\Unity.exe
```

Use an explicit path when necessary:

```powershell
.\build-web.ps1 `
  -UnityPath "D:\Unity\6000.0.65f1\Editor\Unity.exe" `
  -OutputPath "$PWD\dist"
```

The verified Windows Editor installer previously used for this migration was:

```text
C:\tmp\UnitySetup64-6000.0.65f1.exe
SHA-256: 81171EE02147079675B3CDF0FD6622AA32579465B8B983B20B3449E7786E872C
```

## Option B — build on a Linux server

Linux can build this project, but cloning the repository alone is not enough.
The server must have the matching Linux Unity Editor, WebGL module, and valid
license.

Unity's standalone CLI can install an Editor and the `webgl` module:

```bash
curl -fsSL https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.sh \
  | UNITY_CLI_CHANNEL=beta bash

unity --version
unity auth login
unity install 6000.0.65f1 -m webgl
unity editors -i
```

The Unity CLI is currently experimental. `unity auth login` starts a
browser-based sign-in flow. If the server cannot complete an interactive
login or license activation, build on an already activated workstation or CI
runner and use the deploy-only workflow instead. Do not bypass Unity
licensing.

After installation, locate the Linux Editor executable. Common locations
include:

```text
$HOME/Unity/Hub/Editor/6000.0.65f1/Editor/Unity
/opt/unity/Editor/Unity
```

From the repository root, run:

```bash
cd game/unity

export UNITY_EDITOR_PATH="${UNITY_EDITOR_PATH:-$HOME/Unity/Hub/Editor/6000.0.65f1/Editor/Unity}"
export NIMING_UNITY_OUTPUT="$(pwd)/dist"

test -x "$UNITY_EDITOR_PATH" || {
  echo "Unity Editor not found or not executable: $UNITY_EDITOR_PATH" >&2
  exit 1
}

mkdir -p Logs "$NIMING_UNITY_OUTPUT"

"$UNITY_EDITOR_PATH" \
  -batchmode \
  -quit \
  -accept-apiupdate \
  -projectPath "$(pwd)" \
  -buildTarget WebGL \
  -executeMethod NimingDalong.Editor.WebBuild.Build \
  -logFile "$(pwd)/Logs/web-build.log"
```

The Editor method performs these operations:

1. Validates the required art, audio, fonts, and Web template.
2. Generates `Assets/Scenes/Login.unity`.
3. Configures WebGL, Gzip, data caching, and decompression fallback.
4. Includes the runtime shaders.
5. Builds the static site into `dist/`.

Confirm the result before deployment:

```bash
test -f dist/index.html
test -d dist/Build
test -d dist/TemplateData
find dist -maxdepth 2 -type f -printf '%p %s bytes\n' | sort
```

If the build fails, inspect:

```bash
tail -n 200 Logs/web-build.log
```

## Deploy an existing build to Linux

This is the recommended server workflow. Copy or extract a completed `dist/`
artifact, then publish it with a static web server.

Example deployment:

```bash
sudo install -d -m 0755 /var/www/niming-dalong
sudo rsync -a --delete dist/ /var/www/niming-dalong/
sudo find /var/www/niming-dalong -type d -exec chmod 0755 {} +
sudo find /var/www/niming-dalong -type f -exec chmod 0644 {} +
```

Before using `--delete`, verify that `/var/www/niming-dalong` is the intended
dedicated game directory. Never point it at `/var/www`, `/`, or a shared site
root.

### Nginx example

```nginx
server {
    listen 80;
    server_name game.example.com;

    root /var/www/niming-dalong;
    index index.html;

    location = /index.html {
        add_header Cache-Control "no-cache";
        try_files $uri =404;
    }

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.unityweb$ {
        default_type application/octet-stream;
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }
}
```

Validate and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Use HTTPS in production. Configure TLS through the hosting platform,
reverse proxy, or Certbot as appropriate for the server.

The current build enables Unity's JavaScript decompression fallback and emits
`.unityweb` files. This makes deployment work on static hosts that cannot set
special Gzip response headers, with a small loading-performance cost. Do not
manually add `Content-Encoding: gzip` unless the server configuration and
generated files have been tested together.

## Browser validation

Never open `dist/index.html` with a `file://` URL. Serve it over HTTP or HTTPS.

Check the deployment:

```bash
curl -fsSI https://game.example.com/
curl -fsS https://game.example.com/ | head
```

Then open the HTTPS URL in a current 64-bit Chrome browser. Also test:

- Chrome desktop at a wide and narrow viewport
- Android Chrome
- iOS Safari 15 or newer
- Login validation and guest login
- Loading progress and retry state
- Music after the first click or tap
- Browser console and Network panel for `404`, MIME, Wasm, or memory errors

Browser autoplay rules prevent reliable music playback before the first user
gesture. The login scene unlocks music on the first click, tap, or key press;
this is expected behavior.

## Common failures

### `Unity Editor not found`

Unity is not installed, is installed at another path, or
`UNITY_EDITOR_PATH` is wrong.

### `No valid Unity Editor license`

The build account has not activated Unity. Activate a legitimate license for
the same user that runs the headless build.

### `No WebGL module loaded` or unsupported build target

Install Web Build Support for Unity `6000.0.65f1`. Installing only the Editor
is insufficient.

### `NimingDalong.Editor.WebBuild.Build` cannot be found

The wrong `-projectPath` was supplied, or C# compilation failed before Unity
could load the Editor method. Check `Logs/web-build.log` for the first compiler
error.

### Loading screen opens but the game never starts

Check Chrome DevTools:

- `404`: the `Build/` directory is missing or was uploaded at the wrong level.
- HTML returned for a build file: a catch-all server rewrite is intercepting
  Unity files.
- Wasm or decompression error: the host altered compression headers or files.
- Out of memory: close other tabs and test on a 64-bit device with more memory.

### Audio starts only after clicking

This is normal browser autoplay behavior, not a deployment failure.

## Handoff checklist for another AI or server operator

1. Determine whether this machine is a **builder** or **deploy-only host**.
2. For a builder, verify Editor version, WebGL module, executable path, and
   license before running Unity.
3. For a deploy-only host, request a complete `dist/` artifact.
4. Never expose Unity source directories through the web server.
5. Verify `dist/index.html`, `dist/Build`, and `dist/TemplateData`.
6. Deploy to a dedicated directory and configure HTTPS.
7. Test the public URL in Chrome and inspect the browser console.
8. Preserve `Logs/web-build.log` when reporting a build failure.
