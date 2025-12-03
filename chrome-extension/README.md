# VigilAI Chrome Extension

A Chrome extension that provides instant competitive intelligence when visiting competitor websites.

## Features

- 🎯 **Auto-detection**: Automatically detects when you're on a competitor's website
- 💪 **Instant Battlecards**: Shows kill points and objection handling in a popup
- 🔄 **Real-time Sync**: Syncs with your VigilAI dashboard
- 🎨 **Non-intrusive**: Minimalist design that doesn't interfere with your browsing

## Installation

### Development Mode

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder

### From Chrome Web Store

Coming soon!

## Setup

1. Click the VigilAI extension icon in your toolbar
2. Enter your API URL (default: `http://localhost:8000`)
3. Enter your API token (get this from VigilAI dashboard → Settings → API Keys)
4. Click "Connect"

## Usage

1. Visit any competitor website you've added to VigilAI
2. A widget will automatically appear in the bottom-right corner
3. Click to expand and view:
   - Kill points (why you win)
   - Objection handling responses
   - Quick link to full battlecard

## Development

### File Structure

```
chrome-extension/
├── manifest.json       # Extension configuration
├── content.js          # Injected into web pages
├── content.css         # Widget styling
├── popup.html          # Extension popup UI
├── popup.js            # Popup logic
├── background.js       # Service worker
└── icons/              # Extension icons
```

### Building for Production

1. Update version in `manifest.json`
2. Create icons (16x16, 48x48, 128x128)
3. Zip the extension folder
4. Upload to Chrome Web Store

## Permissions

- `activeTab`: To detect current website domain
- `storage`: To store API credentials securely
- `host_permissions`: To communicate with VigilAI API

## Security

- API tokens are stored locally using Chrome's secure storage API
- All API calls use HTTPS in production
- No data is collected or sent to third parties

## Support

For issues or feature requests, please visit:
https://github.com/yourusername/vigilai/issues
