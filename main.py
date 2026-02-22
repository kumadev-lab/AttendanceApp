from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import FileResponse

app = FastAPI()

# UI（HTML）から通信を許可するための設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttendanceRequest(BaseModel):
    user_id: str
    user_pass: str

# display html
@app.get('/')
async def read_index():
    return FileResponse('./static/index.html')

@app.post('/api/CheckIn')
async def checkin(req: AttendanceRequest):
    now = datetime.now()
    return {
        "status": 'CheckIn',
        "time": now.strftime('%Y-%m-%d %H:%M:%S'),
        "username": req.user_id
    }
