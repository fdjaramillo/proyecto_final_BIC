-- Activación obligatoria de integridad referencial en SQLite
PRAGMA foreign_keys = ON;

-- Eliminar tablas si existen para evitar errores al crear nuevas tablas
DROP TABLE IF EXISTS pacientes;
DROP TABLE IF EXISTS mamografias;
DROP TABLE IF EXISTS hallazgos_radiologicos;
DROP TABLE IF EXISTS variantes_genomicas;

CREATE TABLE IF NOT EXISTS pacientes (
    patient TEXT PRIMARY KEY,
    id_biop TEXT UNIQUE,
    visit_date TEXT,
    hospital TEXT,
    sex TEXT,
    birth_date TEXT
);

CREATE TABLE IF NOT EXISTS mamografias (
    patient TEXT PRIMARY KEY,
    diagnostic TEXT,
    radius REAL,
    texture REAL,
    perimeter REAL,
    area REAL,
    regularity REAL,
    compactability REAL,
    concavity REAL,
    simetry REAL,
    fractal_dimension REAL,
    Fecha TEXT,
    FOREIGN KEY (patient) REFERENCES pacientes(patient) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS hallazgos_radiologicos (
    patient TEXT PRIMARY KEY,
    hallazgo TEXT,
    localizacion TEXT,
    birads_cat TEXT,
    observaciones TEXT,
    FOREIGN KEY (patient) REFERENCES pacientes(patient) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS variantes_genomicas (
    variant_id TEXT,
    patient TEXT,
    chrom TEXT,
    pos INTEGER,
    ref TEXT,
    alt TEXT,
    genotype TEXT,
    PRIMARY KEY (variant_id, patient),
    FOREIGN KEY (patient) REFERENCES pacientes(patient) ON DELETE RESTRICT
);