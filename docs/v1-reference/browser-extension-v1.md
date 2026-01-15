# Browser Extension - V1 Simple Popup

**Scope**: Dead-simple popup for capture and retrieval (no command palette, no ghost button).
**Target**: Chrome/Edge (Manifest V3)
**Priority**: Working > Pretty

---

## What V1 IS

A **basic popup extension** with:
- Textarea for entering content
- "Save" button → POST to `/v1/capture`
- "Get Context" button → Query API + copy to clipboard
- Simple success/error messages

**That's it.** No fancy UX. Prove the value first.

---

## What V1 is NOT

- ❌ Command palette (`⌘⇧Space`)
- ❌ Ghost button (clipboard capture)
- ❌ Double-tap shortcuts
- ❌ Inline page injection
- ❌ System-matched design aesthetics
- ❌ First-run setup flow

**Defer all of this to v2.** See `docs/v2-vision/browser-plugin-full.md` for future vision.

---

## File Structure

```
browser-extension/
├── manifest.json          # Chrome extension manifest
├── popup.html            # Simple popup UI
├── popup.js              # Save/retrieve logic
├── popup.css             # Minimal styling
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── config.js             # API endpoint configuration
```

**Total**: ~200 lines of code max.

---

## manifest.json

```json
{
  "manifest_version": 3,
  "name": "Context Substrate",
  "version": "0.1.0",
  "description": "Capture content for your personal AI memory",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png"
    }
  },
  "permissions": [
    "activeTab",
    "clipboardWrite"
  ],
  "host_permissions": [
    "http://localhost:8000/*"
  ]
}
```

**Permissions**:
- `activeTab`: Read current tab URL/title
- `clipboardWrite`: Copy context to clipboard

**No background service worker in v1** - keep it simple.

---

## popup.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <h1>Context Substrate</h1>

    <!-- Capture Section -->
    <div class="section">
      <label for="content">Capture Content:</label>
      <textarea id="content" placeholder="Paste or type content to save..." rows="6"></textarea>
      <button id="save-btn">Save</button>
    </div>

    <!-- Retrieve Section -->
    <div class="section">
      <label for="query">Search Context:</label>
      <input type="text" id="query" placeholder="What are you looking for?" />
      <button id="search-btn">Get Context</button>
    </div>

    <!-- Status Messages -->
    <div id="status" class="status"></div>
  </div>

  <script src="config.js"></script>
  <script src="popup.js"></script>
</body>
</html>
```

**Simple structure**:
- Textarea for content
- Save button
- Search input + button
- Status div for feedback

---

## popup.css

```css
body {
  width: 400px;
  padding: 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
}

.container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

h1 {
  font-size: 18px;
  margin: 0 0 8px 0;
  color: #333;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #555;
}

textarea, input {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  font-size: 13px;
}

textarea {
  resize: vertical;
  min-height: 80px;
}

button {
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.status {
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
  display: none;
}

.status.success {
  display: block;
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status.error {
  display: block;
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
```

**Styling**: Functional, not fancy. Standard form elements.

---

## config.js

```javascript
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000',
  API_ENDPOINTS: {
    capture: '/v1/capture',
    search: '/v1/retrieve/semantic'
  }
};
```

**Centralized config** - easy to change API endpoint.

---

## popup.js

```javascript
// DOM elements
const contentTextarea = document.getElementById('content');
const queryInput = document.getElementById('query');
const saveBtn = document.getElementById('save-btn');
const searchBtn = document.getElementById('search-btn');
const statusDiv = document.getElementById('status');

// Show status message
function showStatus(message, type = 'success') {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  setTimeout(() => {
    statusDiv.className = 'status';
  }, 3000);
}

// Save content
saveBtn.addEventListener('click', async () => {
  const content = contentTextarea.value.trim();

  if (!content) {
    showStatus('Please enter some content to save', 'error');
    return;
  }

  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving...';

  try {
    // Get current tab info for metadata
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.capture}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: content,
        source: 'browser_extension',
        metadata: {
          url: tab.url,
          title: tab.title
        }
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    showStatus(`Saved! ID: ${data.capture_id.slice(0, 8)}...`, 'success');
    contentTextarea.value = '';  // Clear after save

  } catch (error) {
    console.error('Save error:', error);
    showStatus(`Error: ${error.message}`, 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save';
  }
});

// Search and retrieve context
searchBtn.addEventListener('click', async () => {
  const query = queryInput.value.trim();

  if (!query) {
    showStatus('Please enter a search query', 'error');
    return;
  }

  searchBtn.disabled = true;
  searchBtn.textContent = 'Searching...';

  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.search}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query,
        limit: 5
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.results.length === 0) {
      showStatus('No relevant context found', 'error');
      return;
    }

    // Format results for clipboard
    const formattedResults = data.results.map((r, i) =>
      `[${i + 1}] (similarity: ${r.similarity_score.toFixed(2)})\n${r.content}\n`
    ).join('\n---\n\n');

    const contextText = `Context for: "${query}"\n\n${formattedResults}`;

    // Copy to clipboard
    await navigator.clipboard.writeText(contextText);

    showStatus(`Copied ${data.results.length} items to clipboard!`, 'success');

  } catch (error) {
    console.error('Search error:', error);
    showStatus(`Error: ${error.message}`, 'error');
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = 'Get Context';
  }
});

// Auto-populate content from clipboard on load (optional)
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const clipboardText = await navigator.clipboard.readText();
    if (clipboardText && clipboardText.length < 1000) {
      contentTextarea.value = clipboardText;
      contentTextarea.select();
    }
  } catch (error) {
    // Clipboard read failed - ignore
  }
});
```

**Functionality**:
1. **Save**: POST content + current tab metadata → Show success/error
2. **Search**: POST query → Format results → Copy to clipboard
3. **Auto-populate** (optional): Pre-fill textarea from clipboard

---

## User Flow

### Capture Flow

1. User clicks extension icon
2. Popup opens with textarea
3. User pastes/types content (or auto-populated from clipboard)
4. User clicks "Save"
5. Extension POSTs to API
6. Success message shows with capture_id
7. Textarea clears

**Total time**: 5 seconds

### Retrieval Flow

1. User is in ChatGPT/Claude/etc.
2. User wants relevant context
3. User clicks extension icon
4. User types query in search box
5. User clicks "Get Context"
6. Extension searches via API
7. Results copied to clipboard
8. User pastes into LLM chat

**Total time**: 10 seconds

---

## Development Setup

### Load Unpacked Extension

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `browser-extension/` directory
5. Extension appears in toolbar

### Testing

1. Start API server: `make api`
2. Click extension icon
3. Save some test content
4. Try searching for it
5. Verify clipboard copy works

### Debugging

- Right-click extension icon → "Inspect popup"
- Check console for errors
- Verify API calls in Network tab

---

## Known Limitations (V1)

1. **No offline support** - requires API running
2. **No content preview** - search results only show in clipboard
3. **No pagination** - shows top 5 results only
4. **No error retry** - single API call, fails if network issue
5. **No settings UI** - API URL hardcoded in `config.js`

**All acceptable for v1.** Fix in v2 if users complain.

---

## Future Enhancements (V2)

See `docs/v2-vision/browser-plugin-full.md` for:
- Command palette with `⌘⇧Space`
- Ghost button for clipboard capture
- Inline context injection (no copy/paste)
- Settings page for API configuration
- Recent items list in popup
- Content preview before save
- Keyboard shortcuts

**V1 goal**: Prove the core loop works. Polish later.

---

## Testing Checklist

- [ ] Extension loads without errors
- [ ] Save button captures content
- [ ] API receives correct JSON payload
- [ ] Success message shows after save
- [ ] Search returns relevant results
- [ ] Results copied to clipboard correctly
- [ ] Error messages display on failure
- [ ] Works with current tab metadata (URL, title)
- [ ] Textarea clears after successful save
- [ ] Clipboard auto-populate works (optional)

---

## Distribution (V1: Manual Only)

**V1**: Share as unpacked extension (developer mode).

**V2**: Publish to Chrome Web Store.

---

## Estimated Build Time

- Manifest + HTML/CSS: 30 minutes
- JavaScript logic: 1-2 hours
- Icons (use placeholder): 10 minutes
- Manual testing: 30 minutes

**Total**: ~3 hours for working v1 extension.

---

## Success Criteria

Extension is "done" when:
1. You can save content from any webpage
2. You can search and retrieve context
3. Results are useful enough to paste into LLM chats
4. No critical bugs in happy path

**Not required**: Beautiful design, perfect error handling, edge case coverage.
