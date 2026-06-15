"""
profiling.py
Pipeline de Auditoría Forense y Diagnóstico de Calidad de Datos Clínicos.
Entorno: SISCAT / Proyecto Final BIC 2025-2026.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any

# =============================================================================
# 1. FUNCIONES GENÉRICAS (Motor de Auditoría)
# =============================================================================

def load_raw_data(file_path: Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Centraliza la lectura física abstrayendo el formato y forzando codificación UTF-8.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Fallo crítico: Archivo no localizado en ruta {file_path}")
    
    if file_path.suffix == '.csv':
        return pd.read_csv(file_path, encoding='utf-8')
    elif file_path.suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    else:
        raise ValueError(f"Formato no soportado por el pipeline de ingestión: {file_path.suffix}")

def check_missing_values(df: pd.DataFrame) -> Dict[str, Tuple[int, float]]:
    """
    Mapea la presencia de nulos y calcula (cantidad absoluta, porcentaje).
    """
    total_rows = len(df)
    if total_rows == 0:
        return {str(col): (0, 0.0) for col in df.columns}
    
    null_counts = df.isna().sum()
    return {
        str(col): (int(count), round(float(count) / total_rows * 100, 2))
        for col, count in null_counts.items()
    }

def validate_data_ranges(df: pd.DataFrame, rules: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
    """
    Evalúa límites biológicos y lógicos retornando las filas que infringen las reglas.
    """
    if df.empty:
        return df
    
    mask = pd.Series(False, index=df.index)
    for col, (min_val, max_val) in rules.items():
        if col in df.columns:
            # Detectar valores menores al mínimo o mayores al máximo
            col_mask = (df[col] < min_val) | (df[col] > max_val)
            mask = mask | col_mask
            
    return df[mask]

def validate_id_integrity(source_ids: pd.Series, target_ids: pd.Series) -> List[str]:
    """
    Comprueba consistencia referencial: IDs en 'source' que no existen en 'target'.
    """
    source_set = set(source_ids.dropna().astype(str))
    target_set = set(target_ids.dropna().astype(str))
    
    # Diferencia de conjuntos para encontrar huérfanos
    return list(source_set - target_set)

def generate_summary_report(report_data: Dict[str, Any]) -> str:
    """
    Consolida las métricas en texto estructurado y directo para consola/log.
    """
    lines = ["\n" + "="*60, "REPORTE DE AUDITORÍA DE CALIDAD (PROFILING)", "="*60]
    
    for asset, metrics in report_data.items():
        lines.append(f"\n>>> ACTIVO: {asset.upper()}")
        for metric_name, value in metrics.items():
            if isinstance(value, dict):
                lines.append(f"  [-] {metric_name.upper()}:")
                for k, v in value.items():
                    if v[0] > 0:  # Imprimir solo si hay nulos para reducir ruido
                        lines.append(f"      - {k}: {v[0]} nulos ({v[1]}%)")
            elif isinstance(value, list):
                lines.append(f"  [-] {metric_name.upper()}: {len(value)} discrepancias encontradas.")
            elif isinstance(value, pd.DataFrame):
                lines.append(f"  [-] {metric_name.upper()}: {len(value)} registros infringen límites lógicos.")
            else:
                lines.append(f"  [-] {metric_name.upper()}: {value}")
                
    lines.append("="*60 + "\n")
    return "\n".join(lines)


# =============================================================================
# 2. ORQUESTACIÓN Y APLICACIÓN ESPECÍFICA (Flujo Principal)
# =============================================================================

def main():
    # Estructura de directorios rígida
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    # Inicialización del diccionario maestro
    reporte_calidad = {}
    
    # -------------------------------------------------------------------------
    # Activos 6 y 7: Inventarios de IDs Clínicos
    # -------------------------------------------------------------------------
    df_ids1 = load_raw_data(data_dir / "patient_IDs.xlsx")
    df_ids2 = load_raw_data(data_dir / "patient_IDs 2.xlsx")
    
    orphans_1_not_in_2 = validate_id_integrity(df_ids1['patient'], df_ids2['patient'])
    orphans_2_not_in_1 = validate_id_integrity(df_ids2['patient'], df_ids1['patient'])
    
    reporte_calidad['patient_ids_mapping'] = {
        'total_ids_archivo_1': len(df_ids1),
        'total_ids_archivo_2': len(df_ids2),
        'huerfanos_1_vs_2': orphans_1_not_in_2,
        'huerfanos_2_vs_1': orphans_2_not_in_1
    }
    
    # Se establece un listado maestro provisional para validación
    master_ids = df_ids1['patient']
    
    # -------------------------------------------------------------------------
    # Activo 3: Datos Genómicos (genomico_sintetico.csv)
    # -------------------------------------------------------------------------
    df_gen = load_raw_data(data_dir / "genomico_sintetico.csv")
    
    # Extraer identificadores de pacientes desde los nombres de las columnas
    # Suponiendo nomenclatura p1, p2, p3...
    patient_columns = [col for col in df_gen.columns if col.startswith('p') and col[1:].isdigit()]
    
    reporte_calidad['genomico_sintetico'] = {
        'nulos': check_missing_values(df_gen),
        'ids_huerfanos_vs_clinica': validate_id_integrity(pd.Series(patient_columns), master_ids)
    }
    
    # -------------------------------------------------------------------------
    # Activo 4: Etiquetas Radiológicas (imagenes_informes_BI-RADS.xlsx)
    # -------------------------------------------------------------------------
    df_birads = load_raw_data(data_dir / "imagenes_informes_BI-RADS.xlsx")
    nulos_birads = check_missing_values(df_birads)
    
    reporte_calidad['informes_birads'] = {
        'nulos': nulos_birads,
        'filas_fantasmas_detectadas': nulos_birads.get('patient', (0, 0.0))[0]
    }
    
    # -------------------------------------------------------------------------
    # Activo 5: Metadatos ML (mamografias_ML.xlsx)
    # -------------------------------------------------------------------------
    df_ml = load_raw_data(data_dir / "mamografias_ML.xlsx")
    
    # Reglas de negocio predefinidas
    metric_rules = {
        'radius': (5.0, 40.0),
        'area': (100.0, 3000.0)
    }
    
    reporte_calidad['mamografias_ml'] = {
        'nulos': check_missing_values(df_ml),
        'outliers_limites_biologicos': validate_data_ranges(df_ml, metric_rules),
        'ids_huerfanos_vs_clinica': validate_id_integrity(df_ml['patient'], master_ids)
    }
    
    # -------------------------------------------------------------------------
    # 3. CONSOLIDACIÓN Y EXPORTACIÓN DEL REPORTE
    # -------------------------------------------------------------------------
    informe_final = generate_summary_report(reporte_calidad)
    print(informe_final)
    
    # Opcional: Escribir log en disco para cumplimiento de principio Reusable (FAIR)
    log_path = base_dir / "profiling_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(informe_final)

if __name__ == "__main__":
    main()
    