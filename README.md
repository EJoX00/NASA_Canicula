# NASA_Canicula

# 🌾 Canícula — NASA Agro-Climatic & Topographic Decision-Support Tool

[![NASA Space Apps Challenge](https://img.shields.io/badge/NASA_Space_Apps-Field_Shift-bf432a?style=for-the-badge)](https://www.spaceappschallenge.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-1f569c?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MapLibre GL](https://img.shields.io/badge/MapLibre_3D-SRTM_DEM-2d6a4f?style=for-the-badge)](https://maplibre.org/)

> **English Abstract (For Global Judges):**  
> **Canícula** is an explainable, physics-driven geospatial decision-support system designed for the *Field Shift: Adapting Farms with NASA Data* challenge. Built with a farmer-centered approach, it translates 27 years of NASA Earth observations (**NASA POWER, GPM IMERG, SMAP L4, MODIS NDVI, and SRTM 30m DEM**) and soil physical properties (**ISRIC SoilGrids v2.0 / USDA**) into actionable crop rotation strategies. Instead of using opaque "black-box" machine learning models that lack farm-level ground truth, **Canícula** couples a **3D/2D Topographic Relief Visor** with deterministic **FAO-56 water balance**, **FAO-33 yield-stress response ($K_y$)**, **RUSLE slope erosion modeling**, and **Mann-Kendall / Sen's slope climate trend analysis** to help farmers and agricultural technicians build long-term soil health and drought resilience anywhere in the world.

---

## 📌 1. Problemática y Propósito

Los productores agrícolas —especialmente en regiones vulnerables como el Corredor Seco Centroamericano (con caso piloto en Somoto, Madriz, Nicaragua) y zonas de ladera a nivel global— enfrentan lluvias cada vez más irregulares, canículas prolongadas (sequías intraestivales en julio–agosto), olas de calor y degradación severa del suelo por erosión hídrica.

Aunque existen terabytes de datos satelitales de la NASA, rara vez están traducidos a un formato auditable y comprensible en campo. **Canícula** cierra esta brecha permitiendo al productor y al técnico agrícola:
1. **Explorar cualquier coordenada o finca del mundo en 3D y 2D** (incluyendo localización directa por GPS desde dispositivos móviles).
2. **Medir y visualizar 5 variables biofísicas críticas en tiempo real** sin descargar archivos pesados:
   * **1. Cobertura Vegetal (% e Índice NDVI)** según la etapa fenológica real del calendario agrícola.
   * **2. Tipo de Suelo (Clasificación Textural USDA)** con fracciones de arcilla, arena, limo y materia orgánica.
   * **3. Pendiente Real del Terreno (% y grados)** derivada del modelo de elevación digital SRTM.
   * **4. Retención Hídrica del Suelo ($\text{mm/m}$ y % SMAP)** en la zona radicular.
   * **5. Radiación Solar Incidente ($\text{MJ/m}^2/\text{día}$) y Temperatura Superficial ($^\circ\text{C}$)**.
3. **Evaluar y diseñar estrategias de rotación de cultivos** (exigiendo un mínimo estricto de $\ge 2$ especies distintas para romper el monocultivo) combinando granos básicos (**Maíz, Frijol Común, Sorgo, Caupí**), sistemas perennes (**Café Arábica**) y leguminosas de cobertura/abono verde (**Canavalia, Mucuna**).

---

## 🛰️ 2. Fuentes de Datos Satelitales (NASA) y Geofísicos

El sistema opera **100% en memoria RAM** mediante llamadas a APIs públicas oficiales (sin requerir credenciales privadas ni almacenar gigabytes en disco):

| Misión / Fuente Oficial | Producto / Endpoint | Variables Extraídas | Uso en el Motor de **Canícula** |
| :--- | :--- | :--- | :--- |
| **NASA POWER** (*Agroclimatology*) | `/api/temporal/daily/point` (Fusión GPM IMERG + MERRA-2, 1998–2025) | `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`, `T2M_MAX`, `T2M_MIN`, `T2M`, `RH2M`, `WS2M` | Cálculo de evapotranspiración potencial ($ET_0$), balance hídrico diario FAO-56, energía erosiva de lluvia y tendencias Mann-Kendall. |
| **NASA SMAP / GLDAS** | `GWETROOT` ($0-100\text{ cm}$), `GWETTOP` ($0-5\text{ cm}$) y `SMAP_L4` vía NASA GIBS | Fracción de humedad en zona de raíces y superficial ($\%$) | Estado hídrico real del suelo, detección de rachas secas de canícula y saturación por lluvias torrenciales. |
| **NASA MODIS** | `MODIS_Terra_NDVI_8Day` y `Land_Surface_Temp_Day` (NASA GIBS WMTS) | Índice de Vegetación (`NDVI`) y Temperatura Superficial (`LST`) | Superposición satelital global/nacional sincronizada por fecha y validación de meses con suelo descubierto. |
| **USGS / NASA SRTM** | AWS Terrarium DEM ($30\text{ m}$) y Open-Meteo Elevation API | Elevación ($Z$) y derivadas espaciales ($\partial Z/\partial x, \partial Z/\partial y$) | Levantamiento topográfico 3D, corte longitudinal de $6\text{ km}$, máscara automática de cuerpos de agua y factor topográfico $LS$. |
| **ISRIC SoilGrids** | SoilGrids v2.0 REST API ($250\text{ m}$) + Zonificación Edafológica USDA | `clay`, `sand`, `silt`, `soc` ($0-5\text{ cm}$) | Clasificación textural USDA, capacidad de campo ($\theta_{FC}$), punto de marchitez ($\theta_{WP}$), reserva $TAW$ ($\text{mm/m}$) y factor de erodabilidad $K$. |

---

## 🧮 3. Motor Matemático y Agronómico Explicable

Para evitar la falsa confianza de modelos de Inteligencia Artificial opacos sin datos de cosecha por parcela, **Canícula** implementa cuatro módulos deterministas y auditables:

### 3.1. Tendencias Climáticas No Paramétricas (Mann-Kendall y Pendiente de Sen)
Sobre la serie histórica de 25+ años se evalúa la significancia estadística ($\tau$ de Kendall y valor $p$) y la magnitud de cambio por década (**Pendiente de Sen**) en:
* Duración de la canícula (máxima racha de días consecutivos con lluvia $< 2.0\text{ mm}$ entre el 1 de julio y el 20 de agosto).
* Precipitación anual acumulada ($\text{mm/década}$).
* Anomalía térmica media ($^\circ\text{C/década}$).

### 3.2. Balance Hídrico por Etapa Fenológica (FAO-56) y Sensibilidad al Estrés (FAO-33)
Para cada rotación candidata se simulan los **3 ciclos agrícolas del año** (*Primera: Mayo–Agosto*, *Postrera: Septiembre–Noviembre*, *Apante/Seca: Diciembre–Abril*) a lo largo de los últimos 25 años históricos:

$$D_{r,i} = D_{r,i-1} - P_{\text{efectiva},i} + ET_{c\text{ adj},i} + DP_i$$

$$K_{s,i} = \frac{TAW - D_{r,i}}{(1 - p) \cdot TAW} \quad \text{cuando } D_{r,i} > RAW$$

$$1 - \frac{Y_a}{Y_m} = K_y \left( 1 - \frac{ET_{c\text{ adj}}}{ET_c} \right)$$

Esto entrega una distribución probabilística real (ej. *"Éxito hídrico en 21 de 25 años [84%]"*) en lugar de una predicción arbitraria.

### 3.3. Susceptibilidad a la Erosión Hídrica en Ladera (Modelo RUSLE)
Cada celda topográfica combina la erosividad de la lluvia diaria ($R$), la erodabilidad según textura y materia orgánica del suelo ($K$), el factor de longitud e inclinación de la pendiente SRTM ($LS$) y el factor de protección vegetal de la rotación ($C$):

$$A_{\text{rel}} = f(R_{\text{IMERG}} \cdot K_{\text{SoilGrids}} \cdot LS_{\text{SRTM}} \cdot C_{\text{Rotación}})$$

### 3.4. Regla Estricta de Rotación y Análisis Multicriterio
* **Validación de diversidad ($\ge 2$ cultivos):** Si el usuario selecciona un único cultivo, el sistema advierte que no existe rotación sino monocultivo continuo y cuantifica el agotamiento de nitrógeno ($\text{kg N/ha}$) y pérdida de suelo.
* **Ponderación centrada en el productor:** Permite ajustar las prioridades del agricultor ($w_{\text{Agua}}, w_{\text{Suelo}}, w_{\text{Estabilidad}}$) y simular escenarios climáticos extremos ($\pm 40\%$ de lluvia y $+3.5\ ^\circ\text{C}$ de temperatura).

---

## 🗂️ 4. Estructura del Proyecto

```text
canicula-nasa/
├── config.py              # Parámetros auditados FAO-56 (Kc, Zr, p), FAO-33 (Ky), N fijado y Factor C RUSLE
├── nasa_client.py         # Cliente en RAM para NASA POWER, SRTM DEM (transecto y malla 7x7) e ISRIC SoilGrids
├── motor_agronomico.py    # Mann-Kendall/Sen, validador de granos (>=2), fenología diaria y balance FAO-56
├── main.py                # Servidor FastAPI con endpoints REST y servicio directo del visor 3D
├── requirements.txt       # Dependencias ligeras de Python para producción
├── Dockerfile             # Contenedor listo para despliegue en la nube
└── static/
    └── index.html         # Interfaz 3D/2D (MapLibre GL JS + NASA GIBS + Chart.js + Modo Crema/Carbón + ES/EN)
