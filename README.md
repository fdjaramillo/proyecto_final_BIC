# Proyecto Final - Curso de Bioinformática Clínica

Este repositorio contiene el proyecto final del Curso de Bioinformática Clínica impartido por [Eixample Clinic](https://eixampleclinic.es/es/cursos-formacion-reglada/curso-bioinformatica-clinica/).

El objetivo del trabajo es diseñar y ejecutar un pipeline ETL para integrar datos biomédicos multimodales. El sistema centraliza flujos independientes de información clínica, radiómica y genómica en una base de datos relacional optimizada para su análisis posterior.

## Datos Recibidos

Los datos brutos proporcionados para el proyecto incluyen:
* Identificadores y registro maestro de pacientes: `patient_IDs.xlsx` y `patient_IDs_2.xlsx`.
* Métricas biofísicas de mamografías generadas mediante Machine Learning: `mamografias_ML.xlsx`.
* Informes radiológicos en texto con categorización estándar BI-RADS: `imagenes_informes_BI-RADS.xlsx`.
* Matrices de variantes genómicas con genotipos en formato tipo VCF: `genomico_sintetico.csv`.

Todos los conjuntos de datos de este proyecto son **sintéticos** y **NO** contienen información de carácter personal. Su almacenamiento y versionado en este repositorio es seguro.

## Pasos Generales del Proyecto

El proceso se divide en tres etapas secuenciales:

1. **Auditoría de Calidad (Profiling):** Análisis en memoria de los archivos brutos para evaluar la dispersión de los datos (sparsity), detectar registros duplicados, comprobar límites lógicos y biológicos en variables numéricas, y revisar la integridad referencial antes de diseñar la base de datos.
2. **Limpieza y Transformación (Cleaning):** Normalización de fechas al estándar ISO-8601, homogeneización de diagnósticos clínicos y eliminación de filas vacías o nulos estructurales. Asegurar el cumplimiento de las formas normales en la base de datos para evitar redundancias.
3. **Carga en Base de Datos (Loading):** Creación del esquema e inserción de los datos limpios en SQLite. La carga se realiza de forma jerárquica respetando las claves primarias y foráneas, utilizando transacciones (commit/rollback) para evitar datos corruptos o cargas parciales.

## Estructura del Repositorio
El repositorio se organiza de la siguiente manera:

```
.
├── data
│   ├── genomico_sintetico.csv
│   ├── imagenes_informes_BI-RADS.xlsx
│   ├── mamografias_ML.xlsx
│   ├── patient_IDs 2.xlsx
│   └── patient_IDs.xlsx
├── docs
│   ├── Proyecto Final BIC 2025-2026.docx
│   └── Rúbrica del Proyecto.xlsx
├── notebooks
│   ├── 01_Auditoria_y_Arquitectura_SQL_12.6.26.ipynb
│   └── proyecto_final_BIC.ipynb
├── plots
│   ├── barplot_pacientes_hospital.png
│   └── boxplot_radio_area_tumor_diagnostico.png
├── scripts
│   ├── build_db.py
│   ├── cleaning.py
│   ├── profiling.py
│   └── schema.sql
├── .gitignore
├── .python-version
├── README.md
├── proyecto_bic.db
├── pyproject.toml
└── uv.lock
```
