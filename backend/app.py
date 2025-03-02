from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import couchdb
import shutil
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

db_name = 'posts'
couch = couchdb.Server('http://admin:admin@127.0.0.1:5984/')

if db_name in couch:
    db = couch[db_name]
else:
    db = couch.create(db_name)

media_folder = 'UserMedia'
os.makedirs(media_folder, exist_ok=True)

# ✅ Define a Pydantic Model (Does Not Support `Form` Directly)
class PostModel(BaseModel):
    username: str
    postID: str
    caption: str
    mediaType: str
    hashtags: str
    location: str
    tagged_users: str
    system_date_time: str
    isSponsered: str
    platform_Name: str

# ✅ Pydantic Model for Update (Only allows optional fields)
class UpdatePostModel(BaseModel):
    caption: Optional[str] = None
    mediaType: Optional[str] = None
    hashtags: Optional[str] = None
    location: Optional[str] = None
    tagged_users: Optional[str] = None
    system_date_time: Optional[str] = None
    isSponsered: Optional[str] = None
    platform_Name: Optional[str] = None

# ✅ Extract Form Data Using `Depends()`
def parse_form_data(
    username: str = Form(...),
    postID: str = Form(...),
    caption: str = Form(...),
    mediaType: str = Form(...),
    hashtags: str = Form(...),
    location: str = Form(...),
    tagged_users: str = Form(...),
    system_date_time: str = Form(...),
    isSponsered: str = Form(...),
    platform_Name: str = Form(...)
):
    return PostModel(
        username=username,
        postID=postID,
        caption=caption,
        mediaType=mediaType,
        hashtags=hashtags,
        location=location,
        tagged_users=tagged_users,
        system_date_time=system_date_time,
        isSponsered=isSponsered,
        platform_Name=platform_Name,
    )

# ✅ Create Post Route Using Pydantic and Form Data
@app.post("/posts/")
async def create_post(
    post: PostModel = Depends(parse_form_data),
    mediaFile: Optional[UploadFile] = File(None)
):
    new_media_path = ""
    if mediaFile:
        media_extension = os.path.splitext(mediaFile.filename)[-1]
        new_media_filename = f"{post.username}.{post.postID}{media_extension}"
        new_media_path = os.path.join(media_folder, new_media_filename)
        with open(new_media_path, "wb") as buffer:
            shutil.copyfileobj(mediaFile.file, buffer)

    post_doc = post.dict()
    post_doc["_id"] = post.postID  # Ensure unique document ID
    post_doc["mediaURL"] = new_media_path

    db.save(post_doc)
    return {"message": f"Post {post.postID} by {post.username} added successfully!"}

# ✅ Fetch All Posts
@app.get("/posts/")
def read_posts():
    posts = [db[doc_id] for doc_id in db]
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found.")
    return posts

# ✅ Update a Post
@app.put("/posts/{postID}")
def update_post(postID: str, post_update: UpdatePostModel):
    if postID not in db:
        raise HTTPException(status_code=404, detail="Post not found in CouchDB.")

    doc = db[postID]
    update_data = post_update.dict(exclude_unset=True)  # Exclude None values
    doc.update(update_data)

    db.save(doc)
    return {"message": f"Post {postID} updated successfully!"}

# ✅ Delete a Post
@app.delete("/posts/{postID}")
def delete_post(postID: str):
    if postID not in db:
        raise HTTPException(status_code=404, detail="Post not found in CouchDB.")

    doc = db[postID]
    if 'mediaURL' in doc and os.path.exists(doc['mediaURL']):
        os.remove(doc['mediaURL'])

    db.delete(doc)
    return {"message": f"Post {postID} deleted successfully!"}