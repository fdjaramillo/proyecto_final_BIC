"""
build_db.py
Orquestador Principal de Integración de Datos (ETL) y Generación de Base de Datos.
Entorno: SISCAT / Proyecto Final BIC 2025-2026.
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path

# Importación de las funciones maestras de transformación
from cleaning import (
    process_patient_master_registry,
    process_genomic_matrix,
    process_radiological_reports,
    process_mamographies_ml
)

# =============================================================================
# 1. CONFIGURACIÓN DE RUTAS Y ENTORNO
# =============================================================================

# Definición de la estructura de directorios estricta
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
DB_PATH = BASE_DIR / "repositorio_clinico.db"
SCHEMA_PATH = SRC_DIR / "schema.sql"

def main():
    print("Iniciando pipeline de integración de datos ETL...")

    # =============================================================================
    # 2. LIMPIEZA DEL ENTORNO Y RECONSTRUCCIÓN DEL ESQUEMA FÍSICO
    # =============================================================================
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"[OK] Archivo de base de datos anterior eliminado: {DB_PATH.name}")

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Fallo crítico: No se encuentra el archivo DDL en {SCHEMA_PATH}")

    # Conexión al motor SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Activación estricta de restricciones referenciales
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Inyección del esquema relacional
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("[OK] Esquema SQL (DDL) inyectado correctamente.")

        # =============================================================================
        # 3. EXTRACCIÓN Y TRANSFORMACIÓN EN MEMORIA (Invocación a cleaning.py)
        # =============================================================================
        print("Procesando y normalizando activos clínicos...")

        # Activos 6 y 7: Pacientes
        df_ids1_raw = pd.read_excel(DATA_DIR / "patient_IDs.xlsx")
        df_ids2_raw = pd.read_excel(DATA_DIR / "patient_IDs 2.xlsx")
        df_pacientes = process_patient_master_registry(df_ids1_raw, df_ids2_raw)

        # Activo 3: Genómica
        df_gen_raw = pd.read_csv(DATA_DIR / "genomico_sintetico.csv", encoding="utf-8")
        df_variantes = process_genomic_matrix(df_gen_raw)

        # Activo 5: Mamografías ML
        df_ml_raw = pd.read_excel(DATA_DIR / "mamografias_ML.xlsx")
        df_mamografias = process_mamographies_ml(df_ml_raw)

        # Activo 4: Informes BI-RADS
        df_birads_raw = pd.read_excel(DATA_DIR / "imagenes_informes_BI-RADS.xlsx")
        df_informes = process_radiological_reports(df_birads_raw)

        # =============================================================================
        # 4. CONTROL DE CALIDAD PRE-CARGA (Defensa contra Constraint Errors)
        # =============================================================================
        if df_pacientes['patient_id'].duplicated().any():
            raise ValueError("Error de Integridad: IDs de pacientes duplicados en el registro maestro.")
        
        if df_mamografias['patient_id'].duplicated().any():
            raise ValueError("Error de Integridad: Relación 1-a-N detectada en tabla de métricas ML (violación de diseño 1-a-1).")

        # =============================================================================
        # 5. CARGA (INSERCIÓN MASIVA A SQL)
        # =============================================================================
        print("Iniciando inyección de datos a SQLite...")

        # El orden de carga es jerárquico y obligatorio para no violar Claves Foráneas
        
        # 5.1 Tabla Padre: pacientes
        df_pacientes.to_sql(name='pacientes', con=conn, if_exists='append', index=False)
        print(f"[OK] Insertados {len(df_pacientes)} registros en 'pacientes'.")

        # 5.2 Tabla Hija 1: variantes_genomicas
        df_variantes.to_sql(name='variantes_genomicas', con=conn, if_exists='append', index=False)
        print(f"[OK] Insertados {len(df_variantes)} registros en 'variantes_genomicas'.")

        # 5.3 Tabla Hija 2: mamografias_ml (Subtipo obligatorio de pacientes)
        df_mamografias.to_sql(name='mamografias_ml', con=conn, if_exists='append', index=False)
        print(f"[OK] Insertados {len(df_mamografias)} registros en 'mamografias_ml'.")

        # 5.4 Tabla Hija 3: informes_birads (Subtipo opcional de pacientes)
        df_informes.to_sql(name='informes_birads', con=conn, if_exists='append', index=False)
        print(f"[OK] Insertados {len(df_informes)} registros en 'informes_birads'.")

        # Transacción definitiva
        conn.commit()
        print("Pipeline finalizado con éxito. Base de datos operativa.")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise RuntimeError(f"Fallo crítico de integridad referencial durante la carga SQL: {e}")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Excepción no controlada en el pipeline ETL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
