import * as z from 'zod';

const HydratedMovie = z.object({
    id: z.number(),
    score: z.number(),
    title: z.string(),
    genres: z.array(z.string()),
    cast: z.array(z.string()),
    release_date: z.string(),
    directors: z.array(z.string()),
    poster_url: z.string(),
});

export const HydratedMovies = z.array(HydratedMovie);



export function normalize(s: string): string {
    return s.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, "").trim();
}
