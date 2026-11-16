# main.py - Servidor Principal FastAPI (Canicula)
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from nasa_client import (
    obtener_series_nasa,
    obtener_transecto_y_malla_srtm,
    obtener_propiedades_suelo
)
from motor_agronomico import (
    analizar_tendencias_mann_kendall,
    generar_estrategias_desde_granos,
    procesar_ventana_temporal,
    simular_rotaciones_multianual
)

app = FastAPI(title="Canícula — NASA Spatial Agro-Climatic Decision System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def servir_interfaz():
    return FileResponse("static/index.html")

@app.get("/api/analizar")
def analizar_ubicacion(
    lat: float = Query(13.4850),
    lon: float = Query(-86.5820),
    nombre_lugar: str = Query("Somoto, Madriz"),
    fecha_inicio: str = Query("2020-10-15"),
    fecha_fin: str = Query("2020-12-05"),
    agrupacion: str = Query("dias"),
    granos_seleccionados: str = Query("maiz,frijol,sorgo,canavalia"),
    cambio_lluvia: float = Query(0.0),
    cambio_temp: float = Query(0.0),
    w_agua: float = Query(0.40),
    w_suelo: float = Query(0.35),
    w_ingreso: float = Query(0.25)
):
    df_nasa, url_nasa_json = obtener_series_nasa(lat, lon, inicio="19980101", fin="20251231")
    relieve = obtener_transecto_y_malla_srtm(lat, lon)
    suelo = obtener_propiedades_suelo(lat, lon, relieve["elevacion_centro_m"], relieve["pendiente_pct"])
    tendencias_mk = analizar_tendencias_mann_kendall(df_nasa)

    lista_rot, validacion_rot = generar_estrategias_desde_granos(
        granos_seleccionados,
        pendiente_pct=relieve["pendiente_pct"],
        elevacion_m=relieve["elevacion_centro_m"]
    )

    ventana = procesar_ventana_temporal(
        df_nasa,
        fecha_ini=fecha_inicio,
        fecha_fin=fecha_fin,
        agrupacion=agrupacion,
        pendiente_pct=relieve["pendiente_pct"],
        suelo_info=suelo,
        lista_rotaciones=lista_rot,
        cambio_lluvia_pct=cambio_lluvia,
        cambio_temp_c=cambio_temp
    )

    suma_w = max(w_agua + w_suelo + w_ingreso, 0.01)
    pesos = {
        "agua": w_agua / suma_w,
        "suelo": w_suelo / suma_w,
        "ingreso": w_ingreso / suma_w
    }
    rotaciones = simular_rotaciones_multianual(
        df_nasa,
        pendiente_pct=relieve["pendiente_pct"],
        elevacion_m=relieve["elevacion_centro_m"],
        suelo_info=suelo,
        lista_rotaciones=lista_rot,
        cambio_lluvia_pct=cambio_lluvia,
        cambio_temp_c=cambio_temp,
        pesos=pesos
    )

    return {
        "ubicacion": {
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "nombre": nombre_lugar,
            "es_cuerpo_agua": relieve["es_cuerpo_agua"],
            "elevacion_m": relieve["elevacion_centro_m"],
            "pendiente_pct": relieve["pendiente_pct"],
            "pendiente_grados": relieve["pendiente_grados"],
            "pendiente_max_pct": relieve["pendiente_max_pct"]
        },
        "suelo": suelo,
        "tendencias_climaticas": tendencias_mk,
        "validacion_rotacion": validacion_rot,
        "url_auditoria_nasa": url_nasa_json,
        "ventana": ventana,
        "transecto": relieve,
        "rotaciones": rotaciones
    }

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=puerto)
