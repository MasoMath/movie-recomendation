import * as z from 'zod';

const hydratedMovieSchema = z.object({
    id: z.number(),
    score: z.number(),
    title: z.string(),
    genres: z.array(z.string()),
    cast: z.array(z.string()),
    release_date: z.string(),
    directors: z.array(z.string()),
    production_companies: z.array(z.string()),
    poster_url: z.string().nullable(),
});

export type HydratedMovie = z.infer<typeof hydratedMovieSchema>;

export const ServerPayload = z.object({
    input_movies: z.array(hydratedMovieSchema),
    recommended_movies: z.array(hydratedMovieSchema),
});

export function normalize(s: string): string {
    return s.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, "").trim();
}
