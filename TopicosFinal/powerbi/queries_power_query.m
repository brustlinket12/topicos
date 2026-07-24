// ============================================================
// POWER QUERY M - Consultas de Transformación
// Proyecto: Análisis del Canal de Panamá
// ============================================================

// ------------------------------------------------------------
// 1. Función para detectar codificación y limpiar texto
// ------------------------------------------------------------
let
    LimpiarTexto = (texto as text) as text =>
        let
            // Reemplazar caracteresproblemáticos comunes
           替换 = Text.Replace(texto, "Ã¡", "á"),
           替换 = Text.Replace(替换, "Ã©", "é"),
           替换 = Text.Replace(替换, "Ã­", "í"),
           替换 = Text.Replace(替换, "Ã³", "ó"),
           替换 = Text.Replace(替换, "Ãº", "ú"),
           替换 = Text.Replace(替换, "Ã±", "ñ"),
           替换 = Text.Replace(替换, "Â¡", "¡"),
           替换 = Text.Replace(替换, "Â¿", "¿"),
           替换 = Text.Replace(替换, "paÃ­ses", "países"),
           替换 = Text.Replace(替换, "PaÃ­ses", "Países"),
           替换 = Text.Replace(替换, "JapÃ³n", "Japón"),
           替换 = Text.Replace(替换, "PerÃº", "Perú"),
           替换 = Text.Replace(替换, "MÃ©xico", "México"),
           替换 = Text.Replace(替换, "CanadÃ¡", "Canadá"),
           替换 = Text.Replace(替换, "PanamÃ¡", "Panamá"),
           替换 = Text.Replace(替换, "EspaÃ±a", "España")
        in
           替换
in
    LimpiarTexto

// ------------------------------------------------------------
// 2. Cargar y transformar fact_transitos
// ------------------------------------------------------------
let
    // Origen del archivo CSV
    Origen = Csv.Document(
        File.Contents("C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\data\fact_transitos.csv"),
        [
            Delimiter = ",",
            Encoding = TextEncoding.UTF8,
            QuoteStyle = QuoteStyle.None
        ]
    ),

    // Promover encabezados
    PrimeraFilaComoEncabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    // Cambiar tipos de datos
    TipoCambiado = Table.TransformColumnTypes(
        PrimeraFilaComoEncabezados,
        {
            {"fecha", type date},
            {"segmento", type text},
            {"transitos", Int64.Type},
            {"ingresos", Int64.Type},
            {"toneladas", Int64.Type},
            {"volumen", Int64.Type}
        }
    ),

    // Agregar columna de año
    AgregarAnio = Table.AddColumn(TipoCambiado, "anio", each Date.Year([fecha]), Int64.Type),

    // Agregar columna de mes
    AgregarMes = Table.AddColumn(AgregarAnio, "mes_num", each Date.Month([fecha]), Int64.Type),

    // Agregar nombre del mes
    AgregarNombreMes = Table.AddColumn(
        AgregarMes,
        "mes_nombre",
        each Date.ToText([fecha], "MMMM", "es-ES"),
        type text
    ),

    // Agregar trimestre
    AgregarTrimestre = Table.AddColumn(
        AgregarNombreMes,
        "trimestre",
        each Date.QuarterOfYear([fecha]),
        Int64.Type
    ),

    // Agregar fecha completa como clave
    AgregarFechaKey = Table.AddColumn(
        AgregarTrimestre,
        "fecha_key",
        each Date.ToText([fecha], "yyyyMMdd"),
        type text
    )
in
    AgregarFechaKey

// ------------------------------------------------------------
// 3. Cargar y transformar clusters_paises
// ------------------------------------------------------------
let
    // Origen del archivo CSV con codificación Latin1 (ISO-8859-1)
    Origen = Csv.Document(
        File.Contents("C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\data\clusters_paises.csv"),
        [
            Delimiter = ",",
            Encoding = 28591, // Latin1 ISO-8859-1
            QuoteStyle = QuoteStyle.None
        ]
    ),

    // Promover encabezados
    PrimeraFilaComoEncabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    // Cambiar tipos de datos
    TipoCambiado = Table.TransformColumnTypes(
        PrimeraFilaComoEncabezados,
        {
            {"pais", type text},
            {"origen", Int64.Type},
            {"destino", Int64.Type},
            {"costa_a_costa", type number},
            {"total", Int64.Type},
            {"total_menos_cc", Int64.Type},
            {"porcentaje", type text},
            {"cluster", Int64.Type},
            {"distancia_centroide", type number}
        }
    ),

    // Limpiar columna pais (remover caracteres encoding problemáticos)
    PaisLimpio = Table.TransformColumns(
        TipoCambiado,
        {
            {"pais", each Text.Replace(_, "PaÃ­ses", "Países"), type text}
        }
    )
in
    PaisLimpio

// ------------------------------------------------------------
// 4. Cargar y transformar predicciones_2026
// ------------------------------------------------------------
let
    // Origen del archivo CSV
    Origen = Csv.Document(
        File.Contents("C:\Users\Propietario\Music\Proyectos\topicos\TopicosFinal\data\predicciones_2026.csv"),
        [
            Delimiter = ",",
            Encoding = TextEncoding.UTF8,
            QuoteStyle = QuoteStyle.None
        ]
    ),

    // Promover encabezados
    PrimeraFilaComoEncabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    // Cambiar tipos de datos
    TipoCambiado = Table.TransformColumnTypes(
        PrimeraFilaComoEncabezados,
        {
            {"fecha", type date},
            {"segmento", type text},
            {"pred_transitos", type number},
            {"pred_ingresos", type number},
            {"limite_inferior", type number},
            {"limite_superior", type number},
            {"modelo", type text}
        }
    ),

    // Agregar columnas de año y mes
    AgregarAnio = Table.AddColumn(TipoCambiado, "anio", each Date.Year([fecha]), Int64.Type),
    AgregarMes = Table.AddColumn(AgregarAnio, "mes_num", each Date.Month([fecha]), Int64.Type),

    // Agregar nombre del mes
    AgregarNombreMes = Table.AddColumn(
        AgregarMes,
        "mes_nombre",
        each Date.ToText([fecha], "MMMM", "es-ES"),
        type text
    ),

    // Agregar trimestre
    AgregarTrimestre = Table.AddColumn(
        AgregarNombreMes,
        "trimestre",
        each Date.QuarterOfYear([fecha]),
        Int64.Type
    ),

    // Agregar indicador de predicción
    AgregarEsPrediccion = Table.AddColumn(
        AgregarTrimestre,
        "es_prediccion",
        each true,
        type bool
    )
in
    AgregarEsPrediccion

// ------------------------------------------------------------
// 5. Combinar datos históricos con predicciones
// ------------------------------------------------------------
let
    // Cargar tabla de tránsitos históricos
    Historial = Table.FromRows(
        {
            {Date.From("2020-01-01"), "NeoPanamax", 308, 135551279, 23811798, 9311252},
            {Date.From("2020-02-01"), "NeoPanamax", 268, 112186169, 19811487, 8662008}
            -- ... (resto de datos históricos)
        },
        {"fecha", "segmento", "transitos", "ingresos", "toneladas", "volumen"}
    ),

    // Cargar tabla de predicciones
    Predicciones = Table.FromRows(
        {
            {Date.From("2026-01-01"), "Panamax_AltoCalado", 712.29, 161179631.79, 0, 0},
            {Date.From("2026-02-01"), "Panamax_AltoCalado", 705.89, 151743458.68, 0, 0}
            -- ... (resto de predicciones)
        },
        {"fecha", "segmento", "transitos", "ingresos", "toneladas", "volumen"}
    ),

    // Agregar columna indicador a cada tabla
    HistorialConIndicador = Table.AddColumn(Historial, "tipo_dato", each "Histórico", type text),
    PrediccionesConIndicador = Table.AddColumn(Predicciones, "tipo_dato", each "Predicción", type text),

    // Combinar tablas
    Combinada = Table.Combine({HistorialConIndicador, PrediccionesConIndicador})
in
    Combinada

// ------------------------------------------------------------
// 6. Crear tabla de dimensiones de tiempo
// ------------------------------------------------------------
let
    // Generar rango de fechas completas
    FechaMin = #date(2020, 1, 1),
    FechaMax = #date(2026, 12, 1),

    // Función recursiva para generar lista de fechas
    GenerarFechas = List.Generate(
        () => FechaMin,
        each _ <= FechaMax,
        each Date.AddMonths(_, 1)
    ),

    // Convertir a tabla
    TablaFechas = Table.FromList(
        GenerarFechas,
        Splitter.SplitByNothing(),
        {"fecha"},
        null,
        ExtraValues.Error
    ),

    // Renombrar columna
    TablaFechas2 = Table.RenameColumns(TablaFechas, {{"Column1", "fecha"}}),

    // Agregar columnas de tiempo
    DimTiempo = Table.TransformColumns(
        TablaFechas2,
        {
            {"fecha", each Date.From(_), type date}
        }
    ),

    // Agregar año
    AgregarAnio = Table.AddColumn(DimTiempo, "anio", each Date.Year([fecha]), Int64.Type),

    // Agregar mes numérico
    AgregarMes = Table.AddColumn(AgregarAnio, "mes_num", each Date.Month([fecha]), Int64.Type),

    // Agregar nombre del mes en español
    AgregarNombreMes = Table.AddColumn(
        AgregarMes,
        "mes_nombre",
        each Date.ToText([fecha], "MMMM", "es-ES"),
        type text
    ),

    // Agregar trimestre
    AgregarTrimestre = Table.AddColumn(
        AgregarNombreMes,
        "trimestre",
        each Date.QuarterOfYear([fecha]),
        Int64.Type
    ),

    // Agregar indicador de semestre
    AgregarSemestre = Table.AddColumn(
        AgregarTrimestre,
        "semestre",
        each if [mes_num] <= 6 then 1 else 2,
        Int64.Type
    ),

    // Clave única para la fecha
    AgregarFechaKey = Table.AddColumn(
        AgregarSemestre,
        "fecha_key",
        each Date.ToText([fecha], "yyyyMMdd"),
        type text
    )
in
    AgregarFechaKey

// ------------------------------------------------------------
// 7. Crear tabla de clusters de países
// ------------------------------------------------------------
let
    // Definir los clusters
    Clusters = Table.FromRows(
        {
            {"Cluster 0 - Emergentes", "Chile", "Corea del Sur", "Perú", "México", "Colombia", "Ecuador", "Canadá", "Panamá", "Guatemala", "Brasil", "España", "Holanda (Países Bajos)"},
            {"Cluster 1 - Potencias", "Estados Unidos"},
            {"Cluster 2 - Asiáticos", "China", "Japón"}
        },
        {"cluster_nombre", "pais1", "pais2", "pais3", "pais4", "pais5", "pais6", "pais7", "pais8", "pais9", "pais10", "pais11", "pais12"}
    ),

    // Despivotear para tener una fila por país
    Despivotar = Table.UnpivotOtherColumns(Clusters, {"cluster_nombre"}, "atributo", "pais"),
    
    // Filtrar países no nulos
    Filtrar = Table.SelectRows(Despivotar, each [pais] <> "" and [pais] <> null),

    // Seleccionar columnas finales
    Seleccionar = Table.SelectColumns(Filtrar, {"cluster_nombre", "pais"})
in
    Seleccionar

// ------------------------------------------------------------
// FIN DE CONSULTAS POWER QUERY
// ------------------------------------------------------------
