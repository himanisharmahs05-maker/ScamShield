from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.core.database import engine, Base
from app.core.models import User, ScanHistory
from app.core.trust_manager import trust_manager
from app.ml.model import phishing_ml_model

# --- LIFECYCLE MANAGEMENT ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("[INFO] Connected to database and verified tables successfully!")
        
        # Seed default test user if users table is empty
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy.future import select
            from app.core.security import get_password_hash
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(User).limit(1))
                if not res.scalar_one_or_none():
                    demo_user = User(
                        email="test@scamshield.com",
                        hashed_password=get_password_hash("password123"),
                        full_name="ScamShield User",
                        is_admin=False
                    )
                    session.add(demo_user)
                    await session.commit()
                    print("[INFO] Seeded default user: test@scamshield.com (password: password123)")
        except Exception as seed_err:
            print(f"[WARNING] User check skipped: {seed_err}")
    except Exception as e:
        print(f"[WARNING] Database initialization note: {e}")

    # 2. Load top domains list into memory cache
    try:
        trust_manager.load_cache()
        phishing_ml_model.load()
        print("[INFO] Trust manager data loaded successfully!")
    except Exception as e:
        print(f"[WARNING] Failed to load trust manager data: {e}")

    yield  # FastAPI running state occurs here

    # ------------------ SHUTDOWN EVENTS ------------------
    await engine.dispose()
    print("[INFO] Disconnected from PostgreSQL safely.")


# --- FASTAPI APP DEFINITION ---
app = FastAPI(title="ScamShield API", version="1.0", lifespan=lifespan)

# --- CORS SETTINGS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUDE ROUTES ---
app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")


@app.get("/")
def read_root():
    return {
        "message": "ScamShield Backend is Running (PostgreSQL & Enterprise Trust Feed enabled)"
    }
