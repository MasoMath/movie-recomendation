export function normalize(s: string): string {
    return s.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, "").trim();
}
