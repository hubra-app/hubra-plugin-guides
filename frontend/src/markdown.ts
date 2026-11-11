/**
 * A guide's Markdown with its images turned into links.
 *
 * Guides have no uploads, so an image in a guide is always on another site,
 * and loading it would tell that site who reads the guide and when (their
 * IP address, browser and the time). The reader opens it with a click
 * instead. Fenced code stays as written.
 */
export function linkImages(markdown: string, label: string): string {
  let fence: string | null = null
  return markdown
    .split('\n')
    .map((line) => {
      const f = line.match(/^\s{0,3}(```|~~~)/)
      if (f) {
        fence = fence === null ? f[1] : fence === f[1] ? null : fence
        return line
      }
      if (fence) return line
      // ![alt](url) and ![alt][ref] become [alt](url) and [alt][ref];
      // an image without alt text gets the label.
      return line.replace(/!\[([^\]]*)\](?=\s*[([])/g, (_, alt: string) => `[${alt.trim() || label}]`)
    })
    .join('\n')
}
