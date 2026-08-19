// Mock chrome API globally
global.chrome = {
    runtime: {},
    storage: {
        local: {
            get: jest.fn(),
            set: jest.fn()
        }
    }
} as any;

import { bufferEvent, getBufferedEvents, removeEventsFromBuffer } from "../src/storage/buffer";
import { BrowserEvent } from "../src/events/builder";

describe("Buffer Storage", () => {
    const mockEvent: BrowserEvent = {
        event_id: "123",
        timestamp: "2026-08-18T10:00:00Z",
        event_type: "click",
        source: "browser_extension",
        schema_version: 1
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("buffers an event successfully", async () => {
        (chrome.storage.local.get as jest.Mock).mockImplementation((keys, cb) => cb({}));
        (chrome.storage.local.set as jest.Mock).mockImplementation((obj, cb) => cb());

        await bufferEvent(mockEvent);

        expect(chrome.storage.local.set).toHaveBeenCalledWith(
            { event_buffer: [mockEvent] },
            expect.any(Function)
        );
    });

    test("removes specific events from buffer", async () => {
        const mockEvent2: BrowserEvent = { ...mockEvent, event_id: "456" };
        (chrome.storage.local.get as jest.Mock).mockImplementation((keys, cb) => cb({
            event_buffer: [mockEvent, mockEvent2]
        }));
        (chrome.storage.local.set as jest.Mock).mockImplementation((obj, cb) => cb());

        await removeEventsFromBuffer(["123"]);

        expect(chrome.storage.local.set).toHaveBeenCalledWith(
            { event_buffer: [mockEvent2] },
            expect.any(Function)
        );
    });
});
