# Browser Intelligence Agent Extension

This extension securely captures browser activity for intelligence processing.

## Permissions Documentation

Every permission requested in `manifest.json` serves a specific architectural requirement:

1. **`storage`**
   - **Why it is needed**: Enables resilient, asynchronous operation by buffering captured events locally. If the backend is unavailable or a network failure occurs, data is preserved across service worker restarts.
   - **Where it is used**: `src/storage/buffer.ts` (`chrome.storage.local`).
   - **Can it be removed?**: No, removing it would cause event loss during backend unavailability.

2. **`webNavigation`**
   - **Why it is needed**: Enables reliable, passive detection of top-level frame navigation to generate accurate `page_loaded` events.
   - **Where it is used**: `src/background/service_worker.ts` (`chrome.webNavigation.onCompleted`).
   - **Can it be removed?**: No, it is the primary hook for tracing the user's navigational timeline.

3. **`<all_urls>` (Host Permissions)**
   - **Why it is needed**: The extension acts as a global intelligence agent. Content scripts must attach to all websites to monitor global clicks and searches passively. Without this, the extension would be blind to user activity on non-whitelisted domains.
   - **Where it is used**: `manifest.json` (content script injection matches, host_permissions).
   - **Can it be removed?**: No, removing it breaks the fundamental intelligence-gathering capability of the project.

## Privacy

The extension implements aggressive filtering (see `src/utils/privacy.ts`) to ensure passwords, credit cards, and sensitive inputs are never evaluated or captured. Arbitrary keystrokes are completely ignored in favor of intercepting actual form submission intents.
