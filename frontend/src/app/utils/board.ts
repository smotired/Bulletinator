const whitespaceRegex = RegExp('[ -]+', 'g');
const disallowedRegex = RegExp('[^\\w]', 'g');
const underscoreConvergeRegex = RegExp('__+', 'g');

/**
 * Converts a name to a default identifier.
 * @param name Name of the board
 * @returns The name converted to an identifier.
 */
export function convertToIdentifier(name: string): string {
    return name.replaceAll(whitespaceRegex, '_')
        .replaceAll(disallowedRegex, '')
        .replaceAll(underscoreConvergeRegex, '_')
}