import { BrowserEvent } from "../events/builder";

const STORAGE_KEY = "event_buffer";

/**
 * Appends a new event to the Chrome local storage buffer safely.
 */
export async function bufferEvent(event: BrowserEvent): Promise<void> {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            
            const buffer: BrowserEvent[] = result[STORAGE_KEY] || [];
            buffer.push(event);
            
            chrome.storage.local.set({ [STORAGE_KEY]: buffer }, () => {
                if (chrome.runtime.lastError) {
                    return reject(chrome.runtime.lastError);
                }
                resolve();
            });
        });
    });
}

/**
 * Retrieves all events currently in the buffer.
 */
export async function getBufferedEvents(): Promise<BrowserEvent[]> {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            resolve(result[STORAGE_KEY] || []);
        });
    });
}

/**
 * Removes specific events from the buffer by their event_id.
 * Safe against concurrent appends because it filters existing storage.
 */
export async function removeEventsFromBuffer(eventIds: string[]): Promise<void> {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            
            const buffer: BrowserEvent[] = result[STORAGE_KEY] || [];
            const idSet = new Set(eventIds);
            
            // Keep only events that were NOT in the provided eventIds
            const newBuffer = buffer.filter(ev => !idSet.has(ev.event_id));
            
            chrome.storage.local.set({ [STORAGE_KEY]: newBuffer }, () => {
                if (chrome.runtime.lastError) {
                    return reject(chrome.runtime.lastError);
                }
                resolve();
            });
        });
    });
}
