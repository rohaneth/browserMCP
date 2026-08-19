export type EventType = "page_loaded" | "click" | "search_submitted" | "input_submitted" | "form_submitted" | "page_content";

export interface BrowserEvent {
    event_id: string;
    timestamp: string;
    event_type: EventType;
    url?: string;
    domain?: string;
    page_title?: string;
    content?: string;
    input_text?: string;
    metadata?: Record<string, any>;
    source: string;
    schema_version: number;
}

export function generateUUID(): string {
    return crypto.randomUUID();
}

export function extractDomain(url: string): string | undefined {
    try {
        const parsed = new URL(url);
        return parsed.hostname;
    } catch {
        return undefined;
    }
}

export function createBrowserEvent(params: {
    event_type: EventType;
    url?: string;
    page_title?: string;
    content?: string;
    input_text?: string;
    metadata?: Record<string, any>;
}): BrowserEvent {
    return {
        event_id: generateUUID(),
        timestamp: new Date().toISOString(),
        event_type: params.event_type,
        url: params.url,
        domain: params.url ? extractDomain(params.url) : undefined,
        page_title: params.page_title,
        content: params.content,
        input_text: params.input_text,
        metadata: params.metadata || {},
        source: "browser_extension",
        schema_version: 1
    };
}
