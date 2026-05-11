# Data Contract

## Inputs

### Payload sent to server, this data is validated
```typescript
  
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

```

### Payload expected by server (Using Pydantic)
```python
   
class Category(BaseModel):
    items: list[str]
    weight: float

class InputFormatted(BaseModel):
    movies: Category
    actors: Category
    directors: Category
    genres: Category
```

## Outputs

### Payload sent by server
```python

@dataclass
class Payload:
    input_movies: list[HydratedMovie]
    recommended_movies: list[HydratedMovie]
  

@dataclass
class HydratedMovie:
    id: int
    score: float
    title: str
    genres: list[str]
    cast: list[str]
    release_date: str
    directors: list[str]
    poster_url: str
```

### Payload received by client (Validated using Zod)
```typescript
  
const HydratedMovie = z.object({
    id: z.number(),
    score: z.number(),
    title: z.string(),
    genres: z.array(z.string()),
    cast: z.array(z.string()),
    release_date: z.string(),
    directors: z.array(z.string()),
    poster_url: z.string().nullable(),
});

export const ServerPayload = z.object({
    input_movies: z.array(HydratedMovie),
    recommended_movies: z.array(HydratedMovie),
});
```

## Notes
On the inputs, any of the fields can be empty, but not all.

On the outputs, ...TODO...

