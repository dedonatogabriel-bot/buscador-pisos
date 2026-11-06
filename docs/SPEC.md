# Especificación — buscador-pisos

Versión 1 · 6 de noviembre de 2026 · Fuente: plan "Marcos se muda — Plan del buscador total".

## 1. Objetivo

Encontrar para Marcos el mejor alquiler de CABA al mejor precio, con entrada el 1 de mayo de 2027.
El sistema captura todos los avisos posibles, los valora contra el mercado y avisa rápido.

## 2. Requisitos de Marcos

| Requisito | Valor |
| --- | --- |
| Zona | Capital Federal, al norte de Av. Juan de Garay |
| Tipo | Alquiler tradicional, sin amueblar, no temporario |
| Tamaño | 1 dormitorio o más (2 ambientes o más), 50 m² cubiertos o más |
| Edificio | Piso 5 o más, con ascensor. Antigüedad ~25 años está bien |
| Imprescindibles | Balcón, calefacción |
| Transporte | 30–40 min puerta a puerta hasta Callao y Corrientes. Prioriza subte o Metrobús cerca |
| Presupuesto | Alquiler hasta $700.000 + expensas hasta $200.000 = $900.000/mes total |
| Garantía | Garantía propietaria de CABA |
| Irrelevante | Cochera, apto profesional, apto crédito, mascotas |
| Anunciante | Dueño directo o inmobiliaria |
| Frecuencia aceptada | Revisar avisos nuevos cada 6 horas |
| Contrato actual | En pesos, ajuste IPC trimestral, vence en mayo 2027. Penalidad declarada: 2 meses de alquiler |

Pendientes de confirmar: ver `docs/DECISIONES.md`.

## 3. Contexto de mercado (sep 2026)

- Mediana 2 ambientes CABA: $898.154/mes (Index Zonaprop). Palermo: $1.005.424.
- Suba mensual reciente: 1,3% a 1,5%. Mediana proyectada a mayo 2027: ~$1.000.000.
- El tope de Marcos queda ~22% bajo la mediana hoy y ~30% en mayo.
- Consecuencia: el sistema busca el 10–15% más barato del mercado. Los pisos fuera de presupuesto sirven como datos de mercado.
- Barrios de mediana más baja dentro del radio: Almagro, Balvanera, Boedo, San Cristóbal, Caballito, Villa Crespo.

## 4. Arquitectura

```
Fuentes ──► Captura ──► Supabase (ingest) ──► Normalizar ──► Deduplicar ──► Enriquecer ──► Valorar ──► Salidas
                                                                                                  ├─ Telegram (alertas, comandos)
                                                                                                  └─ Web privada (mapa, ranking, ficha, pipeline)
```

- **Fuente de verdad:** Supabase. Toda fuente entra por la Edge Function `ingest`.
- **Primera alerta sin IA:** reglas + datos del portal + palabras clave + precio contra comparables SQL. Inmediata.
- **IA por lotes:** `claude -p` con Haiku corre en la PC entre 02:00 y 08:00 Madrid. Confirma o corrige campos y score.

## 5. Fuentes

| Nivel | Fuente | Método | Frecuencia |
| --- | --- | --- | --- |
| 1 | Zonaprop | Alertas por email + Playwright desde la PC | Push + cada 6 h |
| 1 | Argenprop | Alertas por email + Playwright desde la PC | Push + cada 6 h |
| 1 | MercadoLibre Inmuebles | API oficial con OAuth (sin token devuelve 403) + alertas por email | Cada 1 h |
| 1 | Properati | HTML desde GitHub Actions | Cada 12 h |
| 2 | Franquicias (RE/MAX, Century 21, Toribio Achával) | Adaptador por sitio, validar factibilidad | Cada 12 h |
| 3 | Inmobiliarias de barrio | Adaptador por plataforma (Tokko primero) | Cada 12 h |
| 4 | Facebook, Instagram, carteles, encargados | Inbox del bot de Telegram | A demanda |

Marzo y abril: scrapers de portales cada 2 h.

## 6. Modelo de datos (Supabase + PostGIS)

| Tabla | Contenido |
| --- | --- |
| `sources` | Fuente: nombre, tipo, método, activa, última corrida, último éxito |
| `listings_raw` | Respuesta cruda por aviso y corrida: fuente, url, html gzip (path en Storage) o json, fecha |
| `listings` | Aviso normalizado: fuente, id externo, url, título, descripción, precio, moneda, expensas, m², ambientes, dormitorios, piso, ascensor, balcón, calefacción, orientación, antigüedad, estado, ajuste, garantías, disponible desde, anunciante (dueño/inmobiliaria), agencia, coordenadas, precisión de ubicación, barrio, fotos (urls), banderas, first_seen, last_seen, status (activo/retirado), unit_id, campos de IA, versión de extracción |
| `units` | Piso físico que agrupa avisos duplicados: ubicación, m², ambientes, precio mínimo y fuente del mínimo |
| `price_events` | Historial: listing_id, precio anterior, precio nuevo, fecha |
| `scores` | Por unit: filtros duros (pasa/falla y motivo), precio justo p10/p50/p90, desvío, tipos de chollo, componentes del score, score total, versión |
| `pipeline` | Estado de Marcos con cada unit: nuevo, me interesa, contactado, visita agendada, visitado, oferta, firmado, descartado; motivo; notas |
| `agencies` | Inmobiliarias: nombre, web, instagram, barrio, plataforma detectada, adaptador, activa |
| `geo_*` | Capas: barrios, estaciones de subte, Metrobús, isocrona de 40 min |
| `market_stats` | Medianas y oferta por barrio y semana |

## 7. Extracción (IA por lotes)

Entrada: título, descripción, atributos del portal. Salida JSON validada con esquema:

- precio, moneda, expensas, ABL si figura
- m² cubiertos y totales, ambientes, dormitorios, piso, ascensor
- balcón: sí/no, tipo (francés, corrido, aterrazado), m²
- calefacción: losa radiante, central, tiro balanceado, split frío/calor, ninguna, desconocida
- orientación, luminosidad, frente/contrafrente, antigüedad, estado
- ajuste (IPC trimestral, cuatrimestral, semestral, ICL, USD, otro), duración, garantías aceptadas, fecha disponible
- banderas: pide honorarios, pide seña antes de visitar, temporario disfrazado, amueblado
- confianza por campo

Visión (pisos que pasan filtros): balcón confirmado, estado de cocina y baño, luz natural, humedad visible, calidad de fotos.
Hash perceptual (pHash) de cada foto para deduplicar y detectar estafas (misma foto en dos direcciones).

## 8. Deduplicado

1. Candidatos: radio de 150 m + mismos ambientes + m² ±3.
2. Similitud de fotos (pHash, distancia de Hamming baja) = mismo piso.
3. Similitud de descripción.
4. Agrupar en `units`. Guardar el precio más bajo y quién lo publica.

## 9. Enriquecimiento

- Normalizar dirección con USIG (GCBA). Guardar precisión: exacta, cuadra, barrio.
- Distancia a la estación de subte y de Metrobús más cercanas, y su línea. Priorizar líneas B, D y A.
- Isocrona de 40 min a Callao y Corrientes (OpenTripPlanner + GTFS, calculada una vez). Filtro con `ST_Within`.
- Capas de entorno (delitos, ruido, inundación) si los datasets del GCBA están vigentes.

## 10. Valoración y chollos

**Precio provisorio (sin IA, inmediato):** mediana de $/m² de los 15 comparables activos más cercanos con mismos ambientes.
**Modelo nocturno:** LightGBM con regresión por cuantiles (p10, p50, p90) entrenado con todos los avisos capturados, dentro y fuera de presupuesto.
Variables: m², ambientes, barrio, distancia a subte, piso, balcón, calefacción, antigüedad, estado, amenities, expensas, días publicado, mes.
Desvío = (precio pedido − p50) / p50. Control de calidad: error absoluto medio ≤ 10%.

| Chollo | Señal |
| --- | --- |
| Subvaluado | Desvío ≤ −15% con confianza alta |
| Baja de precio | Evento de precio negativo |
| Arbitraje | Mismo unit más barato en otro aviso |
| Dueño directo reciente | Publicado hace < 24 h, sin inmobiliaria |
| Estancado | > 45 días publicado → ofertar 8–12% abajo |
| Aviso feo | Fotos malas, título pobre, barrio mal cargado |
| Expensas bajas | Edificio sin encargado o PH |
| Ajuste favorable | Semestral o mejor |

**Antifraude:** desvío ≤ −35%, urgencia, seña antes de visitar, dueño "en el exterior", fotos repetidas en otra dirección.

## 11. Filtros duros y score

Filtros duros: tradicional, sin amueblar, ≥ 1 dormitorio, ≥ 50 m², balcón y calefacción confirmados, piso ≥ 5 con ascensor, dentro de la isocrona, costo total ≤ tope indexado + 10%.
Los que fallan se guardan como datos de mercado.

```
Score = 35·P + 20·T + 15·E + 15·C + 10·U + 5·N   (0–100)
P precio (costo total vs tope y vs precio justo) · T transporte · E espacio
C confort · U urgencia (probabilidad de alquilarse en 72 h) · N entorno
```

Los pesos viven en `config/busqueda.yaml`. Los descartes con motivo reajustan los pesos.
El tope se indexa por IPC mensual si Marcos lo confirma.

## 12. Salidas

**Telegram**
- Rojo inmediato (08:00–23:00 BA): score ≥ 80, baja de precio en favorito, dueño directo < 24 h.
- Amarillo: score 60–79, resumen a las 09:00 y 19:00 BA.
- Mercado: reporte semanal, lunes 09:00 BA.
- Sistema: fuente caída → Gabi.
- Botones: Me interesa · Descartar (motivo) · Ver ficha · Contactar (abre WhatsApp con plantilla).
- Comandos: `/top`, `/barrio <nombre>`, `/max <miles>`, `/balcon`, `/nuevos`.
- Inbox: links, capturas, foto de cartel (OCR + GPS de la foto).

Plantilla de contacto: disponibilidad desde [fecha], expensas reales del último mes, ajuste y frecuencia, acepta garantía propietaria CABA, tipo de calefacción, visita [día] [hora].

**Web privada** (Firebase Hosting, Supabase Auth con link mágico, solo 2 emails)
Mapa · Ranking · Ficha del piso (fotos, avisos agrupados, historial, precio justo, comparables, minutos, costo total, simulación 24 meses, contactar) · Pipeline · Mercado · Calculadora · Configuración.
Guardar captura de cada aviso como prueba.

## 13. Reglas legales y económicas

- CABA: Ley 5859, el inquilino no paga comisión ni honorarios. Marcar avisos que los piden.
- DNU 70/2023: sin pacto, rescindir cuesta 10% del alquiler que falta. El contrato de Marcos dice 2 meses: verificar cláusula.
- Mudarse antes conviene si (alquiler actual − alquiler nuevo) × meses que faltan > penalidad + mudanza + superposición.
- Negociar en el contrato nuevo: ajuste semestral, rescisión 10% o 1 mes, inicio alineado con el fin del actual, expensas extraordinarias a cargo del propietario.
- Nunca pagar seña sin visitar y sin informe de dominio. Verificar matrícula de la inmobiliaria.

## 14. Roadmap y controles

| Fase | Fechas | Contenido |
| --- | --- | --- |
| 0 Base | nov 2026 | Cuentas, decisiones, repo, esquema |
| 1 Captura | nov–dic | Portales, ingest, dedupe v1, bot y web v1, salud |
| 2 Inteligencia | dic–ene | IA por lotes, enriquecimiento, modelo, chollos, score |
| 3 Cobertura | ene–feb | Inmobiliarias, inbox, web v2 |
| 4 Agentes y caza | feb–may | Médico de scrapers, analista nocturno, modo caza, cierre |

- **Control modelo** (fin fase 2): error absoluto medio del precio justo ≤ 10%.
- **Control oferta** (fin de febrero): ≥ 3 pisos por semana pasan los filtros duros. Si no, ajustar tope, barrios o m² con Marcos.

## 15. Costo

Objetivo US$0: planes gratis de Supabase, GitHub Actions (2.000 min/mes), Apps Script, Firebase Hosting y Telegram.
La IA corre con la suscripción Pro de Gabi vía `claude -p` en la franja 02:00–08:00 Madrid.
Opcional: clave de API con tope US$5/mes para visión de los 10 mejores pisos del día.
