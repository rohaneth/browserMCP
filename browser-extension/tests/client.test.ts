import { flushBufferToAPI } from "../src/api/client";
import { getBufferedEvents, removeEventsFromBuffer } from "../src/storage/buffer";
import { BrowserEvent } from "../src/events/builder";

jest.mock("../src/storage/buffer");

const mockGetBufferedEvents = getBufferedEvents as jest.Mock;
const mockRemoveEventsFromBuffer = removeEventsFromBuffer as jest.Mock;

describe("API Client", () => {
    const mockEvent: BrowserEvent = {
        event_id: "123",
        timestamp: "2026-08-18T10:00:00Z",
        event_type: "click",
        source: "browser_extension",
        schema_version: 1
    };

    beforeEach(() => {
        jest.clearAllMocks();
        global.fetch = jest.fn();
    });

    test("flushes events successfully and clears buffer", async () => {
        mockGetBufferedEvents.mockResolvedValue([mockEvent]);
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: true,
            status: 200
        });

        await flushBufferToAPI();

        expect(global.fetch).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify({ events: [mockEvent] })
            })
        );
        expect(mockRemoveEventsFromBuffer).toHaveBeenCalledWith(["123"]);
    });

    test("leaves events in buffer on network failure", async () => {
        mockGetBufferedEvents.mockResolvedValue([mockEvent]);
        (global.fetch as jest.Mock).mockRejectedValue(new Error("Network Error"));

        await flushBufferToAPI();

        expect(global.fetch).toHaveBeenCalled();
        expect(mockRemoveEventsFromBuffer).not.toHaveBeenCalled();
    });

    test("leaves events in buffer on 5xx server error", async () => {
        mockGetBufferedEvents.mockResolvedValue([mockEvent]);
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 500
        });

        await flushBufferToAPI();

        expect(global.fetch).toHaveBeenCalled();
        expect(mockRemoveEventsFromBuffer).not.toHaveBeenCalled();
    });

    test("removes events from buffer on unrecoverable 400/409/422 error", async () => {
        mockGetBufferedEvents.mockResolvedValue([mockEvent]);
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 422
        });

        await flushBufferToAPI();

        expect(global.fetch).toHaveBeenCalled();
        expect(mockRemoveEventsFromBuffer).toHaveBeenCalledWith(["123"]);
    });

    test("leaves events in buffer on 401/403 auth errors", async () => {
        mockGetBufferedEvents.mockResolvedValue([mockEvent]);
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: false,
            status: 401
        });

        await flushBufferToAPI();

        expect(global.fetch).toHaveBeenCalled();
        expect(mockRemoveEventsFromBuffer).not.toHaveBeenCalled();
    });
});
