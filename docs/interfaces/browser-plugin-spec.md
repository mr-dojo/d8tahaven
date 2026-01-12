# Browser Plugin Specification

**Interface Type**: Chrome/Firefox Browser Extension
**Purpose**: Primary capture and context injection interface for PDC
**Target Platforms**: Chrome (Manifest V3), Firefox (Manifest V3)

---

## Overview

The browser plugin is the **primary interface** for the PDC system, providing two core modes:

1. **SAVE Mode**: One-click content capture from any webpage
2. **GET Context Mode**: Inject relevant PDC context into LLM text inputs

**Core UX Principle**: Minimal friction. No forms, no interruptions, no context switching.

---

## Architecture

### Extension Components

```
browser-extension/
├── manifest.json              # Extension configuration (V3)
├── background/
│   ├── service-worker.js      # Background service worker
│   └── api-client.js          # PDC API communication
├── content-scripts/
│   ├── save-mode.js           # Text selection detection
│   ├── get-mode.js            # LLM interface detection
│   └── ui-injector.js         # Button injection
├── popup/
│   ├── popup.html             # Extension popup UI
│   ├── popup.js               # Settings, API key config
│   └── popup.css              # Styles
├── options/
│   ├── options.html           # Settings page
│   └── options.js             # Configuration management
└── assets/
    ├── icons/                 # Extension icons
    └── styles/                # Injected UI styles
```

### Communication Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Content   │ message │   Service    │  HTTP   │  PDC API    │
│   Script    │────────▶│   Worker     │────────▶│  Backend    │
│ (webpage)   │         │ (background) │         │ (FastAPI)   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                         │                       │
      │ Inject UI               │ Store config          │ Auth/Rate limit
      │ Detect selection        │ Handle API calls      │ Return data
      │ Read prompt text        │ Cache responses       │
```

---

## SAVE Mode Specification

### User Experience Flow

1. User highlights text on any webpage
2. Plugin detects selection, injects "Save to PDC" button near selection
3. User clicks button
4. Visual confirmation (toast notification: "Saved to PDC!")
5. Button disappears
6. Background: Content sent to PDC, enrichment queued

**Time to capture**: <2 seconds from highlight to confirmation

---

### Technical Implementation

#### 1. Text Selection Detection

**Content Script**: `save-mode.js`

```javascript
// Detect text selection
document.addEventListener('mouseup', (event) => {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();

  if (selectedText.length > 10) {  // Minimum 10 characters
    showSaveButton(selection, selectedText);
  } else {
    hideSaveButton();
  }
});

// Handle text selection via keyboard
document.addEventListener('keyup', (event) => {
  if (event.key === 'ArrowUp' || event.key === 'ArrowDown' ||
      event.key === 'Shift') {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (selectedText.length > 10) {
      showSaveButton(selection, selectedText);
    }
  }
});
```

#### 2. Button Injection

**UI Injector**: `ui-injector.js`

```javascript
function showSaveButton(selection, text) {
  // Remove existing button if any
  hideSaveButton();

  // Get selection bounding rectangle
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  // Create button element
  const button = document.createElement('button');
  button.id = 'pdc-save-button';
  button.className = 'pdc-save-btn';
  button.innerHTML = '📥 Save to PDC';
  button.style.position = 'absolute';
  button.style.top = `${rect.bottom + window.scrollY + 5}px`;
  button.style.left = `${rect.left + window.scrollX}px`;
  button.style.zIndex = '999999';

  // Attach click handler
  button.addEventListener('click', () => handleSave(text));

  document.body.appendChild(button);
}

function hideSaveButton() {
  const existing = document.getElementById('pdc-save-button');
  if (existing) existing.remove();
}
```

#### 3. Capture Handler

**Content Script** → **Service Worker** message:

```javascript
async function handleSave(content) {
  // Show loading state
  updateButtonState('saving');

  // Capture metadata
  const metadata = {
    url: window.location.href,
    title: document.title,
    domain: window.location.hostname,
    timestamp: new Date().toISOString()
  };

  // Send to service worker
  chrome.runtime.sendMessage({
    action: 'save_content',
    data: { content, metadata }
  }, (response) => {
    if (response.success) {
      showToast('✓ Saved to PDC!', 'success');
      hideSaveButton();
    } else {
      showToast('✗ Save failed', 'error');
      updateButtonState('error');
    }
  });
}
```

**Service Worker**: `background/service-worker.js`

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'save_content') {
    saveToPDC(message.data)
      .then(result => sendResponse({ success: true, capture_id: result.capture_id }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;  // Keep message channel open for async response
  }
});

async function saveToPDC({ content, metadata }) {
  const apiKey = await getStoredApiKey();
  const apiUrl = await getStoredApiUrl();

  const response = await fetch(`${apiUrl}/v1/capture`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({
      content: content,
      source: 'browser_plugin',
      metadata: metadata
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return await response.json();
}
```

#### 4. Visual Confirmation

```javascript
function showToast(message, type) {
  const toast = document.createElement('div');
  toast.className = `pdc-toast pdc-toast-${type}`;
  toast.textContent = message;
  toast.style.position = 'fixed';
  toast.style.top = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '1000000';
  toast.style.padding = '12px 20px';
  toast.style.borderRadius = '6px';
  toast.style.background = type === 'success' ? '#10b981' : '#ef4444';
  toast.style.color = 'white';
  toast.style.fontFamily = 'system-ui, -apple-system, sans-serif';
  toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 2000);
}
```

---

### Keyboard Shortcut (Optional Enhancement)

**User Preference**: `Cmd+Shift+S` (Mac) or `Ctrl+Shift+S` (Windows/Linux)

```javascript
// manifest.json
{
  "commands": {
    "save-selection": {
      "suggested_key": {
        "default": "Ctrl+Shift+S",
        "mac": "Command+Shift+S"
      },
      "description": "Save selected text to PDC"
    }
  }
}

// background/service-worker.js
chrome.commands.onCommand.addListener((command) => {
  if (command === 'save-selection') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'save_current_selection' });
    });
  }
});
```

---

## GET Context Mode Specification

### User Experience Flow

1. User is in an LLM interface (Claude, ChatGPT, Copilot, etc.)
2. User types initial prompt: "Help me write about data sovereignty"
3. Plugin detects LLM text input, injects "Get Context" button near field
4. User clicks "Get Context"
5. Plugin reads prompt text, queries PDC retrieval API
6. Relevant context block inserted into text field at cursor position
7. User reviews context, edits if needed, sends to LLM

**Time to retrieve**: <1 second from click to context insertion

---

### Technical Implementation

#### 1. LLM Interface Detection

**Content Script**: `get-mode.js`

```javascript
// Known LLM interface selectors
const LLM_SELECTORS = {
  claude: 'div[contenteditable="true"][data-test-id="user-input"]',
  chatgpt: 'textarea[data-id="root"]',
  copilot: 'textarea.monaco-editor',
  perplexity: 'textarea[placeholder*="Ask anything"]',
  // Add more as needed
};

// Detect LLM interfaces
function detectLLMInputs() {
  for (const [name, selector] of Object.entries(LLM_SELECTORS)) {
    const inputs = document.querySelectorAll(selector);
    if (inputs.length > 0) {
      inputs.forEach(input => {
        if (!input.dataset.pdcButtonInjected) {
          injectGetContextButton(input, name);
          input.dataset.pdcButtonInjected = 'true';
        }
      });
    }
  }
}

// Watch for dynamically loaded inputs (SPAs)
const observer = new MutationObserver(() => {
  detectLLMInputs();
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Initial detection
detectLLMInputs();
```

#### 2. Button Injection

```javascript
function injectGetContextButton(inputElement, llmType) {
  const button = document.createElement('button');
  button.className = 'pdc-get-context-btn';
  button.innerHTML = '🔍 Get Context';
  button.style.position = 'absolute';
  button.style.zIndex = '999999';

  // Position relative to input field
  const rect = inputElement.getBoundingClientRect();
  button.style.top = `${rect.top - 40}px`;
  button.style.right = `${window.innerWidth - rect.right}px`;

  button.addEventListener('click', () => handleGetContext(inputElement, llmType));

  document.body.appendChild(button);

  // Reposition on scroll/resize
  window.addEventListener('scroll', () => updateButtonPosition(button, inputElement));
  window.addEventListener('resize', () => updateButtonPosition(button, inputElement));
}
```

#### 3. Context Retrieval Handler

```javascript
async function handleGetContext(inputElement, llmType) {
  // Show loading state
  updateButtonState('loading');

  // Read current prompt text
  const promptText = getInputText(inputElement, llmType);

  if (!promptText || promptText.trim().length < 10) {
    showToast('Type a prompt first', 'warning');
    return;
  }

  // Query PDC retrieval API
  chrome.runtime.sendMessage({
    action: 'get_context',
    data: {
      query: promptText,
      max_tokens: 4000,
      format: 'markdown'
    }
  }, (response) => {
    if (response.success) {
      insertContext(inputElement, response.context, llmType);
      showToast(`✓ Added ${response.items_count} items`, 'success');
    } else {
      showToast('✗ Context retrieval failed', 'error');
    }
    updateButtonState('ready');
  });
}

function getInputText(inputElement, llmType) {
  if (inputElement.tagName === 'TEXTAREA') {
    return inputElement.value;
  } else {
    return inputElement.textContent || inputElement.innerText;
  }
}
```

**Service Worker**: API call

```javascript
async function getContextFromPDC({ query, max_tokens, format }) {
  const apiKey = await getStoredApiKey();
  const apiUrl = await getStoredApiUrl();

  const response = await fetch(`${apiUrl}/v1/retrieve/context`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({
      query: query,
      max_tokens: max_tokens,
      format: format
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return await response.json();
}
```

#### 4. Context Insertion

```javascript
function insertContext(inputElement, contextText, llmType) {
  const formattedContext = formatContextBlock(contextText);

  if (inputElement.tagName === 'TEXTAREA') {
    // Plain textarea (ChatGPT, Perplexity)
    const cursorPos = inputElement.selectionStart;
    const currentText = inputElement.value;
    const newText = currentText.slice(0, cursorPos) +
                   '\n\n' + formattedContext + '\n\n' +
                   currentText.slice(cursorPos);

    inputElement.value = newText;
    inputElement.focus();
    inputElement.selectionStart = cursorPos + formattedContext.length + 4;

  } else {
    // ContentEditable div (Claude)
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);

    const contextNode = document.createTextNode('\n\n' + formattedContext + '\n\n');
    range.insertNode(contextNode);

    // Move cursor after inserted text
    range.setStartAfter(contextNode);
    range.setEndAfter(contextNode);
    selection.removeAllRanges();
    selection.addRange(range);

    inputElement.focus();
  }

  // Trigger input event (some LLMs need this)
  inputElement.dispatchEvent(new Event('input', { bubbles: true }));
}

function formatContextBlock(contextText) {
  return `--- PDC Context ---\n${contextText}\n--- End Context ---`;
}
```

---

## Configuration & Settings

### Extension Popup

**Purpose**: Quick access to settings and status

**UI Elements**:
- API Key input (masked)
- API URL input (default: `http://localhost:8000`)
- Status indicator (connected/disconnected)
- Recent captures count (last 24h)
- Quick links (dashboard, settings)

**Popup HTML**: `popup/popup.html`

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="popup-container">
    <header>
      <h1>PDC Browser Plugin</h1>
      <span class="status" id="status-indicator">●</span>
    </header>

    <section class="config">
      <label>API URL:</label>
      <input type="text" id="api-url" placeholder="http://localhost:8000">

      <label>API Key:</label>
      <input type="password" id="api-key" placeholder="Enter your API key">

      <button id="save-config">Save Configuration</button>
    </section>

    <section class="stats">
      <div class="stat">
        <span class="stat-label">Captured today:</span>
        <span class="stat-value" id="capture-count">-</span>
      </div>
    </section>

    <footer>
      <a href="#" id="open-dashboard">Open Dashboard</a>
      <a href="#" id="open-settings">Settings</a>
    </footer>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

---

### Storage Schema

**Chrome Storage API** (encrypted for API key):

```javascript
const CONFIG_SCHEMA = {
  api_url: 'http://localhost:8000',
  api_key: null,  // Encrypted
  save_mode_enabled: true,
  get_mode_enabled: true,
  keyboard_shortcut_enabled: true,
  toast_duration: 2000,
  context_max_tokens: 4000,
  context_format: 'markdown',
  capture_stats: {
    today: 0,
    this_week: 0,
    total: 0
  }
};

// Store config
async function saveConfig(config) {
  await chrome.storage.sync.set(config);
}

// Retrieve config
async function getConfig() {
  return await chrome.storage.sync.get(CONFIG_SCHEMA);
}
```

---

## Security Considerations

### 1. API Key Storage

- Store in Chrome's encrypted storage (`chrome.storage.sync`)
- Never log API key in console
- Mask in UI display
- Clear on logout/reset

### 2. Content Security

- Sanitize all injected HTML/CSS
- Avoid eval() or innerHTML with user data
- Validate API responses before insertion

### 3. Permissions (Manifest V3)

```json
{
  "manifest_version": 3,
  "name": "PDC Browser Plugin",
  "version": "1.0.0",
  "permissions": [
    "storage",           // Store API key and config
    "activeTab",         // Access current tab content
    "scripting"          // Inject content scripts
  ],
  "host_permissions": [
    "http://localhost/*",   // Local PDC API
    "https://*/*"           // User's custom PDC domain
  ],
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content-scripts/save-mode.js", "content-scripts/get-mode.js"],
      "run_at": "document_idle"
    }
  ],
  "background": {
    "service_worker": "background/service-worker.js"
  }
}
```

---

## Error Handling

### Network Errors

```javascript
async function callAPI(endpoint, data) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      if (response.status === 401) {
        showToast('Invalid API key', 'error');
        openConfigPopup();
      } else if (response.status === 429) {
        showToast('Rate limit exceeded', 'warning');
      } else if (response.status >= 500) {
        showToast('Server error. Try again.', 'error');
      }
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();

  } catch (error) {
    if (error.name === 'TypeError') {
      showToast('Cannot reach PDC server', 'error');
    }
    throw error;
  }
}
```

### Offline Support (Future Enhancement)

- Cache failed captures in local storage
- Retry when connection restored
- Show pending count in popup

---

## Testing Strategy

### Unit Tests (Jest)

```javascript
describe('Text Selection Detection', () => {
  test('should show button for selections >10 chars', () => {
    // Mock selection
    window.getSelection = jest.fn(() => ({
      toString: () => 'This is a long enough selection'
    }));

    triggerMouseup();
    expect(document.getElementById('pdc-save-button')).toBeTruthy();
  });

  test('should NOT show button for short selections', () => {
    window.getSelection = jest.fn(() => ({
      toString: () => 'Short'
    }));

    triggerMouseup();
    expect(document.getElementById('pdc-save-button')).toBeFalsy();
  });
});
```

### Integration Tests (Puppeteer)

```javascript
describe('SAVE Mode E2E', () => {
  test('should capture highlighted text from webpage', async () => {
    await page.goto('https://example.com');
    await page.evaluate(() => {
      const range = document.createRange();
      range.selectNodeContents(document.querySelector('p'));
      window.getSelection().addRange(range);
    });

    await page.waitForSelector('#pdc-save-button');
    await page.click('#pdc-save-button');

    await page.waitForSelector('.pdc-toast');
    const toastText = await page.$eval('.pdc-toast', el => el.textContent);
    expect(toastText).toContain('Saved to PDC');
  });
});
```

### Manual Testing Checklist

- [ ] SAVE mode works on static HTML pages
- [ ] SAVE mode works on SPAs (React, Vue, etc.)
- [ ] SAVE mode works with complex selections (multiple paragraphs)
- [ ] GET mode detects Claude interface
- [ ] GET mode detects ChatGPT interface
- [ ] GET mode inserts context at correct cursor position
- [ ] API key storage persists across sessions
- [ ] Rate limiting handled gracefully
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Keyboard shortcuts work

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Button injection latency | <50ms | Time from mouseup to button visible |
| Capture API call | <100ms | Time from click to API response |
| Context retrieval | <500ms | Time from click to API response |
| Context insertion | <50ms | Time from API response to text inserted |
| Extension bundle size | <500KB | Total extension package size |
| Memory footprint | <50MB | RAM usage when active |

---

## Future Enhancements

### Phase 2 Features

- **Voice capture**: Record audio notes, transcribe, send to PDC
- **Image capture**: OCR on screenshots, extract text
- **Automatic capture**: Auto-save bookmarks, tweets, Reddit posts
- **Smart suggestions**: Proactively suggest context based on page content
- **Multi-selection**: Capture multiple selections at once
- **Annotation**: Add notes/tags before saving

### Phase 3 Features

- **Mobile browser extension**: Safari for iOS, Chrome for Android
- **Desktop app integration**: System-wide hotkey for any application
- **Collaborative features**: Share captures with team
- **Advanced filtering**: Configure which sites trigger plugin features

---

**Last Updated**: 2026-01-12
**Status**: Specification Complete, Implementation Pending
**Related**: Features 1.5, 1.6 in `roadmap.md`
