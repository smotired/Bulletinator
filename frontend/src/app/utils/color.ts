/**
 * Converts a string to a color.
 * @param string The string to convert.
 * @returns A hex color string created from the string.
 */
export function colorFromString(string: string): string {
    /* eslint-disable no-bitwise */
    let hash = 0, i = 0;
    for (i = 0; i < string.length; i++)
        hash = string.charCodeAt(i) + ((hash << 5) - hash);
    let color = '#';
    for (i = 0; i < 3; i += 1) {
        const value = (hash >> (i * 8)) & 0xff;
        color += `00${value.toString(16)}`.slice(-2);
    }
    /* eslint-enable no-bitwise */
    return color;
}