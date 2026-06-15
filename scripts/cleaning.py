import pandas as pd
import numpy as np
from typing import List

# =============================================================================
# 1. FUNCIONES UTILITARIAS (Compartidas)
# =============================================================================

def standardize_date_format(date_series: pd.Series) -> pd.Series:
    """
    Detecta y convierte strings de fechas heterogéneas al formato ISO-8601 (YYYY-MM-DD).
    """
    return pd.to_datetime(date_series, errors='coerce').dt.strftime('%Y-%m-%d')

def clean_string_whitespace(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Elimina espacios en blanco al inicio/final y fuerza texto a minúsculas.
    """
    df_cleaned = df.copy()
    for col in columns:
        if col in df_cleaned.columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower()
    return df_cleaned


# =============================================================================
# 2. FUNCIONES DE TRANSFORMACIÓN MAESTRAS (Específicas por Activo)
# =============================================================================

def process_patient_master_registry(df_ids1: pd.DataFrame, df_ids2: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida, desduplica y normaliza el inventario maestro de pacientes.
    """
    df_master = pd.concat([df_ids1, df_ids2], ignore_index=True)
    df_master = df_master.drop_duplicates(subset=['patient'], keep='first')
    df_master = df_master.rename(columns={'patient': 'patient_id'})
    
    if 'birth_date' in df_master.columns:
        df_master['birth_date'] = standardize_date_format(df_master['birth_date'])
    if 'visit_date' in df_master.columns:
        df_master['visit_date'] = standardize_date_format(df_master['visit_date'])
        
    if 'sex' in df_master.columns:
        df_master['sex'] = df_master['sex'].replace({'M': 'Male', 'F': 'Female', 'Mujer': 'Female', 'Hombre': 'Male'})
        df_master = df_master[df_master['sex'].isin(['Female', 'Male'])]
        
    return df_master

def process_genomic_matrix(df_gen: pd.DataFrame) -> pd.DataFrame:
    """
    Transpone la matriz ómica a formato largo y filtra genotipos no resueltos.
    """
    id_vars = ['#CHROM', 'POS', 'ID', 'REF', 'ALT']
    available_id_vars = [col for col in id_vars if col in df_gen.columns]
    patient_cols = [col for col in df_gen.columns if col.startswith('p') and col[1:].isdigit()]
    
    df_long = pd.melt(df_gen, id_vars=available_id_vars, value_vars=patient_cols, 
                      var_name='patient_id', value_name='genotype')
    
    df_long = df_long.dropna(subset=['genotype'])
    df_long = df_long[df_long['genotype'] != './.']
    
    df_long['variant_id'] = (df_long['#CHROM'].astype(str) + '_' + 
                             df_long['POS'].astype(str) + '_' + 
                             df_long['REF'].astype(str) + '_' + 
                             df_long['ALT'].astype(str))
    
    df_long = df_long.rename(columns={'#CHROM': 'chrom', 'POS': 'pos', 'REF': 'ref', 'ALT': 'alt'})
    
    return df_long[['variant_id', 'patient_id', 'chrom', 'pos', 'ref', 'alt', 'genotype']]

def process_radiological_reports(df_birads: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia informes radiológicos, elimina filas fantasma y extrae la categoría BI-RADS pura.
    """
    df_clean = df_birads.dropna(subset=['patient']).copy()
    df_clean = df_clean.rename(columns={'patient': 'patient_id'})
    
    text_cols = ['Hallazgo Imagen', 'Localización']
    df_clean = clean_string_whitespace(df_clean, text_cols)
    
    if 'Categoría BI-RADS' in df_clean.columns:
        df_clean['Categoría BI-RADS'] = df_clean['Categoría BI-RADS'].str.replace('BI-RADS ', '', regex=False)
        
    return df_clean

def process_mamographies_ml(df_ml: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza métricas de ML, imputa nulos por mediana condicionada y crea testigos de calidad.
    """
    df_clean = df_ml.copy()
    df_clean = df_clean.rename(columns={'patient': 'patient_id'})
    
    if 'diagnostic' in df_clean.columns:
        df_clean['diagnostic'] = df_clean['diagnostic'].replace({'Malignant': 'Maligno', 'Benign': 'Benigno'})
    
    metric_cols = ['radius', 'texture', 'perimeter', 'area', 'regularity', 'compactability', 'concavity', 'simetry', 'fractal_dimension']
    available_metrics = [col for col in metric_cols if col in df_clean.columns]
    
    # Generación de banderas de calidad e imputación
    for col in available_metrics + ['diagnostic']:
        if col in df_clean.columns:
            df_clean[f"{col}_imputed"] = df_clean[col].isna().astype(int)
            
    # Imputación condicionada para métricas
    for col in available_metrics:
        if 'diagnostic' in df_clean.columns:
            df_clean[col] = df_clean.groupby('diagnostic')[col].transform(lambda x: x.fillna(x.median()))
        # Cobertura residual por si existen registros sin diagnóstico
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        
    # Imputación para diagnóstico (moda)
    if 'diagnostic' in df_clean.columns:
        mode_val = df_clean['diagnostic'].mode(dropna=True)[0]
        df_clean['diagnostic'] = df_clean['diagnostic'].fillna(mode_val)
        
    if 'Fecha' in df_clean.columns:
        df_clean['Fecha'] = standardize_date_format(df_clean['Fecha'])
        
    return df_clean
