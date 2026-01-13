# Browser Plugin Specification

**Interface Type**: Chrome/Firefox Browser Extension
**Purpose**: Primary capture, search, and context interface for PDC
**Target Platforms**: Chrome (Manifest V3), Firefox (Manifest V3)

---

## Philosophy

One interface. One shortcut. No visual clutter.

The plugin is a **command palette** that appears when summoned and disappears when done. No toolbar icons, no injected buttons, no popups. Just a minimal, elegant input that feels like part of your thought process.

---

## Core Interactions

### 1. Command Palette

**Trigger**: `⌘⇧Space` (Mac) / `Ctrl+Shift+Space` (Windows/Linux)

A floating palette appears, centered on screen:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ _                                               │
│                                                    │
└────────────────────────────────────────────────────┘
```

That's it. A cursor. Waiting.

---

### 2. Ghost Button (Clipboard Capture)

After copying text (20+ characters), a subtle button appears near the copied text for 2 seconds:

```
                    ┌─────┐
  [copied text]     │  +  │  ← soft, semi-transparent
                    └─────┘
```

- Click or press `S` while visible → captured
- Fades after 2 seconds if ignored
- Does not appear for short text, URLs, or obvious non-content

---

### 3. Double-Tap Instant Save

`⌘⇧Space` `⌘⇧Space` (tapped twice quickly, <400ms)

Instantly saves clipboard contents. No UI appears — just a toast confirmation.

---

## Commands

### Save (Default)

Just type. No prefix needed.

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ interesting insight about semantic search       │
│                                                    │
└────────────────────────────────────────────────────┘
                                          [Enter ↵]
```

**With text selected on page**, the selection is shown:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ + "The key to knowledge management is..."      │
│                                                    │
│    Add a note (optional): _                        │
│                                                    │
└────────────────────────────────────────────────────┘
```

Press Enter to save selection with optional note.

**Feedback**: Palette shows "Saved ✓" inline, closes, then toast appears.

---

### Ask (`/`)

Search your knowledge. Start with `/`.

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ /knowledge graphs                               │
│                                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  ⦿ Notes on graph databases              2d ago   │
│  ○ Meeting: Neo4j discussion             1w ago   │
│  ○ Spec: PDC relationship model          3w ago   │
│                                                    │
└────────────────────────────────────────────────────┘
```

- Results appear as you type (debounced)
- Arrow keys to navigate
- Enter to view item detail
- Esc to dismiss

---

### Context (`@`)

Get context formatted for AI prompts. Start with `@`.

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ @help me write a blog post about PKM            │
│                                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  Context ready — 3 items, 2.1k tokens      [Copy]  │
│                                                    │
│  • Your PKM philosophy note                        │
│  • Meeting notes on knowledge systems              │
│  • Spec: PDC retrieval layer                       │
│                                                    │
└────────────────────────────────────────────────────┘
```

- Tab to copy context to clipboard
- Enter to copy and close
- Context is pre-formatted for pasting into ChatGPT/Claude

---

### Help (`?`)

Shows available commands:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  ▸ ?                                               │
│                                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  Commands                                          │
│                                                    │
│  (text)      Save a thought                        │
│  /ask        Ask your knowledge                    │
│  @context    Get context for AI                    │
│  ?           Show this help                        │
│                                                    │
│  Shortcuts                                         │
│                                                    │
│  ⌘⇧Space     Open palette                          │
│  ⌘⇧Space×2   Quick save clipboard                  │
│  S           Save (when ghost button visible)      │
│  Esc         Close palette                         │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## First-Run Experience

When the plugin is opened without configuration:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  Set up PDC                                        │
│                                                    │
│  API URL                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │ http://localhost:8000                        │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  API Key                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │ ••••••••••••••••                             │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│                                    [Connect ↵]     │
│                                                    │
└────────────────────────────────────────────────────┘
```

- Inline setup, no separate settings page
- Enter to connect
- Shows "Connected ✓" on success, then palette ready to use

---

## Visual Design

### Design Language

**Aesthetic**: System-matched, minimal, soft — like natural fiber paper.

| Mode | Background | Text | Subtle |
|------|------------|------|--------|
| Light | Warm off-white `#faf9f7` | Soft black `#2c2c2c` | Warm gray `#e8e6e3` |
| Dark | Warm dark `#1c1b1a` | Off-white `#f5f4f2` | Charcoal `#2d2c2a` |

**No harsh contrasts.** Soft shadows. Gentle borders. Calm.

### Palette Dimensions

```
Width: 520px (fixed)
Min height: 56px (just input)
Max height: 400px (with results)
Border radius: 12px
Shadow: 0 8px 32px rgba(0,0,0,0.12)
```

### Typography

```
Font: system-ui, -apple-system, "SF Pro Text", sans-serif
Input: 16px, regular weight
Results: 14px, regular weight
Timestamps: 12px, muted color
Monospace (code): "SF Mono", "Fira Code", monospace
```

### States

| State | Visual |
|-------|--------|
| Default | Cursor blinks, ready |
| Loading | Subtle pulse animation on input border |
| Success | Green checkmark, soft fade |
| Error | Warm red text, no harsh alerts |
| Selected (results) | Soft highlight, not a harsh box |

### Ghost Button

```
Size: 32px × 32px
Icon: + (plus sign, thin stroke)
Background: rgba(250, 249, 247, 0.9) light / rgba(28, 27, 26, 0.9) dark
Border: 1px solid rgba(0,0,0,0.08)
Border radius: 8px
Shadow: 0 2px 8px rgba(0,0,0,0.08)
```

Appears with soft fade-in (150ms), fades out after 2 seconds.

### Toast Notification

```
Position: Top-right, 20px from edges
Size: Auto-width, padding 12px 20px
Background: Same as palette background
Border: 1px solid subtle
Border radius: 8px
Animation: Slide in from right, fade out after 2s
```

---

## Architecture

### Extension Structure

```
browser-extension/
├── manifest.json
├── background/
│   ├── service-worker.js      # Handles API calls, shortcuts
│   └── api-client.js          # PDC API wrapper
├── content-scripts/
│   ├── palette.js             # Command palette UI
│   ├── ghost-button.js        # Clipboard capture button
│   └── styles.css             # Injected styles
├── shared/
│   ├── config.js              # Configuration management
│   └── constants.js           # Command prefixes, timings
└── assets/
    └── icons/                 # Extension icons only
```

### Communication Flow

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Content Script │ message │  Service Worker  │  HTTP   │  PDC API    │
│  (palette UI)   │────────▶│  (background)    │────────▶│  (FastAPI)  │
└─────────────────┘         └──────────────────┘         └─────────────┘
        │                           │                           │
        │ Render palette            │ Store config              │ Auth
        │ Handle input              │ Handle API calls          │ Process
        │ Show feedback             │ Cache responses           │ Return data
```

---

## Technical Implementation

### Manifest (V3)

```json
{
  "manifest_version": 3,
  "name": "PDC",
  "version": "1.0.0",
  "description": "Your personal knowledge substrate",
  "permissions": [
    "storage",
    "activeTab",
    "scripting",
    "clipboardRead"
  ],
  "host_permissions": [
    "http://localhost/*",
    "https://*/*"
  ],
  "commands": {
    "open-palette": {
      "suggested_key": {
        "default": "Ctrl+Shift+Space",
        "mac": "Command+Shift+Space"
      },
      "description": "Open PDC palette"
    }
  },
  "background": {
    "service_worker": "background/service-worker.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content-scripts/palette.js", "content-scripts/ghost-button.js"],
      "css": ["content-scripts/styles.css"],
      "run_at": "document_idle"
    }
  ],
  "icons": {
    "16": "assets/icons/icon-16.png",
    "48": "assets/icons/icon-48.png",
    "128": "assets/icons/icon-128.png"
  }
}
```

### Command Palette Core

```javascript
// content-scripts/palette.js

class PDCPalette {
  constructor() {
    this.isOpen = false;
    this.lastOpenTime = 0;
    this.element = null;
    this.selection = null;
  }

  open() {
    const now = Date.now();

    // Double-tap detection (instant clipboard save)
    if (now - this.lastOpenTime < 400 && !this.isOpen) {
      this.quickSaveClipboard();
      return;
    }

    this.lastOpenTime = now;

    if (this.isOpen) {
      this.close();
      return;
    }

    // Capture any selected text before opening
    this.selection = window.getSelection().toString().trim();

    this.render();
    this.isOpen = true;
  }

  close() {
    if (this.element) {
      this.element.remove();
      this.element = null;
    }
    this.isOpen = false;
    this.selection = null;
  }

  render() {
    this.element = document.createElement('div');
    this.element.id = 'pdc-palette';
    this.element.innerHTML = this.getTemplate();
    document.body.appendChild(this.element);

    this.bindEvents();
    this.focusInput();
  }

  getTemplate() {
    const hasSelection = this.selection && this.selection.length > 0;

    return `
      <div class="pdc-palette-container">
        <div class="pdc-palette-input-row">
          <span class="pdc-prompt">▸</span>
          ${hasSelection ? `<span class="pdc-selection">+ "${this.truncate(this.selection, 50)}"</span>` : ''}
          <input
            type="text"
            class="pdc-input"
            placeholder="${hasSelection ? 'Add a note (optional)' : ''}"
            autocomplete="off"
            spellcheck="false"
          />
        </div>
        <div class="pdc-results"></div>
      </div>
    `;
  }

  async handleInput(value) {
    const resultsEl = this.element.querySelector('.pdc-results');

    if (value.startsWith('/')) {
      // Ask mode
      const query = value.slice(1).trim();
      if (query.length > 1) {
        const results = await this.ask(query);
        resultsEl.innerHTML = this.renderAskResults(results);
      }
    } else if (value.startsWith('@')) {
      // Context mode
      const prompt = value.slice(1).trim();
      if (prompt.length > 3) {
        const context = await this.getContext(prompt);
        resultsEl.innerHTML = this.renderContextResults(context);
      }
    } else if (value === '?') {
      // Help
      resultsEl.innerHTML = this.renderHelp();
    } else {
      // Save mode - just clear results
      resultsEl.innerHTML = '';
    }
  }

  async handleSubmit(value) {
    if (value.startsWith('/') || value.startsWith('@')) {
      // Handle ask/context selection
      return;
    }

    // Save mode
    const content = this.selection
      ? { text: this.selection, note: value }
      : { text: value };

    await this.save(content);
    this.showSuccess('Saved ✓');

    setTimeout(() => {
      this.close();
      this.showToast('Saved to PDC');
    }, 400);
  }

  async quickSaveClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim().length >= 20) {
        await this.save({ text: text.trim(), source: 'clipboard' });
        this.showToast('Saved from clipboard');
      }
    } catch (err) {
      this.showToast('Could not read clipboard', 'error');
    }
  }

  truncate(str, len) {
    return str.length > len ? str.slice(0, len) + '...' : str;
  }

  // API methods delegated to service worker
  async save(content) {
    return chrome.runtime.sendMessage({ action: 'save', data: content });
  }

  async ask(query) {
    return chrome.runtime.sendMessage({ action: 'ask', data: { query } });
  }

  async getContext(prompt) {
    return chrome.runtime.sendMessage({ action: 'context', data: { prompt } });
  }
}

// Initialize
const palette = new PDCPalette();

// Listen for shortcut
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === 'open-palette') {
    palette.open();
  }
});

// Escape to close
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && palette.isOpen) {
    palette.close();
  }
});
```

### Ghost Button (Clipboard Capture)

```javascript
// content-scripts/ghost-button.js

class GhostButton {
  constructor() {
    this.button = null;
    this.fadeTimeout = null;
    this.MIN_LENGTH = 20;
    this.DISPLAY_DURATION = 2000;
  }

  init() {
    document.addEventListener('copy', () => this.onCopy());
    document.addEventListener('keydown', (e) => this.onKeydown(e));
  }

  async onCopy() {
    // Small delay to let clipboard populate
    await new Promise(r => setTimeout(r, 50));

    try {
      const text = await navigator.clipboard.readText();

      if (!this.shouldShow(text)) {
        return;
      }

      this.show();
    } catch (err) {
      // Clipboard access denied, ignore
    }
  }

  shouldShow(text) {
    if (!text || text.trim().length < this.MIN_LENGTH) {
      return false;
    }

    // Filter out URLs
    if (/^https?:\/\/\S+$/.test(text.trim())) {
      return false;
    }

    // Filter out single words
    if (!/\s/.test(text.trim())) {
      return false;
    }

    return true;
  }

  show() {
    this.hide(); // Remove any existing button

    // Get position near selection
    const selection = window.getSelection();
    let x, y;

    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      x = rect.right + window.scrollX + 8;
      y = rect.top + window.scrollY;
    } else {
      // Fallback to mouse position or corner
      x = window.innerWidth - 60;
      y = 20;
    }

    this.button = document.createElement('button');
    this.button.id = 'pdc-ghost-button';
    this.button.innerHTML = '+';
    this.button.style.cssText = `
      position: absolute;
      left: ${x}px;
      top: ${y}px;
      z-index: 999999;
    `;

    this.button.addEventListener('click', () => this.save());
    document.body.appendChild(this.button);

    // Start fade timer
    this.fadeTimeout = setTimeout(() => this.hide(), this.DISPLAY_DURATION);
  }

  hide() {
    if (this.fadeTimeout) {
      clearTimeout(this.fadeTimeout);
      this.fadeTimeout = null;
    }
    if (this.button) {
      this.button.remove();
      this.button = null;
    }
  }

  onKeydown(e) {
    // 'S' to save when ghost button is visible
    if (e.key.toLowerCase() === 's' && this.button && !this.isTyping(e)) {
      e.preventDefault();
      this.save();
    }
  }

  isTyping(e) {
    const tag = e.target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable;
  }

  async save() {
    try {
      const text = await navigator.clipboard.readText();
      await chrome.runtime.sendMessage({
        action: 'save',
        data: { text: text.trim(), source: 'clipboard' }
      });
      this.hide();
      showToast('Saved to PDC');
    } catch (err) {
      showToast('Could not save', 'error');
    }
  }
}

// Initialize
const ghostButton = new GhostButton();
ghostButton.init();
```

### Service Worker (Background)

```javascript
// background/service-worker.js

import { APIClient } from './api-client.js';

const api = new APIClient();

// Handle keyboard shortcut
chrome.commands.onCommand.addListener((command) => {
  if (command === 'open-palette') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'open-palette' });
      }
    });
  }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message).then(sendResponse);
  return true; // Keep channel open for async response
});

async function handleMessage(message) {
  const { action, data } = message;

  try {
    switch (action) {
      case 'save':
        return await api.save(data);

      case 'ask':
        return await api.ask(data.query);

      case 'context':
        return await api.getContext(data.prompt);

      case 'check-config':
        return await api.checkConfig();

      case 'set-config':
        return await api.setConfig(data);

      default:
        return { success: false, error: 'Unknown action' };
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}
```

### API Client

```javascript
// background/api-client.js

export class APIClient {
  constructor() {
    this.config = null;
  }

  async getConfig() {
    if (!this.config) {
      const stored = await chrome.storage.sync.get(['apiUrl', 'apiKey']);
      this.config = {
        apiUrl: stored.apiUrl || 'http://localhost:8000',
        apiKey: stored.apiKey || null
      };
    }
    return this.config;
  }

  async setConfig({ apiUrl, apiKey }) {
    await chrome.storage.sync.set({ apiUrl, apiKey });
    this.config = { apiUrl, apiKey };

    // Verify connection
    return await this.checkConnection();
  }

  async checkConfig() {
    const config = await this.getConfig();
    if (!config.apiKey) {
      return { configured: false };
    }
    return { configured: true, ...await this.checkConnection() };
  }

  async checkConnection() {
    try {
      const response = await this.fetch('/v1/manage/health');
      return { connected: response.ok };
    } catch {
      return { connected: false };
    }
  }

  async save(data) {
    const metadata = {
      url: data.url || null,
      title: data.title || null,
      source: data.source || 'browser_plugin',
      timestamp: new Date().toISOString()
    };

    const response = await this.fetch('/v1/capture', {
      method: 'POST',
      body: JSON.stringify({
        content: data.note ? `${data.text}\n\n---\nNote: ${data.note}` : data.text,
        metadata
      })
    });

    if (!response.ok) {
      throw new Error(`Save failed: ${response.status}`);
    }

    return { success: true, ...(await response.json()) };
  }

  async ask(query) {
    const response = await this.fetch('/v1/retrieve/semantic', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit: 10
      })
    });

    if (!response.ok) {
      throw new Error(`Ask failed: ${response.status}`);
    }

    return { success: true, ...(await response.json()) };
  }

  async getContext(prompt) {
    const response = await this.fetch('/v1/retrieve/context', {
      method: 'POST',
      body: JSON.stringify({
        query: prompt,
        max_tokens: 4000,
        format: 'markdown'
      })
    });

    if (!response.ok) {
      throw new Error(`Context failed: ${response.status}`);
    }

    return { success: true, ...(await response.json()) };
  }

  async fetch(endpoint, options = {}) {
    const config = await this.getConfig();

    if (!config.apiKey) {
      throw new Error('Not configured');
    }

    return fetch(`${config.apiUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey,
        ...options.headers
      }
    });
  }
}
```

### Styles

```css
/* content-scripts/styles.css */

/* === Design Tokens === */
:root {
  --pdc-bg-light: #faf9f7;
  --pdc-bg-dark: #1c1b1a;
  --pdc-text-light: #2c2c2c;
  --pdc-text-dark: #f5f4f2;
  --pdc-subtle-light: #e8e6e3;
  --pdc-subtle-dark: #2d2c2a;
  --pdc-muted-light: #8a8885;
  --pdc-muted-dark: #6b6966;
  --pdc-success: #2d8a5e;
  --pdc-error: #c45c4a;
  --pdc-radius: 12px;
  --pdc-radius-sm: 8px;
  --pdc-shadow: 0 8px 32px rgba(0,0,0,0.12);
  --pdc-font: system-ui, -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
  --pdc-mono: "SF Mono", "Fira Code", "Consolas", monospace;
}

/* === Palette === */
#pdc-palette {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(2px);
  animation: pdc-fade-in 0.15s ease-out;
}

@keyframes pdc-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.pdc-palette-container {
  width: 520px;
  max-height: 400px;
  overflow: hidden;
  border-radius: var(--pdc-radius);
  box-shadow: var(--pdc-shadow);
  font-family: var(--pdc-font);
  animation: pdc-slide-up 0.15s ease-out;
}

@keyframes pdc-slide-up {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Light mode (default) */
.pdc-palette-container {
  background: var(--pdc-bg-light);
  color: var(--pdc-text-light);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .pdc-palette-container {
    background: var(--pdc-bg-dark);
    color: var(--pdc-text-dark);
  }

  .pdc-results {
    border-top-color: var(--pdc-subtle-dark);
  }

  .pdc-result-item:hover,
  .pdc-result-item.selected {
    background: var(--pdc-subtle-dark);
  }
}

.pdc-palette-input-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  gap: 8px;
}

.pdc-prompt {
  font-family: var(--pdc-mono);
  font-size: 16px;
  opacity: 0.5;
}

.pdc-selection {
  font-size: 14px;
  color: var(--pdc-muted-light);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (prefers-color-scheme: dark) {
  .pdc-selection {
    color: var(--pdc-muted-dark);
  }
}

.pdc-input {
  flex: 1;
  border: none;
  background: transparent;
  font-family: var(--pdc-font);
  font-size: 16px;
  color: inherit;
  outline: none;
}

.pdc-input::placeholder {
  color: var(--pdc-muted-light);
}

@media (prefers-color-scheme: dark) {
  .pdc-input::placeholder {
    color: var(--pdc-muted-dark);
  }
}

/* === Results === */
.pdc-results {
  border-top: 1px solid var(--pdc-subtle-light);
  max-height: 320px;
  overflow-y: auto;
}

.pdc-results:empty {
  display: none;
}

.pdc-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.pdc-result-item:hover,
.pdc-result-item.selected {
  background: var(--pdc-subtle-light);
}

.pdc-result-title {
  font-size: 14px;
  flex: 1;
}

.pdc-result-meta {
  font-size: 12px;
  color: var(--pdc-muted-light);
}

@media (prefers-color-scheme: dark) {
  .pdc-result-meta {
    color: var(--pdc-muted-dark);
  }
}

/* === Context Results === */
.pdc-context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
}

.pdc-context-info {
  font-size: 14px;
}

.pdc-context-copy {
  padding: 6px 12px;
  border: 1px solid var(--pdc-subtle-light);
  border-radius: var(--pdc-radius-sm);
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.1s ease;
}

.pdc-context-copy:hover {
  background: var(--pdc-subtle-light);
}

@media (prefers-color-scheme: dark) {
  .pdc-context-copy {
    border-color: var(--pdc-subtle-dark);
  }

  .pdc-context-copy:hover {
    background: var(--pdc-subtle-dark);
  }
}

.pdc-context-items {
  padding: 0 20px 16px;
}

.pdc-context-item {
  font-size: 13px;
  padding: 4px 0;
  color: var(--pdc-muted-light);
}

@media (prefers-color-scheme: dark) {
  .pdc-context-item {
    color: var(--pdc-muted-dark);
  }
}

/* === Help === */
.pdc-help {
  padding: 16px 20px;
}

.pdc-help-section {
  margin-bottom: 16px;
}

.pdc-help-section:last-child {
  margin-bottom: 0;
}

.pdc-help-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--pdc-muted-light);
  margin-bottom: 8px;
}

@media (prefers-color-scheme: dark) {
  .pdc-help-title {
    color: var(--pdc-muted-dark);
  }
}

.pdc-help-row {
  display: flex;
  gap: 16px;
  padding: 4px 0;
  font-size: 13px;
}

.pdc-help-cmd {
  font-family: var(--pdc-mono);
  min-width: 100px;
}

/* === Ghost Button === */
#pdc-ghost-button {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--pdc-radius-sm);
  background: rgba(250, 249, 247, 0.95);
  color: var(--pdc-text-light);
  font-size: 18px;
  font-weight: 300;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.15s ease;
  animation: pdc-ghost-in 0.15s ease-out;
}

@keyframes pdc-ghost-in {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

#pdc-ghost-button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

@media (prefers-color-scheme: dark) {
  #pdc-ghost-button {
    background: rgba(28, 27, 26, 0.95);
    color: var(--pdc-text-dark);
    border-color: rgba(255, 255, 255, 0.08);
  }
}

/* === Toast === */
#pdc-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000000;
  padding: 12px 20px;
  border-radius: var(--pdc-radius-sm);
  font-family: var(--pdc-font);
  font-size: 14px;
  box-shadow: var(--pdc-shadow);
  animation: pdc-toast-in 0.2s ease-out;
}

@keyframes pdc-toast-in {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

#pdc-toast.pdc-toast-success {
  background: var(--pdc-bg-light);
  color: var(--pdc-success);
  border: 1px solid var(--pdc-subtle-light);
}

#pdc-toast.pdc-toast-error {
  background: var(--pdc-bg-light);
  color: var(--pdc-error);
  border: 1px solid var(--pdc-subtle-light);
}

@media (prefers-color-scheme: dark) {
  #pdc-toast {
    background: var(--pdc-bg-dark);
    border-color: var(--pdc-subtle-dark);
  }
}

/* === Setup Form === */
.pdc-setup {
  padding: 20px;
}

.pdc-setup-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.pdc-setup-field {
  margin-bottom: 16px;
}

.pdc-setup-label {
  display: block;
  font-size: 12px;
  color: var(--pdc-muted-light);
  margin-bottom: 6px;
}

@media (prefers-color-scheme: dark) {
  .pdc-setup-label {
    color: var(--pdc-muted-dark);
  }
}

.pdc-setup-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--pdc-subtle-light);
  border-radius: var(--pdc-radius-sm);
  background: transparent;
  font-family: var(--pdc-font);
  font-size: 14px;
  color: inherit;
  outline: none;
  transition: border-color 0.15s ease;
}

.pdc-setup-input:focus {
  border-color: var(--pdc-text-light);
}

@media (prefers-color-scheme: dark) {
  .pdc-setup-input {
    border-color: var(--pdc-subtle-dark);
  }

  .pdc-setup-input:focus {
    border-color: var(--pdc-text-dark);
  }
}

.pdc-setup-submit {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: var(--pdc-radius-sm);
  background: var(--pdc-text-light);
  color: var(--pdc-bg-light);
  font-family: var(--pdc-font);
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.pdc-setup-submit:hover {
  opacity: 0.9;
}

@media (prefers-color-scheme: dark) {
  .pdc-setup-submit {
    background: var(--pdc-text-dark);
    color: var(--pdc-bg-dark);
  }
}
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Palette open | <50ms |
| Save to API | <100ms response |
| Ask results | <500ms |
| Context retrieval | <500ms |
| Ghost button appear | <100ms after copy |
| Extension bundle | <200KB |
| Memory footprint | <30MB |

---

## Security

### API Key Storage
- Stored in Chrome's encrypted `chrome.storage.sync`
- Never logged to console
- Masked in setup form
- Transmitted only over HTTPS (except localhost)

### Content Security
- No `eval()` or dynamic code execution
- All DOM injection uses safe methods
- No inline event handlers
- CSP-compliant

### Permissions
- `storage` — API key and config
- `activeTab` — Read selection, inject palette
- `scripting` — Inject content scripts
- `clipboardRead` — Ghost button functionality

---

## Testing

### Unit Tests

```javascript
describe('PDCPalette', () => {
  test('double-tap triggers quick save', async () => {
    palette.open();
    await sleep(100);
    palette.open(); // Second tap within 400ms

    expect(api.save).toHaveBeenCalledWith(
      expect.objectContaining({ source: 'clipboard' })
    );
  });

  test('parses /ask command correctly', () => {
    expect(palette.parseCommand('/knowledge graphs')).toEqual({
      type: 'ask',
      query: 'knowledge graphs'
    });
  });

  test('parses @context command correctly', () => {
    expect(palette.parseCommand('@help me write')).toEqual({
      type: 'context',
      prompt: 'help me write'
    });
  });
});
```

### Integration Tests

```javascript
describe('Ghost Button', () => {
  test('appears after copying substantial text', async () => {
    await page.evaluate(() => {
      navigator.clipboard.writeText('This is substantial text that is long enough');
      document.dispatchEvent(new Event('copy'));
    });

    await page.waitForSelector('#pdc-ghost-button');
    expect(await page.$('#pdc-ghost-button')).toBeTruthy();
  });

  test('does not appear for short text', async () => {
    await page.evaluate(() => {
      navigator.clipboard.writeText('short');
      document.dispatchEvent(new Event('copy'));
    });

    await sleep(200);
    expect(await page.$('#pdc-ghost-button')).toBeFalsy();
  });
});
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-01-13 | Complete redesign: command palette, ghost button, minimal UI |
| 1.0.0 | 2026-01-12 | Initial specification (deprecated) |

---

**Status**: Specification Complete
**Related**: Features 1.5, 1.6 in `roadmap.md`
