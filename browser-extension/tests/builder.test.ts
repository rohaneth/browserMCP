import { createBrowserEvent, generateUUID, extractDomain } from "../src/events/builder";
import * as crypto from "crypto";

// Mock global crypto for node environment UUID generation
Object.defineProperty(globalThis, 'crypto', {
  value: {
    randomUUID: () => crypto.randomUUID()
  }
});

describe("BrowserEvent Builder", () => {
    test("generates UUID", () => {
        const id = generateUUID();
        expect(id).toBeDefined();
        expect(id.length).toBe(36); // standard uuid length
    });

    test("extracts domain correctly", () => {
        expect(extractDomain("https://www.example.com/path?q=1")).toBe("www.example.com");
        expect(extractDomain("invalid-url")).toBeUndefined();
    });

    test("creates page_loaded event correctly", () => {
        const ev = createBrowserEvent({
            event_type: "page_loaded",
            url: "https://example.com/test",
            page_title: "Test Page"
        });

        expect(ev.event_id).toBeDefined();
        expect(ev.timestamp).toBeDefined();
        expect(ev.event_type).toBe("page_loaded");
        expect(ev.url).toBe("https://example.com/test");
        expect(ev.domain).toBe("example.com");
        expect(ev.page_title).toBe("Test Page");
        expect(ev.source).toBe("browser_extension");
        expect(ev.schema_version).toBe(1);
    });
});
