# motor_agronomico.py - Balance Hidrico Anual de 3 Ciclos (FAO-56), Fenologia Real y RUSLE
import math
import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from itertools import groupby
from config import CULTIVOS_FAO

def analizar_tendencias_mann_kendall(df: pd.DataFrame):
    df_eval = df.loc["2000-01-01":].copy()
    anual = df_eval.groupby(df_eval.index.year).agg(
        lluvia_mm=("PRECTOTCORR", "sum"),
        tmax_c=("T2M_MAX", "mean")
    )

    dias_canicula = []
    for yr, grp in df_eval.groupby(df_eval.index.year):
        sub_c = grp[(grp.index.month == 7) | ((grp.index.month == 8) & (grp.index.day <= 20))]
        sequia = (sub_c["PRECTOTCORR"] < 2.0).astype(int)
        racha_max = max((sum(1 for _ in g) for k, g in groupby(sequia) if k == 1), default=0)
        dias_canicula.append(racha_max)
    anual["canicula_dias"] = dias_canicula

    def sen_slope_decada(serie):
        x = serie.index.values
        y = serie.values
        if len(x) < 4:
            return 0.0
        slopes = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x))]
        return round(float(np.median(slopes)) * 10.0, 2)

    tau_c, p_c = kendalltau(anual.index.values, anual["canicula_dias"].values)
    return {
        "canicula_media_dias": int(round(float(anual["canicula_dias"].mean()), 0)),
        "sen_canicula_decada": sen_slope_decada(anual["canicula_dias"]),
        "sen_lluvia_decada": sen_slope_decada(anual["lluvia_mm"]),
        "sen_temp_decada": sen_slope_decada(anual["tmax_c"]),
        "tau_canicula": round(float(tau_c), 3) if not np.isnan(tau_c) else 0.0,
        "p_valor_canicula": round(float(p_c), 3) if not np.isnan(p_c) else 1.0
    }

def generar_estrategias_desde_granos(granos_str: str, pendiente_pct: float, elevacion_m: float):
    codigos = [g.strip() for g in granos_str.split(",") if g.strip() in CULTIVOS_FAO and g.strip() != "barbecho"]
    seleccionados = []
    for c in codigos:
        if c not in seleccionados:
            seleccionados.append(c)

    num_unicos = len(seleccionados)
    es_rotacion_valida = (num_unicos >= 2)

    c_testigo = seleccionados[0] if num_unicos >= 1 else "maiz"
    nom_testigo_es = CULTIVOS_FAO[c_testigo]["nombre_es"]
    nom_testigo_en = CULTIVOS_FAO[c_testigo]["nombre_en"]

    estrategia_testigo = {
        "id": "rot_tradicional",
        "nombre_es": f"Testigo sin Rotación (Monocultivo de {nom_testigo_es})",
        "nombre_en": f"Unrotated Baseline ({nom_testigo_en} Monoculture)",
        "ciclo_1": c_testigo, "ciclo_2": c_testigo, "ciclo_3": "barbecho",
        "quema_rastrojo": True,
        "confianza": "Alta",
        "meses_desnudo": ["Dic", "Ene", "Feb", "Mar", "Abr", "Ago"],
        "descripcion_es": f"Sembrar únicamente {nom_testigo_es} sin alternar familias botánicas ni cubrir el suelo en época seca agota nutrientes y expone la parcela a erosión.",
        "descripcion_en": f"Growing only {nom_testigo_en} without alternating botanical families or covering soil in the dry season depletes nutrients and exposes slopes.",
        "validacion_es": "El monocultivo continuo degrada la estructura física del suelo y reduce la retención hídrica.",
        "validacion_en": "Continuous monoculture degrades soil structure and reduces water retention."
    }

    if not es_rotacion_valida:
        sug_leg = "Canavalia o Frijol" if pendiente_pct < 20 else "Mucuna o Canavalia"
        info_validacion = {
            "es_valida": False,
            "num_cultivos_unicos": num_unicos,
            "cultivos_activos": seleccionados,
            "mensaje_es": f"⚠️ Sin Rotación ({num_unicos} cultivo seleccionado: {nom_testigo_es}). Selecciona al menos 2 cultivos distintos para activar la rotación.",
            "mensaje_en": f"⚠️ No Rotation ({num_unicos} crop selected: {nom_testigo_en}). Select at least 2 distinct crops to enable rotation.",
            "sugerencia_es": f"Sugerencia para pendiente de {pendiente_pct}%: Activa un segundo cultivo arriba (ej. {sug_leg} o Sorgo) para comparar rotaciones reales.",
            "sugerencia_en": f"Suggestion for {pendiente_pct}% slope: Enable a second crop above (e.g. {sug_leg} or Sorghum) to compare real rotations."
        }
        return [estrategia_testigo], info_validacion

    cereales = [c for c in seleccionados if not CULTIVOS_FAO[c]["es_leguminosa"]]
    leguminosas_grano = [c for c in seleccionados if CULTIVOS_FAO[c]["es_leguminosa"] and not CULTIVOS_FAO[c]["es_cobertura"]]
    coberturas = [c for c in seleccionados if CULTIVOS_FAO[c]["es_cobertura"]]

    estrategias = [estrategia_testigo]

    c1_u = cereales[0] if cereales else seleccionados[0]
    c2_u = leguminosas_grano[0] if leguminosas_grano else (seleccionados[1] if len(seleccionados) > 1 else seleccionados[0])
    if c2_u == c1_u and len(seleccionados) > 1:
        c2_u = seleccionados[1]
    c3_u = coberturas[0] if coberturas else (seleccionados[2] if len(seleccionados) > 2 else "barbecho")

    meses_des_1 = ["Dic", "Ene", "Feb", "Mar", "Abr"] if c3_u == "barbecho" else (["Mar", "Abr"] if not CULTIVOS_FAO[c3_u]["es_cobertura"] else [])
    estrategias.append({
        "id": "rot_usuario_directa",
        "nombre_es": f"Secuencia Seleccionada ({CULTIVOS_FAO[c1_u]['nombre_es']} → {CULTIVOS_FAO[c2_u]['nombre_es']} → {CULTIVOS_FAO[c3_u]['nombre_es']})",
        "nombre_en": f"Selected Sequence ({CULTIVOS_FAO[c1_u]['nombre_en']} → {CULTIVOS_FAO[c2_u]['nombre_en']} → {CULTIVOS_FAO[c3_u]['nombre_en']})",
        "ciclo_1": c1_u, "ciclo_2": c2_u, "ciclo_3": c3_u,
        "quema_rastrojo": False,
        "confianza": "Alta",
        "meses_desnudo": meses_des_1,
        "descripcion_es": "Alternancia directa entre los cultivos que seleccionaste conservando los residuos de cosecha sobre el suelo.",
        "descripcion_en": "Direct alternation among your selected crops while retaining crop residues on the soil surface.",
        "validacion_es": "Ajustar densidad de siembra y fecha de inicio según humedad superficial SMAP.",
        "validacion_en": "Adjust planting density and start date according to SMAP surface moisture."
    })

    c1_opt = "sorgo" if "sorgo" in seleccionados else ("cafe" if ("cafe" in seleccionados and elevacion_m >= 500) else c1_u)
    c2_opt = "caupi" if "caupi" in seleccionados else ("frijol" if "frijol" in seleccionados else c2_u)
    c3_opt = coberturas[0] if coberturas else "canavalia"

    estrategias.append({
        "id": "rot_optimizada_canicula",
        "nombre_es": f"Óptima Anti-Sequía ({CULTIVOS_FAO[c1_opt]['nombre_es']} → {CULTIVOS_FAO[c2_opt]['nombre_es']} → {CULTIVOS_FAO[c3_opt]['nombre_es']})",
        "nombre_en": f"Drought-Optimized ({CULTIVOS_FAO[c1_opt]['nombre_en']} → {CULTIVOS_FAO[c2_opt]['nombre_en']} → {CULTIVOS_FAO[c3_opt]['nombre_en']})",
        "ciclo_1": c1_opt, "ciclo_2": c2_opt, "ciclo_3": c3_opt,
        "quema_rastrojo": False,
        "confianza": "Alta",
        "meses_desnudo": [],
        "descripcion_es": "Ubica el cultivo de menor sensibilidad hídrica en Primera y protege la humedad radicular en época seca con cobertura leguminosa.",
        "descripcion_en": "Places the most drought-tolerant crop in the first cycle and protects root-zone moisture in the dry season with legume cover.",
        "validacion_es": "Sembrar la cobertura en relevo antes de finalizar Postrera para aprovechar la humedad residual.",
        "validacion_en": "Relay-plant the cover crop before the end of the second season to use residual moisture."
    })

    c3_reg = "mucuna" if "mucuna" in seleccionados else ("canavalia" if "canavalia" in seleccionados else "mucuna")
    c2_reg = "caupi" if "caupi" in seleccionados else c2_opt
    estrategias.append({
        "id": "rot_proteccion_ladera",
        "nombre_es": f"Regeneración de Suelo ({CULTIVOS_FAO[c1_u]['nombre_es']} → {CULTIVOS_FAO[c2_reg]['nombre_es']} → {CULTIVOS_FAO[c3_reg]['nombre_es']})",
        "nombre_en": f"Soil Regeneration ({CULTIVOS_FAO[c1_u]['nombre_en']} → {CULTIVOS_FAO[c2_reg]['nombre_en']} → {CULTIVOS_FAO[c3_reg]['nombre_en']})",
        "ciclo_1": c1_u, "ciclo_2": c2_reg, "ciclo_3": c3_reg,
        "quema_rastrojo": False,
        "confianza": "Media",
        "meses_desnudo": [],
        "descripcion_es": "Maximiza la fijación biológica de nitrógeno y forma un colchón orgánico permanente contra la escorrentía.",
        "descripcion_en": "Maximizes biological nitrogen fixation and forms a permanent organic mulch against runoff.",
        "validacion_es": "Manejar poda de guías de la cobertura viva para evitar competencia con el cultivo principal.",
        "validacion_en": "Manage cover crop vines to prevent competition with the main crop."
    })

    tiene_leg = any(CULTIVOS_FAO[c]["es_leguminosa"] for c in seleccionados)
    tiene_cob = any(CULTIVOS_FAO[c]["es_cobertura"] for c in seleccionados)
    lista_nom_es = ", ".join(CULTIVOS_FAO[c]["nombre_es"] for c in seleccionados)
    lista_nom_en = ", ".join(CULTIVOS_FAO[c]["nombre_en"] for c in seleccionados)

    if not tiene_leg:
        sug_es = f"Seleccionaste {lista_nom_es}, pero falta una leguminosa: el balance de nitrógeno será negativo. Activa Frijol, Caupí o Canavalia."
        sug_en = f"You selected {lista_nom_en}, but lack a legume: nitrogen balance will be negative. Enable Bean, Cowpea, or Canavalia."
    elif not tiene_cob and pendiente_pct >= 10.0:
        sug_es = f"Con pendiente de {pendiente_pct}%, agrega Canavalia o Mucuna a tu selección ({lista_nom_es}) para cubrir el suelo entre diciembre y abril."
        sug_en = f"On a {pendiente_pct}% slope, add Canavalia or Mucuna to your selection ({lista_nom_en}) to cover the soil from December to April."
    else:
        sug_es = f"Combinación equilibrada ({lista_nom_es}): alterna extracción de cereal con fijación de nitrógeno y cobertura protectora."
        sug_en = f"Balanced combination ({lista_nom_en}): alternates cereal extraction with nitrogen fixation and protective cover."

    return estrategias, {
        "es_valida": True,
        "num_cultivos_unicos": num_unicos,
        "cultivos_activos": seleccionados,
        "mensaje_es": f"✓ Rotación Válida ({num_unicos} cultivos activos)",
        "mensaje_en": f"✓ Valid Rotation ({num_unicos} active crops)",
        "sugerencia_es": sug_es,
        "sugerencia_en": sug_en
    }

def calcular_parametros_rotacion(rot: dict, suelo_info: dict):
    c1 = CULTIVOS_FAO[rot["ciclo_1"]]
    c2 = CULTIVOS_FAO[rot["ciclo_2"]]
    c3 = CULTIVOS_FAO[rot["ciclo_3"]]

    factor_c_medio = round((c1["factor_c_rusle"] + c2["factor_c_rusle"] + c3["factor_c_rusle"]) / 3.0, 3)
    mo_total = round(c1["mo_aporte_t"] + c2["mo_aporte_t"] + c3["mo_aporte_t"], 1)
    n_total = c1["n_fijado_kg"] + c2["n_fijado_kg"] + c3["n_fijado_kg"]

    bono_retencion = round(mo_total * 2.5, 1) if not rot["quema_rastrojo"] else 0.0
    return {
        "c1": c1, "c2": c2, "c3": c3,
        "factor_c_rusle": factor_c_medio,
        "mo_aporte_t": mo_total,
        "n_balance_kg": n_total,
        "taw_rotacion_mm_m": round(suelo_info["retencion_base_mm_m"] + bono_retencion, 1)
    }

def cobertura_fenologica_por_doy(doy: int, rot: dict, smap_raiz_pct: float):
    c1 = CULTIVOS_FAO[rot["ciclo_1"]]
    c2 = CULTIVOS_FAO[rot["ciclo_2"]]
    c3 = CULTIVOS_FAO[rot["ciclo_3"]]
    rastrojo_base = 8.0 if rot["quema_rastrojo"] else 26.0
    factor_hum = max(0.45, min(1.10, smap_raiz_pct / 70.0))

    if 135 <= doy <= 232:
        prog = (doy - 135) / 97.0
        curva = math.sin(prog * math.pi) ** 0.85
        kc_vigor = c1["kc_med"] / 1.20
        cob = rastrojo_base + (88.0 - rastrojo_base) * curva * kc_vigor * factor_hum
    elif 233 <= doy <= 253:
        cob = (15.0 if rot["quema_rastrojo"] else 38.0) * factor_hum
    elif 254 <= doy <= 334:
        prog = (doy - 254) / 80.0
        curva = math.sin(prog * math.pi) ** 0.85
        kc_vigor = c2["kc_med"] / 1.20
        cob = rastrojo_base + (86.0 - rastrojo_base) * curva * kc_vigor * factor_hum
    else:
        if rot["ciclo_3"] == "barbecho":
            cob = (9.0 if rot["quema_rastrojo"] else 22.0) * max(0.5, smap_raiz_pct / 80.0)
        else:
            kc_vigor = c3["kc_med"] / 1.15
            cob = (62.0 + 22.0 * kc_vigor) * max(0.65, factor_hum)

    cob_final = round(float(max(6.0, min(96.0, cob))), 1)
    ndvi_final = round(float(0.12 + (cob_final / 100.0) * 0.72), 2)
    return cob_final, ndvi_final

def procesar_ventana_temporal(df: pd.DataFrame, fecha_ini: str, fecha_fin: str,
                              agrupacion: str, pendiente_pct: float,
                              suelo_info: dict, lista_rotaciones: list,
                              cambio_lluvia_pct: float = 0.0, cambio_temp_c: float = 0.0):
    sub = df.loc[fecha_ini:fecha_fin].copy()
    if sub.empty:
        sub = df.tail(90).copy()

    sub["PRECTOTCORR"] = (sub["PRECTOTCORR"] * (1.0 + cambio_lluvia_pct / 100.0)).clip(lower=0.0)
    sub["T2M_MAX"] = sub["T2M_MAX"] + cambio_temp_c
    sub["T2M_MIN"] = sub["T2M_MIN"] + cambio_temp_c
    sub["T2M"] = sub["T2M"] + cambio_temp_c

    if agrupacion == "semanas":
        grp = sub.groupby(sub.index.to_period("W"))
        etiquetas = [str(p.start_time.strftime("%Y-%m-%d")) for p in grp.groups.keys()]
        doys = [int(p.start_time.dayofyear) for p in grp.groups.keys()]
    elif agrupacion == "meses":
        grp = sub.groupby(sub.index.to_period("M"))
        etiquetas = [str(p.start_time.strftime("%Y-%m")) for p in grp.groups.keys()]
        doys = [int(p.start_time.dayofyear) + 14 for p in grp.groups.keys()]
    elif agrupacion == "anios":
        grp = sub.groupby(sub.index.to_period("Y"))
        etiquetas = [str(p) for p in grp.groups.keys()]
        doys = [195 for _ in grp.groups.keys()]
    else:
        grp = None
        etiquetas = [d.strftime("%Y-%m-%d") for d in sub.index]
        doys = [int(d.dayofyear) for d in sub.index]

    if grp is not None:
        lluvia_s = [round(float(x), 1) for x in grp["PRECTOTCORR"].sum()]
        lluvia_max_dia = [round(float(x), 1) for x in grp["PRECTOTCORR"].max()]
        smap_raiz_s = [round(float(x * 100.0), 1) for x in grp["GWETROOT"].mean()]
        smap_sup_s = [round(float(x * 100.0), 1) for x in grp["GWETTOP"].mean()]
        radiacion_s = [round(float(x), 2) for x in grp["ALLSKY_SFC_SW_DWN"].mean()]
        tmax_s = [round(float(x), 1) for x in grp["T2M_MAX"].max()]
        tmin_s = [round(float(x), 1) for x in grp["T2M_MIN"].min()]
        rh_s = [round(float(x), 1) for x in grp["RH2M"].mean()]
    else:
        lluvia_s = [round(float(x), 1) for x in sub["PRECTOTCORR"]]
        lluvia_max_dia = lluvia_s
        smap_raiz_s = [round(float(x * 100.0), 1) for x in sub["GWETROOT"]]
        smap_sup_s = [round(float(x * 100.0), 1) for x in sub["GWETTOP"]]
        radiacion_s = [round(float(x), 2) for x in sub["ALLSKY_SFC_SW_DWN"]]
        tmax_s = [round(float(x), 1) for x in sub["T2M_MAX"]]
        tmin_s = [round(float(x), 1) for x in sub["T2M_MIN"]]
        rh_s = [round(float(x), 1) for x in sub["RH2M"]]

    factor_ls_medio = 0.05 if pendiente_pct < 1.0 else max(0.15, (pendiente_pct / 9.0) ** 1.3)
    factor_k = suelo_info["factor_k_rusle"]

    series_por_rotacion = {}
    for rot in lista_rotaciones:
        p_rot = calcular_parametros_rotacion(rot, suelo_info)
        factor_c = p_rot["factor_c_rusle"]
        cap_max = p_rot["taw_rotacion_mm_m"]

        cobertura_serie, ndvi_serie, retencion_serie, erosion_serie = [], [], [], []

        for doy_i, p_acum, p_pico, sm_r in zip(doys, lluvia_s, lluvia_max_dia, smap_raiz_s):
            cob_val, ndvi_val = cobertura_fenologica_por_doy(doy_i, rot, sm_r)
            eficiencia_conservacion = 0.86 if rot["quema_rastrojo"] else (0.94 + 0.06 * (cob_val / 100.0))
            agua_mm = round(min(cap_max, cap_max * (sm_r / 100.0) * eficiencia_conservacion), 1)

            if p_pico < 1.5 or pendiente_pct < 0.5:
                ero_val = 0.0
            else:
                desproteccion_dia = max(0.04, (1.0 - cob_val / 105.0) * (factor_c / 0.32))
                r_erosividad = (p_pico * 1.40 + p_acum * 0.12) * ((sm_r / 100.0) ** 1.2)
                ero_val = min(100.0, r_erosividad * (factor_k / 0.28) * factor_ls_medio * desproteccion_dia)

            cobertura_serie.append(cob_val)
            ndvi_serie.append(ndvi_val)
            retencion_serie.append(agua_mm)
            erosion_serie.append(round(float(ero_val), 1))

        series_por_rotacion[rot["id"]] = {
            "cobertura_pct": cobertura_serie,
            "ndvi": ndvi_serie,
            "retencion_agua_mm": retencion_serie,
            "capacidad_max_mm_m": cap_max,
            "factor_c_rusle": factor_c,
            "erosion_pct": erosion_serie
        }

    resumen = {
        "fecha_inicio": sub.index.min().strftime("%Y-%m-%d"),
        "fecha_fin": sub.index.max().strftime("%Y-%m-%d"),
        "lluvia_acumulada_mm": round(float(sub["PRECTOTCORR"].sum()), 1),
        "lluvia_pico_mm": round(float(sub["PRECTOTCORR"].max()), 1),
        "smap_raiz_media_pct": round(float(sub["GWETROOT"].mean() * 100.0), 1),
        "radiacion_media_mj": round(float(sub["ALLSKY_SFC_SW_DWN"].mean()), 2),
        "temp_max_c": round(float(sub["T2M_MAX"].max()), 1),
        "temp_min_c": round(float(sub["T2M_MIN"].min()), 1)
    }

    hitos = [
        {
            "indice": int(np.argmax(lluvia_max_dia)) if lluvia_max_dia else 0,
            "fecha": etiquetas[int(np.argmax(lluvia_max_dia))] if etiquetas else resumen["fecha_fin"],
            "titulo_es": "Pico de Lluvia",
            "titulo_en": "Peak Rain",
            "valor": f"{max(lluvia_max_dia) if lluvia_max_dia else 0} mm"
        },
        {
            "indice": int(np.argmax(smap_raiz_s)) if smap_raiz_s else 0,
            "fecha": etiquetas[int(np.argmax(smap_raiz_s))] if etiquetas else resumen["fecha_fin"],
            "titulo_es": "Máx. Retención",
            "titulo_en": "Max Retention",
            "valor": f"{max(smap_raiz_s) if smap_raiz_s else 0}%"
        },
        {
            "indice": int(np.argmin(smap_raiz_s)) if smap_raiz_s else 0,
            "fecha": etiquetas[int(np.argmin(smap_raiz_s))] if etiquetas else resumen["fecha_inicio"],
            "titulo_es": "Mín. Humedad",
            "titulo_en": "Min Moisture",
            "valor": f"{min(smap_raiz_s) if smap_raiz_s else 0}%"
        }
    ]

    return {
        "resumen": resumen,
        "hitos": hitos,
        "series": {
            "etiquetas": etiquetas,
            "doys": doys,
            "lluvia_mm": lluvia_s,
            "lluvia_pico_mm": lluvia_max_dia,
            "smap_raiz_pct": smap_raiz_s,
            "smap_sup_pct": smap_sup_s,
            "radiacion_mj": radiacion_s,
            "tmax_c": tmax_s,
            "tmin_c": tmin_s,
            "rh_pct": rh_s,
            "por_rotacion": series_por_rotacion
        }
    }

def simular_rotaciones_multianual(df: pd.DataFrame, pendiente_pct: float, elevacion_m: float,
                                  suelo_info: dict, lista_rotaciones: list,
                                  cambio_lluvia_pct: float = 0.0, cambio_temp_c: float = 0.0,
                                  pesos: dict = None):
    if pesos is None:
        pesos = {"agua": 0.40, "suelo": 0.35, "ingreso": 0.25}

    df_eval = df.loc["2000-01-01":].copy()
    lluvia = (df_eval["PRECTOTCORR"] * (1.0 + cambio_lluvia_pct / 100.0)).clip(lower=0.0)
    tmed = df_eval["T2M"] + cambio_temp_c
    et0 = (0.0135 * (tmed + 17.78) * (df_eval["ALLSKY_SFC_SW_DWN"] / 2.45)).clip(2.0, 7.5)

    dias_torrenciales_anio = float((lluvia > 45.0).sum()) / max(len(df_eval.index.year.unique()), 1)
    anios = sorted(df_eval.index.year.unique())
    resultados = []

    for rot in lista_rotaciones:
        p_rot = calcular_parametros_rotacion(rot, suelo_info)
        c1, c2, c3 = p_rot["c1"], p_rot["c2"], p_rot["c3"]
        taw_mm_m = p_rot["taw_rotacion_mm_m"]

        anios_exitosos = 0
        estres_anual = []
        ahorro_evaporacion_c3 = 0.55 if c3["es_cobertura"] else (0.75 if not rot["quema_rastrojo"] else 1.0)

        for yr in anios:
            sub_p = lluvia[lluvia.index.year == yr]
            sub_et0 = et0[et0.index.year == yr]
            if len(sub_p) < 340:
                continue

            taw_1 = taw_mm_m * c1["zr_m"]
            raw_1 = c1["p_agot"] * taw_1
            dr = raw_1 * (0.25 if c3["es_cobertura"] else 0.50)
            etc_1, etc_adj_1 = 0.0, 0.0

            for d in range(135, 230):
                p_efec = sub_p.iloc[d] * (0.65 if rot["quema_rastrojo"] else 0.88)
                dia_c = d - 135
                kc = c1["kc_ini"] if dia_c < 22 else (c1["kc_med"] if dia_c < 72 else c1["kc_fin"])
                etc = sub_et0.iloc[d] * kc * (0.90 if not rot["quema_rastrojo"] else 1.05)
                ks = 1.0 if dr <= raw_1 else max(0.0, (taw_1 - dr) / ((1.0 - c1["p_agot"]) * taw_1))
                etc_adj = etc * ks
                dr = min(taw_1, max(0.0, dr - p_efec + etc_adj))
                if 40 <= dia_c <= 72:
                    etc_1 += etc
                    etc_adj_1 += etc_adj

            perdida_c1 = c1["ky_flor"] * max(0.0, 1.0 - (etc_adj_1 / max(etc_1, 1.0))) * 100.0

            taw_2 = taw_mm_m * c2["zr_m"]
            raw_2 = c2["p_agot"] * taw_2
            dr_2 = min(taw_2 * 0.6, dr * (taw_2 / max(taw_1, 1.0)))
            etc_2, etc_adj_2 = 0.0, 0.0

            for d in range(250, 330):
                p_efec = sub_p.iloc[d] * (0.68 if rot["quema_rastrojo"] else 0.90)
                dia_c = d - 250
                kc = c2["kc_ini"] if dia_c < 18 else (c2["kc_med"] if dia_c < 58 else c2["kc_fin"])
                etc = sub_et0.iloc[d] * kc * ahorro_evaporacion_c3
                ks = 1.0 if dr_2 <= raw_2 else max(0.0, (taw_2 - dr_2) / ((1.0 - c2["p_agot"]) * taw_2))
                etc_adj = etc * ks
                dr_2 = min(taw_2, max(0.0, dr_2 - p_efec + etc_adj))
                if 28 <= dia_c <= 55:
                    etc_2 += etc
                    etc_adj_2 += etc_adj

            perdida_c2 = c2["ky_flor"] * max(0.0, 1.0 - (etc_adj_2 / max(etc_2, 1.0))) * 100.0
            perdida_combinada = 0.58 * perdida_c1 + 0.42 * perdida_c2
            if (rot["ciclo_1"] == "cafe" or rot["ciclo_2"] == "cafe") and elevacion_m < 450:
                perdida_combinada += 24.0

            perdida_pct = min(100.0, perdida_combinada)
            estres_anual.append(round(float(perdida_pct), 1))
            if perdida_pct < 26.0:
                anios_exitosos += 1

        total_a = max(len(estres_anual), 1)
        exito_pct = round(100.0 * anios_exitosos / total_a, 1)

        factor_c = p_rot["factor_c_rusle"]
        riesgo_erosion = 0.0 if pendiente_pct < 0.5 else min(100.0, round((pendiente_pct / 28.0) * factor_c * (90.0 + dias_torrenciales_anio * 12.0), 1))

        n_neto = p_rot["n_balance_kg"]
        mo_neta = p_rot["mo_aporte_t"]

        s_agua = exito_pct
        s_suelo = min(100.0, max(10.0, 55.0 + n_neto * 0.3 + mo_neta * 3.5 - riesgo_erosion * 0.35))
        s_ingreso = min(100.0, round(exito_pct * 0.65 + (25.0 if rot["ciclo_3"] != "barbecho" else 8.0), 1))

        score_total = round(
            pesos["agua"] * s_agua +
            pesos["suelo"] * s_suelo +
            pesos["ingreso"] * s_ingreso, 1
        )

        resultados.append({
            "id": rot["id"],
            "nombre_es": rot["nombre_es"],
            "nombre_en": rot["nombre_en"],
            "confianza": rot.get("confianza", "Alta"),
            "calendario_es": {
                "ciclo_1": c1["nombre_es"],
                "ciclo_2": c2["nombre_es"],
                "ciclo_3": c3["nombre_es"]
            },
            "calendario_en": {
                "ciclo_1": c1["nombre_en"],
                "ciclo_2": c2["nombre_en"],
                "ciclo_3": c3["nombre_en"]
            },
            "factor_c_rusle": factor_c,
            "retencion_taw_mm_m": taw_mm_m,
            "score_multicriterio": score_total,
            "anios_exitosos": anios_exitosos,
            "total_anios": total_a,
            "exito_hidrico_pct": exito_pct,
            "riesgo_erosion_pct": riesgo_erosion,
            "balance_n_kg_ha": n_neto,
            "aporte_mo_t_ha": mo_neta,
            "meses_desnudo": rot["meses_desnudo"],
            "descripcion_es": rot["descripcion_es"],
            "descripcion_en": rot["descripcion_en"],
            "validacion_es": rot["validacion_es"],
            "validacion_en": rot["validacion_en"]
        })

    return resultados
