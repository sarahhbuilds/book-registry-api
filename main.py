# 1. IMPORT ALAT ALAT YANG AKAN DIGUNAKAN
import os #impor os lu
from fastapi import FastAPI, Depends, HTTPException, status 
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session


# 2. SESI KONFIGURASI DATABASE
"""
1. dari cari folder db postgres dari os
2. bikin class isi kode rahasia
3. bikin kelas tabel isi kode rahasia yg diwariskan dari kelas base
4. bikin fungsi pemanggilan buka tutup sesi pake getdb
5. eksekusi pembuatan tabel pake Base.metadata blabla dengan koneksi mesin nya engine
"""
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/db_buku") #cari tempat file postgres dari os kita

engine = create_engine(DATABASE_URL) #bikin mesin koneksi ke db url 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #bikin sesi transaksi db dan app

class Base(DeclarativeBase): 
    pass

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. MODEL DATABASE (SQLAlchemy) ---
class Item(Base): #ini model db dan kolom kolom yang bakal ada di db
    __tablename__ = "items" #BIKIN TABLE DI DB NAMANYA ITEMS    
# bikin kolom dalam tabel items ada 3, namanya id, title, description
    id = Column(Integer, primary_key=True) #kolom id, tipe int, primary key itu kunci utama untuk biki clustered index dari nomor 1
    title = Column(String, index=True) 
    description = Column(String)  # Tetap 'description', potensial data panjang jadi ga pake index, karna bisa aja paragraf, kalo title kan paling cuma 1 kalimat

Base.metadata.create_all(bind=engine) 


# --- SCHEMA VALIDASI (Pydantic) --- 
# DATA YANG MASUK DAN KELUAR API HARUS SEPERTI INI, ykwim
class ItemCreate(BaseModel):
    title: str
    description: str  # FIX: Hapus huruf 'e' di belakang

class ItemResponse(BaseModel):
    id: int           # FIX: Ubah jadi int biar sinkron sama database
    title: str
    description: str  # FIX: Hapus huruf 'e' di belakang
    
    model_config = ConfigDict(from_attributes=True) 

# BIKIN APLIKASI 
app = FastAPI()

# --- RUTE DAN ENDPOINT YANG MASUK KELUAR API
@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # .model_dump() sekarang aman karena key-nya udah match sama kolom DB
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    # FIX: Upgrade ke gaya SQLAlchemy 2.0 menggunakan select()
    statement = select(Item).where(Item.id == item_id)
    db_item = db.scalars(statement).first()
    
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

