import { createBrowserEvent } from "../events/builder";
import { isSensitiveField } from "../utils/privacy";

function extractSearchQueryFromURL(url: string): string | undefined {
    try {
        const parsed = new URL(url);
        const keys = ['q', 'query', 'search', 'search_query', 'keyword', 'term', 'k', 'p'];
        for (const k of keys) {
            const val = parsed.searchParams.get(k);
            if (val && val.trim()) {
                return decodeURIComponent(val.trim().replace(/\+/g, ' '));
            }
        }
    } catch {
        return undefined;
    }
    return undefined;
}

// On page load: check if URL contains search parameters and buffer event
const currentURLSearch = extractSearchQueryFromURL(window.location.href);
if (currentURLSearch) {
    const searchEvent = createBrowserEvent({
        event_type: "search_submitted",
        url: window.location.href,
        page_title: document.title,
        input_text: currentURLSearch.substring(0, 1000)
    });
    chrome.runtime.sendMessage({ type: "BUFFER_EVENT", event: searchEvent });
}

// Passive click listener
document.addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    if (!target) return;

    if (isSensitiveField(target)) return;

    const link = target.closest('a');
    const button = target.closest('button');
    
    if (link || button) {
        const textContent = (link?.textContent || button?.textContent || "").trim().substring(0, 500);
        
        const event = createBrowserEvent({
            event_type: "click",
            url: window.location.href,
            page_title: document.title,
            content: textContent,
            metadata: {
                tag: link ? 'A' : 'BUTTON',
                href: link?.href
            }
        });

        chrome.runtime.sendMessage({ type: "BUFFER_EVENT", event });
    }
}, { capture: true, passive: true });

// Form submission listener (capturing queries & inputs)
document.addEventListener("submit", (e) => {
    const target = e.target as HTMLFormElement;
    if (!target) return;

    let query = "";
    const inputs = target.querySelectorAll('input, textarea');
    
    for (const input of Array.from(inputs)) {
        const inputElem = input as HTMLInputElement;
        if (isSensitiveField(inputElem)) continue;

        const nameAttr = (inputElem.name || "").toLowerCase();
        const idAttr = (inputElem.id || "").toLowerCase();
        const typeAttr = (inputElem.type || "").toLowerCase();

        if (
            typeAttr === 'search' ||
            nameAttr === 'q' || nameAttr.includes('search') || nameAttr.includes('query') ||
            idAttr.includes('search') || idAttr.includes('query')
        ) {
            query = inputElem.value;
            if (query) break;
        }
    }

    if (query) {
        const event = createBrowserEvent({
            event_type: "search_submitted",
            url: window.location.href,
            page_title: document.title,
            input_text: query.substring(0, 1000)
        });

        chrome.runtime.sendMessage({ type: "BUFFER_EVENT", event });
    }
}, { capture: true, passive: true });
