import { BrowserEvent } from "../events/builder";
import { getBufferedEvents, removeEventsFromBuffer } from "../storage/buffer";
import { config } from "../config";

export async function flushBufferToAPI(): Promise<void> {
    const events = await getBufferedEvents();
    if (events.length === 0) {
        return;
    }

    try {
        const response = await fetch(config.API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ events })
        });

        const processedIds = events.map(e => e.event_id);

        if (response.ok) {
            // 2xx Success: server acknowledged and processed
            // NOTE: The batch endpoint is an atomic transaction. A 2xx means ALL non-duplicate 
            // events in this payload were successfully persisted to the database.
            await removeEventsFromBuffer(processedIds);
            console.log(`Successfully flushed ${processedIds.length} events to API.`);
        } else if (response.status === 400 || response.status === 409 || response.status === 422) {
            // 400, 422: Permanent malformed payload. Cannot be fixed by retrying.
            // 409: Idempotency conflict (events already exist).
            await removeEventsFromBuffer(processedIds);
            console.warn(`Dropped ${processedIds.length} events due to unrecoverable ${response.status} error.`);
        } else if (response.status === 401 || response.status === 403) {
            // 401/403: Auth errors. Do NOT silently delete valuable buffered events.
            // Authentication may be introduced later, so we preserve the history.
            console.warn(`Authentication required (${response.status}). Preserving events in buffer.`);
        } else {
            // 5xx Server Error, 429 Rate Limit, or other unknown 4xx
            // Transient failures, leave in buffer for next retry.
            console.warn(`Failed to flush events to API. Transient status: ${response.status}`);
        }
    } catch (error) {
        // Network error. Do nothing and leave events in the buffer for the next retry.
        console.error("Network error while flushing buffer:", error);
    }
}
