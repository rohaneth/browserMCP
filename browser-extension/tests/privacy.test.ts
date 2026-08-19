/**
 * @jest-environment jsdom
 */
import { isSensitiveField } from "../src/utils/privacy";

describe("Privacy Filtering", () => {
    test("detects password inputs", () => {
        const input = document.createElement("input");
        input.type = "password";
        expect(isSensitiveField(input)).toBe(true);
    });

    test("detects hidden inputs", () => {
        const input = document.createElement("input");
        input.type = "hidden";
        expect(isSensitiveField(input)).toBe(true);
    });

    test("detects credit card autocomplete", () => {
        const input = document.createElement("input");
        input.type = "text";
        input.autocomplete = "cc-number";
        expect(isSensitiveField(input)).toBe(true);
    });

    test("allows standard text inputs", () => {
        const input = document.createElement("input");
        input.type = "text";
        input.name = "search_query";
        expect(isSensitiveField(input)).toBe(false);
    });
});
