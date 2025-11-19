import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Animal Studios API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Auth --------------------
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "Lucien1409@gmail.streaming.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Streaming.Lucien")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "animal-studios-admin-token")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str = "admin"


def require_admin(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if payload.email == ADMIN_EMAIL and payload.password == ADMIN_PASSWORD:
        return LoginResponse(token=ADMIN_TOKEN)
    raise HTTPException(status_code=401, detail="Invalid credentials")


# -------------------- Utils --------------------
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


def to_obj(doc: Dict[str, Any]):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# -------------------- Schemas (lightweight request models) --------------------
class Setting(BaseModel):
    logo_url: Optional[str] = None
    categories: Optional[List[str]] = None
    theme: str = Field(default="orange-black")

class AboutContent(BaseModel):
    history: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    team: Optional[List[Dict[str, Any]]] = None

class NewsItem(BaseModel):
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

class ProductionEntry(BaseModel):
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


# -------------------- Generic helpers --------------------
COLLECTIONS = {
    "setting": Setting,
    "about": AboutContent,
    "news": NewsItem,
    "film": Film,
    "production": ProductionEntry,
    "partner": Partner,
    "application": Application,
}


def get_collection(name: str):
    if name not in COLLECTIONS:
        raise HTTPException(status_code=404, detail="Unknown collection")
    return db[name]


# Public: read/list endpoints
@app.get("/api/{collection}")
def list_documents(collection: str, limit: int = 100):
    get_collection(collection)
    items = get_documents(collection, {}, limit)
    return [to_obj(i) for i in items]


@app.get("/api/{collection}/{doc_id}")
def get_document(collection: str, doc_id: str):
    coll = get_collection(collection)
    doc = coll.find_one({"_id": PyObjectId.validate(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return to_obj(doc)


# Admin: create/update/delete
@app.post("/api/{collection}")
def create(collection: str, payload: Dict[str, Any], _: bool = Depends(require_admin)):
    get_collection(collection)
    new_id = create_document(collection, payload)
    return {"id": new_id}


@app.put("/api/{collection}/{doc_id}")
@app.patch("/api/{collection}/{doc_id}")
def update(collection: str, doc_id: str, payload: Dict[str, Any], _: bool = Depends(require_admin)):
    coll = get_collection(collection)
    oid = PyObjectId.validate(doc_id)
    payload["updated_at"] = datetime.now(timezone.utc)
    res = coll.update_one({"_id": oid}, {"$set": payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    doc = coll.find_one({"_id": oid})
    return to_obj(doc)


@app.delete("/api/{collection}/{doc_id}")
def delete(collection: str, doc_id: str, _: bool = Depends(require_admin)):
    coll = get_collection(collection)
    oid = PyObjectId.validate(doc_id)
    res = coll.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"status": "deleted", "id": doc_id}


# Convenience endpoints
@app.get("/")
def root():
    return {"name": "Animal Studios API", "status": "ok"}


@app.get("/test")
def test_database():
    response: Dict[str, Any] = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
