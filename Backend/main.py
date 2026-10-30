from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os

DB_FILE = "database.db"

# Inisialisasi Database SQLite murni
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Tabel Master Tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mouldingCode TEXT NOT NULL,
            intervalText TEXT NOT NULL,
            lastDone TEXT NOT NULL,
            nextDueDate TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    
    # 2. Tabel Riwayat Pengerjaan (History Logs) - Ditambahkan kolom category, fotoBefore, fotoAfter
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            taskName TEXT NOT NULL,
            mouldingCode TEXT NOT NULL,
            category TEXT,
            operatorName TEXT NOT NULL,
            tanggalPengerjaan TEXT NOT NULL,
            catatan TEXT,
            status TEXT,
            fotoBefore TEXT,
            fotoAfter TEXT
        )
    """)
    conn.commit()
    
    # Seeder Otomatis jika tabel tasks kosong
    cursor.execute("SELECT COUNT(*) FROM maintenance_tasks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        tasks_to_add = []
        
        # 1. Cleaning Core All Mesin (1 - 21)
        for i in range(1, 22):
            num_str = "0" + str(i) if i < 10 else str(i)
            tasks_to_add.append((
                f"Cleaning Core Mesin {num_str}",
                f"MLD-CORE-{num_str}",
                "1 Bulan",
                "2026-09-20",
                "2026-10-18" if i % 3 == 0 else "2026-10-25" if i % 2 == 0 else "2026-11-05",
                "Cleaning Core"
            ))

        # 2. Service Water Heater (1 - 21)
        for i in range(1, 22):
            num_str = "0" + str(i) if i < 10 else str(i)
            tasks_to_add.append((
                f"Service Water Heater Mesin {num_str}",
                f"WH-UTL-{num_str}",
                "3 Bulan",
                "2026-07-15",
                "2026-10-15" if i % 4 == 0 else "2026-11-15",
                "Service Water Heater"
            ))

        # 3. Service Oil Heater (1 - 21)
        for i in range(1, 22):
            num_str = "0" + str(i) if i < 10 else str(i)
            tasks_to_add.append((
                f"Service Oil Heater Mesin {num_str}",
                f"OH-UTL-{num_str}",
                "3 Bulan",
                "2026-07-10",
                "2026-10-10" if i % 5 == 0 else "2026-11-10",
                "Service Oil Heater"
            ))

        # 4. Ganti Flexible Hose (1 - 21)
        for i in range(1, 22):
            num_str = "0" + str(i) if i < 10 else str(i)
            tasks_to_add.append((
                f"Ganti Flexible Hose Mesin {num_str}",
                f"HS-INJ-{num_str}",
                "3 Bulan",
                "2026-08-01",
                "2026-11-01",
                "Ganti Flexible Hose"
            ))

        # 5. Grease Up Injection Unit (1-4 & 16-21)
        injection_machines = [1, 2, 3, 4, 16, 17, 18, 19, 20, 21]
        for m in injection_machines:
            num_str = "0" + str(m) if m < 10 else str(m)
            tasks_to_add.append((
                f"Grease Up Injection Unit Mesin {num_str}",
                f"INJ-MLD-{num_str}",
                "3 Bulan",
                "2026-07-20",
                "2026-10-20" if m <= 4 else "2026-11-20",
                "Grease Up Injection"
            ))

        # 6. Cleaning Pipa Transfer Botol (Jalur 1-6, Atas & Bawah)
        for j in range(1, 7):
            tasks_to_add.append((
                f"Cleaning Pipa Transfer Jalur {j} (Atas)",
                f"TRF-PIPE-J0{j}-ATAS",
                "6 Bulan",
                "2026-05-15",
                "2026-11-15",
                "Pipa Transfer Botol"
            ))
            tasks_to_add.append((
                f"Cleaning Pipa Transfer Jalur {j} (Bawah)",
                f"TRF-PIPE-J0{j}-BWH",
                "6 Bulan",
                "2026-05-15",
                "2026-11-15",
                "Pipa Transfer Botol"
            ))

        # 7. Cleaning Storage Tank (1 - 8)
        for t in range(1, 9):
            tasks_to_add.append((
                f"Cleaning Storage Tank {t}",
                f"TK-STR-0{t}",
                "6 Bulan",
                "2026-04-20",
                "2026-10-20" if t <= 3 else "2026-11-20",
                "Storage Tank"
            ))

        # 8. Filtrasi & Steril Lainnya
        tasks_to_add.append(("Ganti Medium & HEPA Filter AHU-01", "AHU-STR-01", "3 Bulan", "2026-07-15", "2026-10-15", "Filtrasi & Steril"))
        tasks_to_add.append(("Ganti Pre Filter AHU-01", "AHU-STR-01", "1 Bulan", "2026-09-10", "2026-10-10", "Filtrasi & Steril"))
        tasks_to_add.append(("Cleaning Dust Collector Line 01", "DC-LINE-01", "1 Bulan", "2026-09-13", "2026-10-13", "Filtrasi & Steril"))
        tasks_to_add.append(("Ganti Tali Conveyor Main Line", "CV-MAIN-01", "1 Tahun", "2025-11-01", "2026-11-01", "Mekanik Lainnya"))

        cursor.executemany("""
            INSERT INTO maintenance_tasks (name, mouldingCode, intervalText, lastDone, nextDueDate, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tasks_to_add)
        conn.commit()
        
    conn.close()

# Jalankan inisialisasi database saat startup
init_db()

app = FastAPI(title="Moulding Maintenance System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskSchema(BaseModel):
    name: str
    mouldingCode: str
    intervalText: str
    lastDone: str
    nextDueDate: str
    category: str

class HistorySchema(BaseModel):
    task_id: int
    taskName: str
    mouldingCode: str
    category: str | None = "General"
    operatorName: str
    tanggalPengerjaan: str
    catatan: str
    status: str
    fotoBefore: str | None = None
    fotoAfter: str | None = None

@app.get("/")
def read_root():
    return {"message": "Backend FastAPI Moulding Maintenance System Berjalan Normal!"}

@app.get("/tasks")
def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintenance_tasks")
    rows = cursor.fetchall()
    tasks = [dict(row) for row in rows]
    conn.close()
    return tasks

@app.post("/tasks")
def create_task(task: TaskSchema):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO maintenance_tasks (name, mouldingCode, intervalText, lastDone, nextDueDate, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task.name, task.mouldingCode, task.intervalText, task.lastDone, task.nextDueDate, task.category))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"message": "Task berhasil ditambahkan ke database", "data": {"id": new_id, **task.dict()}}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskSchema):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")
    
    cursor.execute("""
        UPDATE maintenance_tasks 
        SET name = ?, mouldingCode = ?, intervalText = ?, lastDone = ?, nextDueDate = ?, category = ?
        WHERE id = ?
    """, (task.name, task.mouldingCode, task.intervalText, task.lastDone, task.nextDueDate, task.category, task_id))
    conn.commit()
    conn.close()
    return {"message": "Task berhasil diperbarui di database"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task tidak ditemukan")
    
    cursor.execute("DELETE FROM maintenance_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "Task berhasil dihapus"}

# --- ENDPOINT RIWAYAT (HISTORY) ---
@app.get("/history")
def get_history():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintenance_history ORDER BY id DESC")
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history

@app.post("/history")
def add_history(history: HistorySchema):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO maintenance_history (task_id, taskName, mouldingCode, category, operatorName, tanggalPengerjaan, catatan, status, fotoBefore, fotoAfter)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        history.task_id, 
        history.taskName, 
        history.mouldingCode, 
        history.category, 
        history.operatorName, 
        history.tanggalPengerjaan, 
        history.catatan, 
        history.status,
        history.fotoBefore,
        history.fotoAfter
    ))
    conn.commit()
    conn.close()
    return {"message": "Riwayat pengerjaan berhasil disimpan ke database"}