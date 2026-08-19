/**
 * Checks if a given input element or form field is sensitive and should be ignored.
 */
export function isSensitiveField(element: HTMLElement): boolean {
    if (element.tagName.toLowerCase() === 'input') {
        const input = element as HTMLInputElement;
        const type = input.type.toLowerCase();
        
        // Block obvious password/auth inputs
        if (type === 'password' || type === 'hidden') {
            return true;
        }

        // Block credit card inputs based on autocomplete
        const autocomplete = input.autocomplete.toLowerCase();
        if (autocomplete.includes('cc-') || autocomplete.includes('password') || autocomplete.includes('new-password')) {
            return true;
        }
        
        // Block based on generic id/name heuristics for sensitive data
        const id = input.id.toLowerCase();
        const name = input.name.toLowerCase();
        if (
            id.includes('password') || name.includes('password') ||
            id.includes('creditcard') || name.includes('cardnumber') ||
            id.includes('ssn') || name.includes('ssn')
        ) {
            return true;
        }
    }
    return false;
}
