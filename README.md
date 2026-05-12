# LocalSend for Calibre

[![Release](https://img.shields.io/github/v/release/fer-martin/LocalSendCalibre?logo=github)](../../releases/latest)
[![Downloads](https://img.shields.io/github/downloads/fer-martin/LocalSendCalibre/total?logo=github)](../../releases)
[![Receiver: LocalSendKobo](https://img.shields.io/badge/receiver-LocalSendKobo-blue?logo=go)](https://github.com/fer-martin/LocalSendKobo)

A [Calibre](https://calibre-ebook.com/) plugin that transfers books to any device running [LocalSend](https://localsend.org/) over your local network — with automatic conversion to KEPUB for Kobo e-readers.

![screenshot placeholder](docs/screenshot.png)

## Features

- 📡 **Automatic discovery** of LocalSend devices on the LAN via multicast UDP.
- 📝 **Manual IP fallback** for networks where multicast is blocked or filtered.
- 📚 **Automatic EPUB → KEPUB conversion** using Calibre's built-in KEPUB Output plugin (the same conversion that runs when sending to a Kobo over USB). The book lands on the device's *Books* shelf with proper formatting.
- 🖱️ Available from the **main toolbar** and the **right-click context menu** for books in the library.
- ⚙️ Runs as a **background job** with progress visible in Calibre's Jobs panel — the UI never blocks during conversion or transfer.
- 🛠️ Configurable behavior (enable/disable kepubification, etc.).

## Why?

USB transfer isn't always practical: you may not have the cable, may be on a different machine, or simply prefer Wi-Fi. LocalSend offers a fast, peer-to-peer alternative. Several LocalSend clients exist for Kobo e-readers — combine one with this plugin and you can push books to your reader without cables.

## Non-goals

To keep the plugin focused and maintainable, the following are explicitly **out of scope**:

- ❌ **Not a replacement for Calibre's Kobo USB driver.** No metadata sync, reading-progress sync, collections/shelves management, or device-side library manipulation. The plugin only **delivers files**; the device's library scanner picks them up afterwards.
- ❌ **No bidirectional transfer.** Books are sent only; the plugin does not pull files from the device.
- ❌ **No TLS/HTTPS.** The plugin uses LocalSend's plain HTTP mode. Use it only on networks you trust.
- ❌ **No general-purpose file types.** Only e-book formats handled by Calibre's library are supported (currently EPUB and KEPUB).
- ❌ **Not a full LocalSend client.** No clipboard/text-snippet sending, no receiving, no downloads.
- ❌ **No simultaneous multi-device fan-out.** One target device per send action.

## Requirements

- **Calibre 7.0** or newer (for the built-in KEPUB Output plugin).
- A device with a LocalSend server reachable on your LAN.

## Installation

1. Download the latest `localsend-calibre-plugin.zip` from the [Releases page](../../releases).
2. In Calibre: **Preferences → Plugins → Load plugin from file** → select the ZIP.
3. When prompted, choose where to display the plugin (toolbar and/or context menu).
4. Restart Calibre.

## Usage

1. Open LocalSend on the receiving device and ensure it is discoverable.
2. Select one or more books in the Calibre library.
3. Click **Send via LocalSend** in the toolbar, or right-click → **Send via LocalSend**.
4. The plugin scans the network (~4 s). Pick a device from the list or enter an IP manually.
5. Accept the transfer prompt on the receiving device.

Progress is displayed in Calibre's Jobs panel (bottom-right). When the transfer finishes, a summary dialog reports successes and failures.

## Configuration

**Preferences → Plugins → Send via LocalSend → Customize plugin**

- **Convert EPUB → KEPUB automatically** (default: on). Disable to send the original `.epub` file unchanged.

## How it works

LocalSend uses a documented JSON-over-HTTP protocol on port `53317`, with UDP multicast on `224.0.0.167:53317` for discovery. This plugin:

1. Broadcasts a multicast announcement and listens for replies and incoming announcements from peers.
2. For each book, optionally converts EPUB → KEPUB through Calibre's `Plumber` pipeline using the KEPUB Output format plugin.
3. Performs the LocalSend two-step upload: `POST /api/localsend/v2/prepare-upload` followed by `POST /api/localsend/v2/upload?sessionId=…&fileId=…&token=…`.

See the [LocalSend protocol specification](https://github.com/localsend/protocol) for full details.

## Development

```bash
git clone https://github.com/<your-user>/localsend-calibre-plugin
cd localsend-calibre-plugin
./build.sh           # produces dist/localsend-calibre-plugin.zip
```

Or install directly from source for testing (no ZIP needed):

```bash
calibre-customize -b plugin/
```

Then restart Calibre.

## Contributing

Issues and pull requests welcome. Please describe your environment (OS, Calibre version, receiving device) and include relevant log output (`calibre-debug -g`) when reporting bugs.

## Companion tool: kobo-localsend

LocalSendCalibre talks to **any** LocalSend v2 receiver, but it pairs especially well with **[kobo-localsend](https://github.com/fer-martin/LocalSendKobo)** — a minimal receiver written in Go for Kobo e-readers. Together they give you a one-click pipeline from your Calibre library to your Kobo, over Wi-Fi, with no cables and no Calibre Companion server.

**What kobo-localsend adds on the Kobo side:**

- Single static binary (~5 MB), no Python or runtime to install.
- Native Nickel integration: toast on each completed transfer, modal *Stop* dialog while it's running, automatic library rescan when books arrive.
- Auto-discoverable on the local Wi-Fi (shows up as e.g. `Kobo Aura 1234`).
- Installable via NickelMenu so you can toggle it from the device UI.

**Typical workflow:**

1. On the Kobo: NickelMenu → **LocalSend (start)**.
2. In Calibre: right-click a book → **Send via LocalSend** → pick your Kobo.
3. The file is transferred over Wi-Fi, the on-device toast confirms `Received: <title>.epub`, and the Nickel library is rescanned automatically — the book shows up on the home screen.

See the [kobo-localsend README](https://github.com/fer-martin/LocalSendKobo#readme) for build & installation instructions.

## License

[MIT](LICENSE)