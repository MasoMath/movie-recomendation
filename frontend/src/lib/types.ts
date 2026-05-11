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

export interface SearchPayload {
    movies: SearchCategory;
    actors: SearchCategory;
    directors: SearchCategory;
    genres: SearchCategory;
}


