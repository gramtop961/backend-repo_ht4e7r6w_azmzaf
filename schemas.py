from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# The schema viewer can discover these models. Each model name maps to a
# lowercased collection name in MongoDB, e.g. Film -> "film".

class Setting(BaseModel):
    logo_url: Optional[str] = Field(None, description="Public logo URL")
    categories: Optional[List[str]] = Field(default_factory=lambda: [
        "About", "News", "Exclusives", "Production", "Partner", "Animal Streaming"
    ])
    theme: str = Field(default="orange-black", description="Theme identifier")

class About(BaseModel):
    history: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    team: Optional[List[Dict[str, Any]]] = None

class News(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    date: Optional[str] = None
    featured: bool = False
    order: Optional[int] = None

class Film(BaseModel):
    title: str
    poster_url: Optional[str] = None
    length_min: Optional[int] = None
    release_date: Optional[str] = None
    fsk: Optional[str] = None
    description: Optional[str] = None
    trailer_url: Optional[str] = None
    cast: Optional[List[str]] = None
    crew: Optional[List[str]] = None
    exclusive: bool = False
    stream_url: Optional[str] = None

class Production(BaseModel):
    phase: str
    text: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    order: Optional[int] = None

class Partner(BaseModel):
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

class Application(BaseModel):
    name: str
    email: str
    role: str
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
