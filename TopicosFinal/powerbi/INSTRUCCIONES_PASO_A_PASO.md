# Instrucciones Paso a Paso - Power BI Canal de Panamá

## Tabla de Contenidos
1. [Configuración Inicial](#1-configuración-inicial)
2. [Importación de Datos](#2-importación-de-datos)
3. [Transformaciones con Power Query](#3-transformaciones-con-power-query)
4. [Creación del Modelo de Datos](#4-creación-del-modelo-de-datos)
5. [Creación de Medidas DAX](#5-creación-de-medidas-dax)
6. [Creación de Visualizaciones](#6-creación-de-visualizaciones)
7. [Aplicación del Tema Institucional](#7-aplicación-del-tema-institucional)
8. [Publicación y Compartir](#8-publicación-y-compartir)

---

## 1. Configuración Inicial

### 1.1 Abrir Power BI Desktop
1. Ejecutar Power BI Desktop
2. Seleccionar "Nuevo" para crear un reporte en blanco

### 1.2 Configurar opciones regionales
1. Ir a **Archivo** → **Opciones y configuración** → **Opciones**
2. En "Configuración regional actual", seleccionar **Español (México)** o **Español (España)**
3. Hacer clic en **Aceptar**

---

## 2. Importación de Datos

### 2.1 Importar fact_transitos.csv
1. En la pestaña **Inicio**, hacer clic en **Obtener datos**
2. Seleccionar **Texto/CSV**
3. Navegar a: `C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\data\`
4. Seleccionar `fact_transitos.csv`
5. En "Origen del archivo", verificar que esté en **65001: Unicode (UTF-8)**
6. Hacer clic en **Cargar**

### 2.2 Importar predicciones_2026.csv
1. Repetir pasos 2.1.1 - 2.1.5
2. Seleccionar `predicciones_2026.csv`
3. Hacer clic en **Cargar**

### 2.3 Importar clusters_paises.csv
1. Repetir pasos 2.1.1 - 2.1.5
2. Seleccionar `clusters_paises.csv`
3. **Importante**: En "Origen del archivo", cambiar a **28591: ISO-8859-1 (Latin1)**
4. Hacer clic en **Cargar**

---

## 3. Transformaciones con Power Query

### 3.1 Transformar fact_transitos
1. En el panel derecho, bajo "Consultas", clic derecho en `fact_transitos`
2. Seleccionar **Editar**
3. En el Editor de Power Query:

#### 3.1.1 Cambiar tipos de datos
- Seleccionar columna `fecha` → Cambiar tipo → **Fecha**
- Seleccionar columna `segmento` → Cambiar tipo → **Texto**
- Seleccionar columna `transitos` → Cambiar tipo → **Número entero**
- Seleccionar columna `ingresos` → Cambiar tipo → **Número entero**
- Seleccionar columna `toneladas` → Cambiar tipo → **Número entero**
- Seleccionar columna `volumen` → Cambiar tipo → **Número entero**

#### 3.1.2 Agregar columnas calculadas
1. Ir a **Agregar columna** → **Columna personalizada**
2. Nombre: `anio`
3. Fórmula: `Date.Year([fecha])`
4. Aceptar

3. Repetir para crear:
   - `mes_num`: `Date.Month([fecha])`
   - `mes_nombre`: `Date.ToText([fecha], "MMMM", "es-ES")`
   - `trimestre`: `Date.QuarterOfYear([fecha])`
   - `fecha_key`: `Date.ToText([fecha], "yyyyMMdd")`

4. **Guardar y cerrar**

### 3.2 Transformar clusters_paises
1. Clic derecho en `clusters_paises` → **Editar**
2. Aplicar las transformaciones de codificación ya realizadas en el archivo
3. Verificar que los nombres de países aparecen correctamente:
   - Japón (no JapÃ³n)
   - Perú (no PerÃº)
   - México (no MÃ©xico)
   - Canadá (no CanadÃ¡)
   - Panamá (no PanamÃ¡)
   - España (no EspaÃ±a)
   - Países Bajos (no PaÃ­ses Bajos)

### 3.3 Transformar predicciones_2026
1. Clic derecho en `predicciones_2026` → **Editar**
2. Cambiar tipos de datos:
   - `fecha` → **Fecha**
   - `segmento` → **Texto**
   - `pred_transitos` → **Número decimal**
   - `pred_ingresos` → **Número decimal**
   - `limite_inferior` → **Número decimal**
   - `limite_superior` → **Número decimal**
   - `modelo` → **Texto**

3. Agregar columnas: `anio`, `mes_num`, `mes_nombre`, `trimestre`

4. **Guardar y cerrar**

---

## 4. Creación del Modelo de Datos

### 4.1 Abrir la vista de modelo
1. Hacer clic en el icono **Modelo** en el panel izquierdo

### 4.2 Crear tabla Dim_Tiempo
1. Ir a **Tabla** → **Nueva tabla** → **Tabla de fechas**
2. Power BI detectará automáticamente la columna de fechas
3. O crear manualmente:
   ```
   Dim_Tiempo = 
   CALENDARAUTO()
   ```
4. Agregar columnas calculadas en la tabla:
   ```dax
   anio = YEAR(Dim_Tiempo[Date])
   mes_num = MONTH(Dim_Tiempo[Date])
   mes_nombre = FORMAT(Dim_Tiempo[Date], "MMMM", "es-ES")
   trimestre = QUARTER(Dim_Tiempo[Date])
   fecha_key = FORMAT(Dim_Tiempo[Date], "yyyyMMdd")
   es_prediccion = Dim_Tiempo[Date] >= DATE(2026,1,1)
   ```

### 4.3 Crear relaciones
1. En la vista de modelo, arrastrar:
   - `fact_transitos[fecha]` → `Dim_Tiempo[Date]` (relación 1:N)
   - `predicciones_2026[fecha]` → `Dim_Tiempo[Date]` (relación 1:N)

### 4.4 Marcar como tabla de fechas
1. Clic derecho en `Dim_Tiempo` → **Marcar como tabla de fechas**
2. Seleccionar columna `Date`

### 4.5 Organizar tablas
1. Mover `Dim_Tiempo` a la izquierda del modelo
2. Mover `fact_transitos` al centro (tabla de hechos)
3. Mover `clusters_paises` y `predicciones_2026` a la derecha

---

## 5. Creación de Medidas DAX

### 5.1 Crear nueva tabla de medidas (recomendado)
1. Clic derecho en el modelo → **Crear nueva tabla**
2. Nombre: `Medidas`
3. En la barra de fórmulas, pegar las medidas del archivo `medidas_dax.txt`

### 5.2 Medidas principales a crear
Se recomienda crear las siguientes medidas en una tabla llamada "Medidas Canal":

#### Medidas de Tránsito
- `Total_Transitos`
- `Transitos_NeoPanamax`
- `Transitos_Panamax_AltoCalado`
- `Promedio_Transitos_Mensual`
- `Variacion_Transitos`

#### Medidas de Ingresos
- `Total_Ingresos`
- `Ingresos_Millones_USD`
- `Variacion_Ingresos`

#### Medidas de Predicción
- `Prediccion_Transitos_2026`
- `Prediccion_Ingresos_2026`
- `Ancho_Banda_Prediccion`

#### Medidas de Comparación
- `Cambio_Prediccion_Pct`
- `Crecimiento_Anual`

### 5.3 Implementar medidas paso a paso
1. Clic derecho en **Medidas** → **Nueva medida**
2. Escribir la fórmula DAX
3. Presionar **Enter**
4. Repetir para cada medida

---

## 6. Creación de Visualizaciones

### 6.1 Dashboard Executive Summary
**Objetivo**: Vista gerencial de alto nivel

#### Tarjetas (Cards)
1. Insertar visual **Tarjeta**
2. Arrastrar `Total_Transitos`
3. Repetir con:
   - `Total_Ingresos` (formato: moneda USD)
   - `Prediccion_Transitos_2026`
   - `Variacion_Transitos` (formato: porcentaje)

#### Gráfico de líneas (Trend)
1. Insertar visual **Gráfico de líneas**
2. Eje X: `Dim_Tiempo[Date]` (mes/año)
3. Valores: `Total_Transitos`
4. Leyenda: `fact_transitos[segmento]`

#### Gráfico de columnas (Segmentos)
1. Insertar visual **Gráfico de columnas agrupadas**
2. Eje X: `Dim_Tiempo[anio]`
3. Valores: `Transitos_NeoPanamax`, `Transitos_Panamax_AltoCalado`
4. Usar mismo eje para ambos

### 6.2 Dashboard de Análisis Temporal
**Objetivo**: Análisis de tendencias y estacionalidad

#### Gráfico de área
1. Insertar visual **Gráfico de áreas**
2. Eje X: `Dim_Tiempo[mes_nombre]`
3. Valores: `Total_Transitos`
4. Segmentador: `Dim_Tiempo[anio]`

#### Mapa de calor (Matriz)
1. Insertar visual **Matriz**
2. Filas: `Dim_Tiempo[mes_nombre]`
3. Columnas: `Dim_Tiempo[anio]`
4. Valores: `Total_Transitos`

#### Gráfico de barras horizontales (Top países)
1. Insertar visual **Gráfico de barras**
2. Eje Y: `clusters_paises[pais]`
3. Valores: `clusters_paises[total]`
4. Ordenar: descendente

### 6.3 Dashboard de Predicciones
**Objetivo**: Comparación histórico vs predicción

#### Gráfico de líneas con predicción
1. Insertar visual **Gráfico de líneas**
2. Agregar serie "Histórico": `Total_Transitos`
3. Agregar serie "Predicción": `Prediccion_Transitos_2026`
4. Agregar línea de confianza inferior
5. Agregar línea de confianza superior

#### Tarjetas de comparación
- `Diferencia_Transitos_Pred_vs_Historico`
- `Cambio_Prediccion_Pct`
- `Incertidumbre_Prediccion`

### 6.4 Dashboard de Países/Clusters
**Objetivo**: Análisis geográfico del tráfico

#### Treemap de países
1. Insertar visual **Treemap**
2. Grupo: `clusters_paises[pais]`
3. Valores: `clusters_paises[total]`

#### Gráfico de clusters
1. Insertar visual **Gráfico circular**
2. Leyenda: `clusters_paises[cluster]`
2. Valores: `clusters_paises[total]`

#### Tabla de países
1. Insertar visual **Tabla**
2. Columnas: `pais`, `origen`, `destino`, `costa_a_costa`, `total`, `porcentaje`

---

## 7. Aplicación del Tema Institucional

### 7.1 Importar tema JSON
1. Ir a **Ver** → **Temas** → **Examinar temas**
2. Navegar a: `C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\powerbi\`
3. Seleccionar `theme_institucional.json`
4. Hacer clic en **Abrir**

### 7.2 Verificar aplicación del tema
1. El tema se aplicará automáticamente a todos los elementos
2. Colores institucionales:
   - Primary: #1F4E79 (azul oscuro)
   - Secondary: #2E75B6 (azul medio)
   - Accent: #5B9BD5 (azul claro)

---

## 8. Publicación y Compartir

### 8.1 Guardar el reporte
1. Ir a **Archivo** → **Guardar como**
2. Nombre: `Canal_Panama_Analytics.pbix`
3. Ubicación: `C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\powerbi\`

### 8.2 Publicar en Power BI Service (opcional)
1. Ir a **Inicio** → **Publicar**
2. Seleccionar destino: "Mi área de trabajo"
3. Hacer clic en **Publicar**
4. Iniciar sesión con cuenta de Power BI si es necesario

### 8.3 Programar actualización (opcional)
1. En Power BI Service, ir al dataset publicado
2. Seleccionar **Programar actualización**
3. Configurar credenciales de origen de datos
4. Establecer frecuencia de actualización

---

## Anexo: Estructura de Carpetas Esperada

```
TopicosFinal\
├── data\
│   ├── fact_transitos.csv          (datos históricos)
│   ├── predicciones_2026.csv      (predicciones ML)
│   ├── clusters_paises.csv         (clusters de países)
│   └── metricas_modelo.json        (métricas del modelo)
├── powerbi\
│   ├── Canal_Panama_Analytics.pbix (reporte Power BI)
│   ├── theme_institucional.json    (tema de colores)
│   ├── queries_power_query.m       (código M)
│   ├── medidas_dax.txt             (medidas DAX)
│   └── INSTRUCCIONES_PASO_A_PASO.md
└── ML\
    ├── train.py                    (entrenamiento)
    ├── predict_2026.py             (predicciones)
    └── models\                     (modelos guardados)
```

---

## Troubleshooting Común

### Problema: Caracteres encoding incorrectos
**Solución**: Al importar CSV, seleccionar codificación correcta (UTF-8 o Latin1)

### Problema: Relaciones no se crean automáticamente
**Solución**: Crear manualmente en vista de modelo arrastrando columnas

### Problema: Medidas DAX dan error
**Solución**: Verificar que los nombres de tablas y columnas coincidan exactamente

### Problema: Tema no se aplica
**Solución**: Confirmar que el archivo JSON esté bien formateado

---

## Contacto y Soporte
Para soporte adicional, consultar la documentación en:
- Wiki del proyecto
- Archivos README.md en cada carpeta
