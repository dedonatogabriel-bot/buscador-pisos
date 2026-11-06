# Buscador de deptos — CABA

Sistema de recolección y filtrado automático de alquileres en Capital Federal.

## Qué hace hoy

Corre cada 6 horas. Trae avisos de MercadoLibre, Zonaprop y Argenprop.
Los pasa por cuatro filtros y guarda solo lo que sobrevive.

1. **Zona** — la definen los barrios, no las coordenadas. Pasa lo que esté en
   `BARRIOS_OK`, cae lo que esté en `BARRIOS_EXCLUIDOS`. Además descarta lo que
   quede a más de 1500 m de una estación de subte o metrobús.
2. **Comodidades** — balcón, calefacción, 1 dormitorio, 50 m² mínimo, ascensor,
   sin amoblar. Lo que no informa el dato NO se descarta: se marca `revisar_a_mano`.
3. **Plata** — techo de $700.000 alquiler y $900.000 total con expensas.
4. **Motor financiero** — compara mudarse ya pagando la multa contra esperar a mayo.

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python run.py --actualizar-transporte   # una sola vez, baja datos del GCBA
python run.py --dry                     # prueba sin escribir en la base
python run.py                           # corrida real
python tests/test_pipeline.py           # verifica la lógica de filtrado
```

Cron cada 6 horas:

```
0 */6 * * * cd /ruta/buscador && /usr/bin/python3 run.py >> logs/corrida.log 2>&1
```

## Configuración

Todo lo tuneable está en `config.py`. No toques la lógica para cambiar números.

## MercadoLibre

Es el único con API oficial. Empezá por acá: no se rompe con cambios de HTML.
Sacá un token en developers.mercadolibre.com.ar y exportalo:

```bash
export ML_ACCESS_TOKEN="APP_USR-..."
```

## Limitaciones conocidas

- **Zonaprop y Argenprop están detrás de Cloudflare.** Playwright pasa la mayoría
  de las veces, pero los selectores CSS cambian cada pocos meses. Están todos
  juntos en `scrapers/portales_html.py` para arreglarlos en un solo lugar.
  Si el scraper devuelve 0 avisos, revisá primero los selectores.
- **Los datos de transporte del fallback son aproximados.** Corré
  `--actualizar-transporte` en una máquina con red para usar los datasets
  oficiales del GCBA.
- **La distancia al trabajo es en línea recta, no tiempo real de viaje.** 7 km es
  un proxy grueso de 30-40 minutos. Para tiempo real hay que sumar la API de
  Google Directions.
- **El filtro de balcón y calefacción lee texto.** Un aviso puede tener balcón y
  no mencionarlo. Por eso esos casos van a `revisar_a_mano` en vez de descartarse.

## Lo que falta

- Notificación por WhatsApp o email (hoy solo imprime en consola).
- Grupos de Facebook e Instagram (semi-manual, Meta bloquea automatización).
- Tiempo de viaje real con Google Directions.
- Migrar de SQLite a Supabase si querés verlo desde el celular.

## Estructura

```
config.py                    criterios y números
models.py                    Aviso: modelo único que devuelven todos los scrapers
geo.py                       zona, distancia, cercanía a subte y metrobús
filtros.py                   comodidades sobre el texto del aviso
finanzas.py                  motor mudarse-ya vs esperar-a-mayo
storage.py                   SQLite y deduplicación
run.py                       orquestador
scrapers/mercadolibre.py     API oficial
scrapers/portales_html.py    Zonaprop y Argenprop con Playwright
tests/test_pipeline.py       12 casos límite
```
