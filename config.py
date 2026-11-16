# config.py - Base de Conocimiento Agronomico Auditada (FAO-56, FAO-33 y RUSLE)

CULTIVOS_FAO = {
    "maiz": {
        "id": "maiz",
        "nombre_es": "Maíz",
        "nombre_en": "Maize (Corn)",
        "familia": "graminea",
        "es_leguminosa": False,
        "es_cobertura": False,
        "kc_ini": 0.30, "kc_med": 1.20, "kc_fin": 0.35,
        "ky_flor": 1.50, "zr_m": 1.2, "p_agot": 0.55,
        "n_fijado_kg": -45, "mo_aporte_t": 1.5, "factor_c_rusle": 0.48
    },
    "frijol": {
        "id": "frijol",
        "nombre_es": "Frijol Común",
        "nombre_en": "Common Bean",
        "familia": "leguminosa_grano",
        "es_leguminosa": True,
        "es_cobertura": False,
        "kc_ini": 0.40, "kc_med": 1.15, "kc_fin": 0.35,
        "ky_flor": 1.10, "zr_m": 0.6, "p_agot": 0.45,
        "n_fijado_kg": 40, "mo_aporte_t": 1.8, "factor_c_rusle": 0.36
    },
    "sorgo": {
        "id": "sorgo",
        "nombre_es": "Sorgo",
        "nombre_en": "Sorghum",
        "familia": "graminea",
        "es_leguminosa": False,
        "es_cobertura": False,
        "kc_ini": 0.30, "kc_med": 1.05, "kc_fin": 0.55,
        "ky_flor": 0.55, "zr_m": 1.5, "p_agot": 0.55,
        "n_fijado_kg": -25, "mo_aporte_t": 2.8, "factor_c_rusle": 0.24
    },
    "caupi": {
        "id": "caupi",
        "nombre_es": "Caupí (Frijol Alacín)",
        "nombre_en": "Cowpea",
        "familia": "leguminosa_grano",
        "es_leguminosa": True,
        "es_cobertura": True,
        "kc_ini": 0.40, "kc_med": 1.05, "kc_fin": 0.40,
        "ky_flor": 0.85, "zr_m": 1.1, "p_agot": 0.55,
        "n_fijado_kg": 75, "mo_aporte_t": 3.4, "factor_c_rusle": 0.14
    },
    "cafe": {
        "id": "cafe",
        "nombre_es": "Café Arábica",
        "nombre_en": "Arabica Coffee",
        "familia": "perenne_agroforestal",
        "es_leguminosa": False,
        "es_cobertura": False,
        "kc_ini": 0.90, "kc_med": 1.05, "kc_fin": 0.95,
        "ky_flor": 1.15, "zr_m": 1.3, "p_agot": 0.40,
        "n_fijado_kg": -35, "mo_aporte_t": 3.8, "factor_c_rusle": 0.08
    },
    "canavalia": {
        "id": "canavalia",
        "nombre_es": "Canavalia (Cobertura)",
        "nombre_en": "Canavalia (Cover Crop)",
        "familia": "leguminosa_cobertura",
        "es_leguminosa": True,
        "es_cobertura": True,
        "kc_ini": 0.40, "kc_med": 1.10, "kc_fin": 0.60,
        "ky_flor": 0.65, "zr_m": 1.6, "p_agot": 0.60,
        "n_fijado_kg": 115, "mo_aporte_t": 5.5, "factor_c_rusle": 0.05
    },
    "mucuna": {
        "id": "mucuna",
        "nombre_es": "Mucuna (Abono Verde)",
        "nombre_en": "Mucuna (Green Manure)",
        "familia": "leguminosa_cobertura",
        "es_leguminosa": True,
        "es_cobertura": True,
        "kc_ini": 0.40, "kc_med": 1.15, "kc_fin": 0.55,
        "ky_flor": 0.75, "zr_m": 1.3, "p_agot": 0.50,
        "n_fijado_kg": 135, "mo_aporte_t": 6.8, "factor_c_rusle": 0.04
    },
    "barbecho": {
        "id": "barbecho",
        "nombre_es": "Suelo Desnudo",
        "nombre_en": "Bare Soil",
        "familia": "ninguna",
        "es_leguminosa": False,
        "es_cobertura": False,
        "kc_ini": 0.15, "kc_med": 0.15, "kc_fin": 0.15,
        "ky_flor": 1.00, "zr_m": 0.3, "p_agot": 0.50,
        "n_fijado_kg": -15, "mo_aporte_t": 0.0, "factor_c_rusle": 0.85
    }
}
