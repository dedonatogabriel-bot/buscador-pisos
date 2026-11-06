# Búsquedas guardadas para las alertas por email

> Archivo generado por `uv run python -m scrapers.queries`. No editar a mano: cambiá `config/busqueda.yaml` y volvé a generarlo.

Tope de alquiler: **$875.000** ($700.000 de la config + 25%).
Ambientes: **2 o más**. Alquiler tradicional.

## Qué hacer: una alerta por portal

No hace falta una alerta por barrio. Con **una alerta inmediata por portal** alcanza.

1. Creá el Gmail exclusivo de alertas. No lo uses para nada más.
2. Registrate con ese Gmail en Zonaprop, Argenprop y MercadoLibre.
3. En cada portal abrí la URL de la tabla de abajo.
4. Si no muestra resultados, tocá **Departamentos** + **Alquiler** + **Capital Federal** a mano y anotá en el issue #6 qué URL falló.
5. En los filtros marcá **todos los barrios de la lista** (o dejá CABA entera), precio máximo **$875.000** y **2 ambientes o más**.
6. Tocá "Crear alerta" / "Guardar búsqueda", frecuencia **inmediata**, al Gmail de alertas.
7. Esperá al menos 1 email por portal y comentalo en el issue #6.

| Portal | URL de partida | Qué cubre |
| --- | --- | --- |
| Zonaprop | https://www.zonaprop.com.ar/departamentos-alquiler-agronomia-almagro-balvanera-barracas-belgrano-boedo-caballito-chacarita-coghlan-colegiales-la-paternal-liniers-monte-castro-monserrat-nunez-palermo-parque-chacabuco-parque-chas-parque-patricios-puerto-madero-recoleta-retiro-saavedra-san-cristobal-san-nicolas-san-telmo-velez-sarsfield-versalles-villa-crespo-villa-del-parque-villa-devoto-villa-general-mitre-villa-luro-villa-ortuzar-villa-pueyrredon-villa-real-villa-santa-rita-villa-urquiza-menos-875000-pesos.html | Todos los barrios de la lista |
| Argenprop | https://www.argenprop.com/departamentos/alquiler/capital-federal/hasta-875000-pesos | CABA entera (marcá los barrios en el filtro si podés) |
| MercadoLibre | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/_PriceRange_0-875000_NoIndex_True | CABA entera (marcá los barrios en el filtro si podés) |

Si el portal te manda avisos de barrios que no están en la lista, no pasa nada: el sistema los descarta al procesar el email.

### Barrios a marcar

Agronomía, Almagro, Balvanera, Barracas, Belgrano, Boedo, Caballito, Chacarita, Coghlan, Colegiales, La Paternal, Liniers, Monte Castro, Monserrat, Núñez, Palermo, Parque Chacabuco, Parque Chas, Parque Patricios, Puerto Madero, Recoleta, Retiro, Saavedra, San Cristóbal, San Nicolás, San Telmo, Vélez Sársfield, Versalles, Villa Crespo, Villa del Parque, Villa Devoto, Villa General Mitre, Villa Luro, Villa Ortúzar, Villa Pueyrredón, Villa Real, Villa Santa Rita, Villa Urquiza.

## Estado de verificación

Las URLs de arriba **no están verificadas**: se derivaron de los formatos de abajo.

- **argenprop** (formato por barrio): verificada el 2026-11-06 (la URL de Palermo devolvió 759 avisos)
- **zonaprop** (formato por barrio): formato del scraper viejo (sep-2026); pendiente de abrir en G-06
- **mercadolibre** (formato por barrio): formato del scraper viejo (verificado el 14/09/2026); pendiente de abrir en G-06

## Plan B: una alerta por barrio

Solo si un portal no te deja elegir varios barrios ni CABA entera. Son 114 URLs en total (38 por portal). Mismos pasos 5 a 7, repetidos.

### Argenprop

| Barrio | URL |
| --- | --- |
| Agronomía | https://www.argenprop.com/departamentos/alquiler/agronomia/hasta-875000-pesos |
| Almagro | https://www.argenprop.com/departamentos/alquiler/almagro/hasta-875000-pesos |
| Balvanera | https://www.argenprop.com/departamentos/alquiler/balvanera/hasta-875000-pesos |
| Barracas | https://www.argenprop.com/departamentos/alquiler/barracas/hasta-875000-pesos |
| Belgrano | https://www.argenprop.com/departamentos/alquiler/belgrano/hasta-875000-pesos |
| Boedo | https://www.argenprop.com/departamentos/alquiler/boedo/hasta-875000-pesos |
| Caballito | https://www.argenprop.com/departamentos/alquiler/caballito/hasta-875000-pesos |
| Chacarita | https://www.argenprop.com/departamentos/alquiler/chacarita/hasta-875000-pesos |
| Coghlan | https://www.argenprop.com/departamentos/alquiler/coghlan/hasta-875000-pesos |
| Colegiales | https://www.argenprop.com/departamentos/alquiler/colegiales/hasta-875000-pesos |
| La Paternal | https://www.argenprop.com/departamentos/alquiler/la-paternal/hasta-875000-pesos |
| Liniers | https://www.argenprop.com/departamentos/alquiler/liniers/hasta-875000-pesos |
| Monte Castro | https://www.argenprop.com/departamentos/alquiler/monte-castro/hasta-875000-pesos |
| Monserrat | https://www.argenprop.com/departamentos/alquiler/monserrat/hasta-875000-pesos |
| Núñez | https://www.argenprop.com/departamentos/alquiler/nunez/hasta-875000-pesos |
| Palermo | https://www.argenprop.com/departamentos/alquiler/palermo/hasta-875000-pesos |
| Parque Chacabuco | https://www.argenprop.com/departamentos/alquiler/parque-chacabuco/hasta-875000-pesos |
| Parque Chas | https://www.argenprop.com/departamentos/alquiler/parque-chas/hasta-875000-pesos |
| Parque Patricios | https://www.argenprop.com/departamentos/alquiler/parque-patricios/hasta-875000-pesos |
| Puerto Madero | https://www.argenprop.com/departamentos/alquiler/puerto-madero/hasta-875000-pesos |
| Recoleta | https://www.argenprop.com/departamentos/alquiler/recoleta/hasta-875000-pesos |
| Retiro | https://www.argenprop.com/departamentos/alquiler/retiro/hasta-875000-pesos |
| Saavedra | https://www.argenprop.com/departamentos/alquiler/saavedra/hasta-875000-pesos |
| San Cristóbal | https://www.argenprop.com/departamentos/alquiler/san-cristobal/hasta-875000-pesos |
| San Nicolás | https://www.argenprop.com/departamentos/alquiler/san-nicolas/hasta-875000-pesos |
| San Telmo | https://www.argenprop.com/departamentos/alquiler/san-telmo/hasta-875000-pesos |
| Vélez Sársfield | https://www.argenprop.com/departamentos/alquiler/velez-sarsfield/hasta-875000-pesos |
| Versalles | https://www.argenprop.com/departamentos/alquiler/versalles/hasta-875000-pesos |
| Villa Crespo | https://www.argenprop.com/departamentos/alquiler/villa-crespo/hasta-875000-pesos |
| Villa del Parque | https://www.argenprop.com/departamentos/alquiler/villa-del-parque/hasta-875000-pesos |
| Villa Devoto | https://www.argenprop.com/departamentos/alquiler/villa-devoto/hasta-875000-pesos |
| Villa General Mitre | https://www.argenprop.com/departamentos/alquiler/villa-general-mitre/hasta-875000-pesos |
| Villa Luro | https://www.argenprop.com/departamentos/alquiler/villa-luro/hasta-875000-pesos |
| Villa Ortúzar | https://www.argenprop.com/departamentos/alquiler/villa-ortuzar/hasta-875000-pesos |
| Villa Pueyrredón | https://www.argenprop.com/departamentos/alquiler/villa-pueyrredon/hasta-875000-pesos |
| Villa Real | https://www.argenprop.com/departamentos/alquiler/villa-real/hasta-875000-pesos |
| Villa Santa Rita | https://www.argenprop.com/departamentos/alquiler/villa-santa-rita/hasta-875000-pesos |
| Villa Urquiza | https://www.argenprop.com/departamentos/alquiler/villa-urquiza/hasta-875000-pesos |

### Zonaprop

| Barrio | URL |
| --- | --- |
| Agronomía | https://www.zonaprop.com.ar/departamentos-alquiler-agronomia-menos-875000-pesos.html |
| Almagro | https://www.zonaprop.com.ar/departamentos-alquiler-almagro-menos-875000-pesos.html |
| Balvanera | https://www.zonaprop.com.ar/departamentos-alquiler-balvanera-menos-875000-pesos.html |
| Barracas | https://www.zonaprop.com.ar/departamentos-alquiler-barracas-menos-875000-pesos.html |
| Belgrano | https://www.zonaprop.com.ar/departamentos-alquiler-belgrano-menos-875000-pesos.html |
| Boedo | https://www.zonaprop.com.ar/departamentos-alquiler-boedo-menos-875000-pesos.html |
| Caballito | https://www.zonaprop.com.ar/departamentos-alquiler-caballito-menos-875000-pesos.html |
| Chacarita | https://www.zonaprop.com.ar/departamentos-alquiler-chacarita-menos-875000-pesos.html |
| Coghlan | https://www.zonaprop.com.ar/departamentos-alquiler-coghlan-menos-875000-pesos.html |
| Colegiales | https://www.zonaprop.com.ar/departamentos-alquiler-colegiales-menos-875000-pesos.html |
| La Paternal | https://www.zonaprop.com.ar/departamentos-alquiler-la-paternal-menos-875000-pesos.html |
| Liniers | https://www.zonaprop.com.ar/departamentos-alquiler-liniers-menos-875000-pesos.html |
| Monte Castro | https://www.zonaprop.com.ar/departamentos-alquiler-monte-castro-menos-875000-pesos.html |
| Monserrat | https://www.zonaprop.com.ar/departamentos-alquiler-monserrat-menos-875000-pesos.html |
| Núñez | https://www.zonaprop.com.ar/departamentos-alquiler-nunez-menos-875000-pesos.html |
| Palermo | https://www.zonaprop.com.ar/departamentos-alquiler-palermo-menos-875000-pesos.html |
| Parque Chacabuco | https://www.zonaprop.com.ar/departamentos-alquiler-parque-chacabuco-menos-875000-pesos.html |
| Parque Chas | https://www.zonaprop.com.ar/departamentos-alquiler-parque-chas-menos-875000-pesos.html |
| Parque Patricios | https://www.zonaprop.com.ar/departamentos-alquiler-parque-patricios-menos-875000-pesos.html |
| Puerto Madero | https://www.zonaprop.com.ar/departamentos-alquiler-puerto-madero-menos-875000-pesos.html |
| Recoleta | https://www.zonaprop.com.ar/departamentos-alquiler-recoleta-menos-875000-pesos.html |
| Retiro | https://www.zonaprop.com.ar/departamentos-alquiler-retiro-menos-875000-pesos.html |
| Saavedra | https://www.zonaprop.com.ar/departamentos-alquiler-saavedra-menos-875000-pesos.html |
| San Cristóbal | https://www.zonaprop.com.ar/departamentos-alquiler-san-cristobal-menos-875000-pesos.html |
| San Nicolás | https://www.zonaprop.com.ar/departamentos-alquiler-san-nicolas-menos-875000-pesos.html |
| San Telmo | https://www.zonaprop.com.ar/departamentos-alquiler-san-telmo-menos-875000-pesos.html |
| Vélez Sársfield | https://www.zonaprop.com.ar/departamentos-alquiler-velez-sarsfield-menos-875000-pesos.html |
| Versalles | https://www.zonaprop.com.ar/departamentos-alquiler-versalles-menos-875000-pesos.html |
| Villa Crespo | https://www.zonaprop.com.ar/departamentos-alquiler-villa-crespo-menos-875000-pesos.html |
| Villa del Parque | https://www.zonaprop.com.ar/departamentos-alquiler-villa-del-parque-menos-875000-pesos.html |
| Villa Devoto | https://www.zonaprop.com.ar/departamentos-alquiler-villa-devoto-menos-875000-pesos.html |
| Villa General Mitre | https://www.zonaprop.com.ar/departamentos-alquiler-villa-general-mitre-menos-875000-pesos.html |
| Villa Luro | https://www.zonaprop.com.ar/departamentos-alquiler-villa-luro-menos-875000-pesos.html |
| Villa Ortúzar | https://www.zonaprop.com.ar/departamentos-alquiler-villa-ortuzar-menos-875000-pesos.html |
| Villa Pueyrredón | https://www.zonaprop.com.ar/departamentos-alquiler-villa-pueyrredon-menos-875000-pesos.html |
| Villa Real | https://www.zonaprop.com.ar/departamentos-alquiler-villa-real-menos-875000-pesos.html |
| Villa Santa Rita | https://www.zonaprop.com.ar/departamentos-alquiler-villa-santa-rita-menos-875000-pesos.html |
| Villa Urquiza | https://www.zonaprop.com.ar/departamentos-alquiler-villa-urquiza-menos-875000-pesos.html |

### Mercadolibre

| Barrio | URL |
| --- | --- |
| Agronomía | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/agronomia/_PriceRange_0-875000_NoIndex_True |
| Almagro | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/almagro/_PriceRange_0-875000_NoIndex_True |
| Balvanera | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/balvanera/_PriceRange_0-875000_NoIndex_True |
| Barracas | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/barracas/_PriceRange_0-875000_NoIndex_True |
| Belgrano | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/belgrano/_PriceRange_0-875000_NoIndex_True |
| Boedo | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/boedo/_PriceRange_0-875000_NoIndex_True |
| Caballito | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/caballito/_PriceRange_0-875000_NoIndex_True |
| Chacarita | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/chacarita/_PriceRange_0-875000_NoIndex_True |
| Coghlan | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/coghlan/_PriceRange_0-875000_NoIndex_True |
| Colegiales | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/colegiales/_PriceRange_0-875000_NoIndex_True |
| La Paternal | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/la-paternal/_PriceRange_0-875000_NoIndex_True |
| Liniers | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/liniers/_PriceRange_0-875000_NoIndex_True |
| Monte Castro | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/monte-castro/_PriceRange_0-875000_NoIndex_True |
| Monserrat | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/monserrat/_PriceRange_0-875000_NoIndex_True |
| Núñez | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/nunez/_PriceRange_0-875000_NoIndex_True |
| Palermo | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/palermo/_PriceRange_0-875000_NoIndex_True |
| Parque Chacabuco | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/parque-chacabuco/_PriceRange_0-875000_NoIndex_True |
| Parque Chas | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/parque-chas/_PriceRange_0-875000_NoIndex_True |
| Parque Patricios | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/parque-patricios/_PriceRange_0-875000_NoIndex_True |
| Puerto Madero | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/puerto-madero/_PriceRange_0-875000_NoIndex_True |
| Recoleta | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/recoleta/_PriceRange_0-875000_NoIndex_True |
| Retiro | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/retiro/_PriceRange_0-875000_NoIndex_True |
| Saavedra | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/saavedra/_PriceRange_0-875000_NoIndex_True |
| San Cristóbal | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/san-cristobal/_PriceRange_0-875000_NoIndex_True |
| San Nicolás | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/san-nicolas/_PriceRange_0-875000_NoIndex_True |
| San Telmo | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/san-telmo/_PriceRange_0-875000_NoIndex_True |
| Vélez Sársfield | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/velez-sarsfield/_PriceRange_0-875000_NoIndex_True |
| Versalles | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/versalles/_PriceRange_0-875000_NoIndex_True |
| Villa Crespo | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-crespo/_PriceRange_0-875000_NoIndex_True |
| Villa del Parque | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-del-parque/_PriceRange_0-875000_NoIndex_True |
| Villa Devoto | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-devoto/_PriceRange_0-875000_NoIndex_True |
| Villa General Mitre | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-general-mitre/_PriceRange_0-875000_NoIndex_True |
| Villa Luro | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-luro/_PriceRange_0-875000_NoIndex_True |
| Villa Ortúzar | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-ortuzar/_PriceRange_0-875000_NoIndex_True |
| Villa Pueyrredón | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-pueyrredon/_PriceRange_0-875000_NoIndex_True |
| Villa Real | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-real/_PriceRange_0-875000_NoIndex_True |
| Villa Santa Rita | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-santa-rita/_PriceRange_0-875000_NoIndex_True |
| Villa Urquiza | https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/villa-urquiza/_PriceRange_0-875000_NoIndex_True |
