from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import couchdb
import shutil
from typing import Optional

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


@app.post("/posts/")
async def create_post(
        username: str = Form(...),
        postID: str = Form(...),
        caption: str = Form(...),
        mediaType: str = Form(...),
        hashtags: str = Form(...),
        location: str = Form(...),
        tagged_users: str = Form(...),
        system_date_time: str = Form(...),
        isSponsered: str = Form(...),
        platform_Name: str = Form(...),
        mediaFile: Optional[UploadFile] = File(None)
):
    new_media_path = ""
    if mediaFile:
        media_extension = os.path.splitext(mediaFile.filename)[-1]
        new_media_filename = f"{username}.{postID}{media_extension}"
        new_media_path = os.path.join(media_folder, new_media_filename)
        with open(new_media_path, "wb") as buffer:
            shutil.copyfileobj(mediaFile.file, buffer)

    post_doc = {
        '_id': postID,  # Ensure unique document ID
        'username': username,
        'postID': postID,
        'caption': caption,
        'mediaURL': new_media_path,
        'mediaType': mediaType,
        'hashtags': hashtags,
        'location': location,
        'tagged_users': tagged_users,
        'SystemDateandTime': system_date_time,
        'isSponsered': isSponsered,
        'platform_Name': platform_Name
    }

    db.save(post_doc)
    return {"message": f"Post {postID} by {username} added successfully!"}


@app.get("/posts/")
def read_posts():
    posts = [db[doc_id] for doc_id in db]
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found.")
    return posts


@app.put("/posts/{postID}")
def update_post(
        postID: str,
        caption: Optional[str] = Form(None),
        mediaType: Optional[str] = Form(None),
        hashtags: Optional[str] = Form(None),
        location: Optional[str] = Form(None),
        tagged_users: Optional[str] = Form(None),
        system_date_time: Optional[str] = Form(None),
        isSponsered: Optional[str] = Form(None),
        platform_Name: Optional[str] = Form(None)
):
    if postID not in db:
        raise HTTPException(status_code=404, detail="Post not found in CouchDB.")

    doc = db[postID]
    doc.update({
        'caption': caption or doc.get('caption', ''),
        'mediaType': mediaType or doc.get('mediaType', ''),
        'hashtags': hashtags or doc.get('hashtags', ''),
        'location': location or doc.get('location', ''),
        'tagged_users': tagged_users or doc.get('tagged_users', ''),
        'SystemDateandTime': system_date_time or doc.get('SystemDateandTime', ''),
        'isSponsered': isSponsered or doc.get('isSponsered', ''),
        'platform_Name': platform_Name or doc.get('platform_Name', '')
    })
    db.save(doc)
    return {"message": f"Post {postID} updated successfully!"}


@app.delete("/posts/{postID}")
def delete_post(postID: str):
    if postID not in db:
        raise HTTPException(status_code=404, detail="Post not found in CouchDB.")

    doc = db[postID]
    if 'mediaURL' in doc and os.path.exists(doc['mediaURL']):
        os.remove(doc['mediaURL'])

    db.delete(doc)
    return {"message": f"Post {postID} deleted successfully!"}
