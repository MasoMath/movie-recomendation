import * as d3 from 'd3';

export interface GraphNode extends d3.SimulationNodeDatum {
    id: string | number;
    title: string;
    score?: number;
    isCenter: boolean;
    directors?: string[];
    cast?: string[];
    release_date?: string;
    genres?: string[];
    production_companies?: string[];
    poster_url?: string;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
    source: string | GraphNode;
    target: number | string | GraphNode;
    score: number;
}

export interface SearchCategory {
    items: string[];
    weight: number;
}

export interface ApiSearchCategory {
    items: number[];
    weight: number;
}

export const SEARCH_CATEGORY_KEYS = [
    'movies',
    'actors',
    'directors',
    'genres',
    'production_companies',
] as const;

export type SearchCategoryKey = (typeof SEARCH_CATEGORY_KEYS)[number];

export const CATEGORY_DISPLAY_LABELS: Record<SearchCategoryKey, string> = {
    movies: 'Movies',
    actors: 'Actors',
    directors: 'Directors',
    genres: 'Genres',
    production_companies: 'Production companies',
};

export interface SearchPayload {
    movies: SearchCategory;
    actors: SearchCategory;
    directors: SearchCategory;
    genres: SearchCategory;
    production_companies: SearchCategory;
}

export interface ApiSearchPayload {
    movies: ApiSearchCategory;
    actors: ApiSearchCategory;
    directors: ApiSearchCategory;
    genres: ApiSearchCategory;
    production_companies: ApiSearchCategory;
}



