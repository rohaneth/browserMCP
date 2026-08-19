import { createBrowserEvent } from "../events/builder";
import { bufferEvent } from "../storage/buffer";
import { flushBufferToAPI } from "../api/client";

// Set up periodic alarm to flush buffer every minute
chrome.alarms.create("flushBuffer", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "flushBuffer") {
        flushBufferToAPI();
    }
});

// Listen for page loads
chrome.webNavigation.onCompleted.addListener(async (details) => {
    // Only capture top-level frame navigation
    if (details.frameId === 0) {
        
        // We can optionally fetch the page title by injecting a script, 
        // but for safety/speed we will just capture the URL immediately.
        // We will try to get the title via chrome.tabs if available.
        let title = "";
        try {
            const tab = await chrome.tabs.get(details.tabId);
            title = tab.title || "";
        } catch (e) {
            // Tab might be closed or unavailable
        }

        const event = createBrowserEvent({
            event_type: "page_loaded",
            url: details.url,
            page_title: title
        });
        
        await bufferEvent(event);
    }
});

// Listen for messages from content scripts (clicks, searches)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "BUFFER_EVENT") {
        bufferEvent(message.event).then(() => {
            sendResponse({ success: true });
        }).catch(err => {
            console.error("Failed to buffer event:", err);
            sendResponse({ success: false });
        });
        return true; // Indicates async response
    }
});
