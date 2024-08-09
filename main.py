import time
from fastapi import FastAPI, Request
from fastapi.responses  import JSONResponse
from starlette.middleware.cors import CORSMiddleware  # CORSを回避するために必要
# from api.models import Assignment
from routers import auth, directory,company,file,favorite,assignment,permission,user,department,region,industry
from fastapi.security import HTTPBearer
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from schemas.auth import CsrfSettings

app = FastAPI()
origins= ['http://localhost:3000']

# CORSを回避するために設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@CsrfProtect.load_config
def get_csrf_config():
  return CsrfSettings()

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
  return JSONResponse(
     status_code=exc.status_code, 
     content={"detail": exc.message}
     )

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(directory.router)
app.include_router(file.router)
app.include_router(company.router)
app.include_router(favorite.router)
# app.include_router(assignment.router)
app.include_router(department.router)
# app.include_router(permission.router)
app.include_router(region.router)
app.include_router(industry.router)



