# Calendarios de fiestas locales municipales de España 2026 (ICS)

Descarga un calendario `.ics` determinista con las fiestas laborales de 2026 de cualquier municipio español cubierto. Esta versión publica **7,194 calendarios completos** de los **8,132 municipios** del padrón INE de 2026 y declara explícitamente los **938 municipios sin calendario** y el motivo de cada omisión.

> Este repositorio es un servicio derivado y no oficial. Para decisiones con consecuencias legales u operativas, verifica las fechas en las publicaciones oficiales enlazadas.

## Descargar un calendario

1. Abre [`calendars/index.json`](calendars/index.json).
2. Localiza el municipio por su código INE oficial de cinco dígitos o por su nombre.
3. Descarga el archivo indicado por su `path`; por ejemplo, `calendars/2026/andalucia/04001-abla.ics`.

Solo las entradas de `calendars` se anuncian como completas. El array `omissions` nombra cada municipio sin archivo publicado y explica el motivo, agrupado por comunidad autónoma.

## Importar en Google Calendar

En un ordenador, abre Google Calendar y elige **Configuración > Importar y exportar > Importar**, selecciona el archivo `.ics` descargado, elige el calendario de destino e impórtalo. Los archivos importados son instantáneas y no se sincronizan con correcciones posteriores; descarga de nuevo el archivo regenerado tras una actualización de las fuentes.

Google documenta el flujo de importación y el envoltorio iCalendar exigido en su [ayuda de Calendar](https://support.google.com/calendar/answer/37118?hl=es).

## Qué contiene cada calendario

Cada calendario combina las fiestas no locales del territorio (nacionales y de la comunidad autónoma, del calendario oficial del BOE) con las fiestas locales del municipio publicadas por la fuente oficial de su comunidad. Según el modelo legal de cada comunidad, se añaden el día insular (Canarias), el día de territorio (País Vasco) o el día común de San Francisco Javier (Navarra).

Los eventos son de día completo RFC 5545 con identificadores estables, marcas de tiempo deterministas, líneas UTF-8 CRLF y plegado de 75 octetos. Los nombres de archivo usan el código INE para que un cambio de nombre no cambie la identidad.

## Cobertura y lagunas conocidas

| Medida                                        | Valor 2026                 |
| --------------------------------------------- | -------------------------- |
| Municipios de España en el padrón INE         | 8,132                      |
| Calendarios completos publicados              | 7,194                      |
| Municipios omitidos                           | 938                        |
| Andalucía (`andalucia`)                       | 774/785 (11 omitidos)      |
| Aragón (`aragon`)                             | 577/731 (154 omitidos)     |
| Asturias (`asturias`)                         | 71/78 (7 omitidos)         |
| Canarias (`canarias`)                         | 88/88 (0 omitidos)         |
| Cantabria (`cantabria`)                       | 102/102 (0 omitidos)       |
| Castilla-La Mancha (`castilla-la-mancha`)     | 904/919 (15 omitidos)      |
| Castilla y León (`castilla-y-leon`)           | 1,612/2,248 (636 omitidos) |
| Cataluña (`catalunya`)                        | 891/947 (56 omitidos)      |
| Ceuta (`ceuta`)                               | 1/1 (0 omitidos)           |
| Comunidad de Madrid (`comunidad-de-madrid`)   | 178/179 (1 omitidos)       |
| Comunitat Valenciana (`comunitat-valenciana`) | 539/542 (3 omitidos)       |
| Extremadura (`extremadura`)                   | 388/388 (0 omitidos)       |
| Galicia (`galicia`)                           | 313/313 (0 omitidos)       |
| Illes Balears (`illes-balears`)               | 67/67 (0 omitidos)         |
| La Rioja (`la-rioja`)                         | 161/174 (13 omitidos)      |
| Melilla (`melilla`)                           | 1/1 (0 omitidos)           |
| Navarra (`navarra`)                           | 236/272 (36 omitidos)      |
| País Vasco (`pais-vasco`)                     | 246/252 (6 omitidos)       |
| Región de Murcia (`region-de-murcia`)         | 45/45 (0 omitidos)         |

Las fuentes primarias son mutables y reciben correcciones durante el año (cadenas de resoluciones de modificación en varios boletines). Las instantáneas congeladas reflejan el estado documentado de cada fuente; cambios oficiales posteriores requieren una actualización de fuentes y una regeneración. Los nombres de las fuentes pueden diferir de los nombres INE; todas las uniones son explícitas y auditadas, nunca emparejadas de forma difusa. Las listas completas de exclusiones aparecen en [Municipios no incluidos](#municipios-no-incluidos).

## Municipios no incluidos

Los municipios siguientes **no tienen calendario publicado**: la evidencia oficial congelada no contiene un par completo de fiestas locales de ámbito municipal para 2026 (el pleno no comunicó propuesta, la resolución publica solo fechas de pedanías o núcleos con fechas distintas, o la fecha es «sin determinar»). No se publica un calendario que podría resultar engañoso. Los nombres proceden del padrón municipal oficial del INE.

### Andalucía

- Motivo: La fuente oficial congelada (Junta de Andalucía) no contiene dos registros de fiestas locales de 2026 para este municipio.

| Código INE | Municipio               |
| ---------- | ----------------------- |
| 04043      | Felix                   |
| 04060      | Lucainena de las Torres |
| 18064      | Dehesas de Guadix       |
| 18109      | Jete                    |
| 18115      | Láchar                  |
| 18185      | Ventas de Huelma        |
| 18901      | Taha, La                |
| 29016      | Árchez                  |
| 29024      | Benalauría              |
| 41008      | Algámitas               |
| 41013      | Aznalcóllar             |

### Aragón

- Motivo: Ausente de las resoluciones oficiales BOA 225 y BOA 56 de 2026, o con una sola fecha de ámbito municipal; sin publicación municipal oficial localizada.

| Código INE | Municipio                            |
| ---------- | ------------------------------------ |
| 22017      | Alcolea de Cinca                     |
| 22037      | Arguis                               |
| 22050      | Barbuñales                           |
| 22052      | Belver de Cinca                      |
| 22064      | Blecua y Torres                      |
| 22068      | Borau                                |
| 22106      | Fago                                 |
| 22127      | Igriés                               |
| 22156      | Monflorite-Lascasas                  |
| 22177      | Perarrúa                             |
| 22178      | Pertusa                              |
| 22234      | Torrente de Cinca                    |
| 22235      | Torres de Alcanadre                  |
| 22251      | Villanueva de Sigena                 |
| 44001      | Ababuj                               |
| 44003      | Aguatón                              |
| 44005      | Aguilar del Alfambra                 |
| 44006      | Alacón                               |
| 44007      | Alba                                 |
| 44011      | Alcaine                              |
| 44018      | Almohaja                             |
| 44021      | Allepuz                              |
| 44024      | Anadón                               |
| 44028      | Argente                              |
| 44035      | Barrachina                           |
| 44036      | Bea                                  |
| 44039      | Bello                                |
| 44041      | Bezas                                |
| 44042      | Blancas                              |
| 44043      | Blesa                                |
| 44046      | Bueña                                |
| 44053      | Camañas                              |
| 44055      | Camarillas                           |
| 44060      | Cañada de Benatanduz                 |
| 44065      | Castejón de Tornos                   |
| 44066      | Castel de Cabra                      |
| 44074      | Cedrillas                            |
| 44075      | Celadas                              |
| 44087      | Crivillén                            |
| 44088      | Cuba, La                             |
| 44093      | Cuevas de Almudén                    |
| 44101      | Ferreruela de Huerva                 |
| 44102      | Fonfría                              |
| 44106      | Fortanete                            |
| 44110      | Fuenferrada                          |
| 44111      | Fuentes Calientes                    |
| 44125      | Huesa del Común                      |
| 44126      | Iglesuela del Cid, La                |
| 44130      | Jorcas                               |
| 44132      | Lagueruela                           |
| 44133      | Lanzuela                             |
| 44136      | Lidón                                |
| 44138      | Loscos                               |
| 44142      | Maicas                               |
| 44146      | Mata de los Olmos, La                |
| 44148      | Mezquita de Jarque                   |
| 44149      | Mirambel                             |
| 44150      | Miravete de la Sierra                |
| 44152      | Monforte de Moyuela                  |
| 44153      | Monreal del Campo                    |
| 44156      | Monteagudo del Castillo              |
| 44159      | Moscardón                            |
| 44161      | Muniesa                              |
| 44167      | Obón                                 |
| 44168      | Odón                                 |
| 44169      | Ojos Negros                          |
| 44173      | Olmos, Los                           |
| 44175      | Orrios                               |
| 44176      | Palomar de Arroyos                   |
| 44178      | Parras de Castellote, Las            |
| 44180      | Peracense                            |
| 44183      | Pitarque                             |
| 44184      | Plou                                 |
| 44185      | Pobo, El                             |
| 44190      | Pozuel del Campo                     |
| 44194      | Ráfales                              |
| 44198      | Royuela                              |
| 44205      | Samper de Calanda                    |
| 44211      | Segura de los Baños                  |
| 44213      | Singra                               |
| 44219      | Tornos                               |
| 44224      | Torre de las Arcas                   |
| 44229      | Torres de Albarracín                 |
| 44235      | Tramacastilla                        |
| 44236      | Tronchón                             |
| 44246      | Valderrobres                         |
| 44251      | Villafranca del Campo                |
| 44252      | Villahermosa del Campo               |
| 44256      | Villanueva del Rebollar de la Sierra |
| 44258      | Villar del Salz                      |
| 44260      | Villarluengo                         |
| 44262      | Villarroya de los Pinares            |
| 44266      | Visiedo                              |
| 44267      | Vivel del Río Martín                 |
| 44268      | Zoma, La                             |
| 50004      | Aguarón                              |
| 50009      | Alarba                               |
| 50010      | Alberite de San Juan                 |
| 50021      | Almochuel                            |
| 50028      | Anento                               |
| 50035      | Artieda                              |
| 50036      | Asín                                 |
| 50040      | Badules                              |
| 50042      | Balconchán                           |
| 50052      | Bisimbre                             |
| 50071      | Campillo de Aragón                   |
| 50075      | Castejón de Alarba                   |
| 50078      | Castiliscar                          |
| 50080      | Cerveruela                           |
| 50088      | Cosuenda                             |
| 50114      | Fuendetodos                          |
| 50116      | Fuentes de Jiloca                    |
| 50123      | Grisén                               |
| 50134      | Langa del Castillo                   |
| 50135      | Layana                               |
| 50139      | Letux                                |
| 50142      | Lobera de Onsella                    |
| 50148      | Luesia                               |
| 50149      | Luesma                               |
| 50168      | Mianos                               |
| 50171      | Moneva                               |
| 50173      | Monterde                             |
| 50176      | Morata de Jiloca                     |
| 50178      | Moros                                |
| 50182      | Muela, La                            |
| 50183      | Munébrega                            |
| 50188      | Nombrevilla                          |
| 50194      | Olvés                                |
| 50195      | Orcajo                               |
| 50198      | Oseja                                |
| 50205      | Pedrosas, Las                        |
| 50210      | Pintanos, Los                        |
| 50216      | Pozuelo de Aragón                    |
| 50217      | Pradilla de Ebro                     |
| 50218      | Puebla de Albortón                   |
| 50220      | Puendeluna                           |
| 50224      | Retascón                             |
| 50227      | Romanos                              |
| 50228      | Rueda de Jalón                       |
| 50233      | Samper del Salz                      |
| 50245      | Sigüés                               |
| 50254      | Tierga                               |
| 50258      | Torralbilla                          |
| 50259      | Torrehermosa                         |
| 50266      | Trasobares                           |
| 50269      | Urrea de Jalón                       |
| 50273      | Valdehorna                           |
| 50274      | Val de San Martín                    |
| 50275      | Valmadrid                            |
| 50277      | Valtorres                            |
| 50279      | Velilla de Jiloca                    |
| 50282      | Vilueña, La                          |
| 50290      | Villanueva de Huerva                 |
| 50901      | Biel                                 |

### Asturias

- Motivo: La resolución oficial del BOPA no contiene dos fiestas locales de ámbito de concejo para 2026: las fechas publicadas son específicas de parroquia o núcleos, o la fiesta patronal es movible sin fecha fija.

| Código INE | Municipio                  |
| ---------- | -------------------------- |
| 33003      | Amieva                     |
| 33019      | Colunga                    |
| 33046      | Peñamellera Alta           |
| 33055      | Ribadedeva                 |
| 33059      | Salas                      |
| 33060      | San Martín del Rey Aurelio |
| 33078      | Yernes y Tameza            |

### Castilla y León

- Motivo: Sin registro oficial completo de fiestas locales para 2026: ausente o incompleto en los anuncios provinciales de septiembre de 2025 (BOP) y en el conjunto de datos de la Junta de Castilla y León.

| Código INE | Municipio                          |
| ---------- | ---------------------------------- |
| 05002      | Adrada, La                         |
| 05007      | Aldeanueva de Santa Cruz           |
| 05010      | Aldehuela, La                      |
| 05018      | Avellaneda                         |
| 05021      | Barco de Ávila, El                 |
| 05022      | Barraco, El                        |
| 05024      | Becedas                            |
| 05025      | Becedillas                         |
| 05026      | Bercial de Zapardiel               |
| 05030      | Berrocalejo de Aragona             |
| 05039      | Brabos                             |
| 05063      | Collado del Mirón                  |
| 05066      | Cuevas del Valle                   |
| 05080      | Gallegos de Sobrinos               |
| 05084      | Gilbuena                           |
| 05087      | Gotarrendura                       |
| 05088      | Grandes y San Martín               |
| 05092      | Hernansancho                       |
| 05096      | Hija de Dios, La                   |
| 05097      | Horcajada, La                      |
| 05100      | Hornillo, El                       |
| 05103      | Hoyorredondo                       |
| 05106      | Hoyos de Miguel Muñoz              |
| 05116      | Malpartida de Corneja              |
| 05117      | Mamblas                            |
| 05119      | Manjabálago y Ortigosa de Rioalmar |
| 05126      | Mesegar de Corneja                 |
| 05131      | Mirueña de los Infanzones          |
| 05139      | Muñogrande                         |
| 05148      | Narros del Puerto                  |
| 05155      | Navaescurial                       |
| 05160      | Navalosa                           |
| 05164      | Navaquesera                        |
| 05169      | Navatalgordo                       |
| 05175      | Oso, El                            |
| 05184      | Peguerinos                         |
| 05190      | Pozanco                            |
| 05195      | Riofrío                            |
| 05200      | San Bartolomé de Corneja           |
| 05206      | San Esteban de los Patos           |
| 05212      | San Juan del Molinillo             |
| 05213      | San Juan del Olmo                  |
| 05214      | San Lorenzo de Tormes              |
| 05217      | San Miguel de Corneja              |
| 05222      | Santa Cruz de Pinares              |
| 05224      | Santa María del Arroyo             |
| 05226      | Santa María de los Caballeros      |
| 05228      | Santiago del Collado               |
| 05229      | Santo Domingo de las Posadas       |
| 05230      | Santo Tomé de Zabarcos             |
| 05234      | Sigeres                            |
| 05238      | Solosancho                         |
| 05243      | Tolbaños                           |
| 05251      | Vadillo de la Sierra               |
| 05256      | Villaflor                          |
| 05260      | Villanueva del Campillo            |
| 05263      | Villatoro                          |
| 05264      | Viñegra de Moraña                  |
| 05901      | San Juan de Gredos                 |
| 05904      | Santiago del Tormes                |
| 09006      | Aguas Cándidas                     |
| 09007      | Aguilar de Bureba                  |
| 09009      | Albillos                           |
| 09014      | Altos, Los                         |
| 09020      | Arauzo de Miel                     |
| 09022      | Arauzo de Torre                    |
| 09025      | Arija                              |
| 09026      | Arlanzón                           |
| 09032      | Avellanosa de Muñó                 |
| 09034      | Balbases, Los                      |
| 09037      | Barbadillo de Herreros             |
| 09039      | Barbadillo del Pez                 |
| 09046      | Bascuñana                          |
| 09050      | Berberana                          |
| 09052      | Berzosa de Bureba                  |
| 09061      | Cabañes de Esgueva                 |
| 09062      | Cabezón de la Sierra               |
| 09063      | Cavia                              |
| 09066      | Campolara                          |
| 09068      | Cantabrana                         |
| 09071      | Carcedo de Bureba                  |
| 09072      | Carcedo de Burgos                  |
| 09077      | Cascajares de Bureba               |
| 09079      | Castellanos de Castro              |
| 09082      | Castildelgado                      |
| 09083      | Castil de Peones                   |
| 09084      | Castrillo de la Reina              |
| 09088      | Castrillo de Riopisuerga           |
| 09090      | Castrillo Mota de Judíos           |
| 09093      | Cayuela                            |
| 09094      | Cebrecos                           |
| 09101      | Ciadoncha                          |
| 09102      | Cillaperlata                       |
| 09103      | Cilleruelo de Abajo                |
| 09108      | Cogollos                           |
| 09109      | Condado de Treviño                 |
| 09113      | Covarrubias                        |
| 09117      | Cueva de Roa, La                   |
| 09123      | Espinosa del Camino                |
| 09127      | Fontioso                           |
| 09128      | Frandovínez                        |
| 09129      | Fresneda de la Sierra Tirón        |
| 09130      | Fresneña                           |
| 09137      | Fuentelcésped                      |
| 09138      | Fuentelisendo                      |
| 09143      | Galbarros                          |
| 09148      | Grijalba                           |
| 09149      | Grisaleña                          |
| 09159      | Hontanas                           |
| 09167      | Hornillos del Camino               |
| 09169      | Hortigüela                         |
| 09173      | Huerta de Arriba                   |
| 09174      | Huerta de Rey                      |
| 09176      | Hurones                            |
| 09178      | Ibrillos                           |
| 09182      | Itero del Castillo                 |
| 09183      | Jaramillo de la Fuente             |
| 09184      | Jaramillo Quemado                  |
| 09190      | Junta de Villalba de Losa          |
| 09191      | Jurisdicción de Lara               |
| 09192      | Jurisdicción de San Zadornil       |
| 09195      | Llano de Bureba                    |
| 09198      | Mahamud                            |
| 09199      | Mambrilla de Castrejón             |
| 09200      | Mambrillas de Lara                 |
| 09202      | Manciles                           |
| 09206      | Mazuela                            |
| 09208      | Mecerreyes                         |
| 09216      | Merindad de Valdeporres            |
| 09220      | Miraveche                          |
| 09225      | Moncalvillo                        |
| 09226      | Monterrubio de la Demanda          |
| 09229      | Nava de Roa                        |
| 09230      | Navas de Bureba                    |
| 09231      | Nebreda                            |
| 09236      | Olmillos de Muñó                   |
| 09243      | Padilla de Arriba                  |
| 09244      | Padrones de Bureba                 |
| 09246      | Palacios de la Sierra              |
| 09248      | Palazuelos de la Sierra            |
| 09253      | Pardilla                           |
| 09257      | Pedrosa del Páramo                 |
| 09258      | Pedrosa del Príncipe               |
| 09261      | Peñaranda de Duero                 |
| 09262      | Peral de Arlanza                   |
| 09265      | Piérnigas                          |
| 09266      | Pineda de la Sierra                |
| 09269      | Pinilla de los Moros               |
| 09273      | Prádanos de Bureba                 |
| 09275      | Presencio                          |
| 09277      | Puentedura                         |
| 09280      | Quintanabureba                     |
| 09287      | Quintanaortuño                     |
| 09289      | Quintanar de la Sierra             |
| 09292      | Quintanavides                      |
| 09294      | Quintanilla de la Mata             |
| 09295      | Quintanilla del Coco               |
| 09298      | Quintanilla San García             |
| 09301      | Quintanilla Vivar                  |
| 09303      | Rábanos                            |
| 09304      | Rabé de las Calzadas               |
| 09310      | Reinoso                            |
| 09311      | Retuerta                           |
| 09316      | Revilla Vallejera                  |
| 09317      | Rezmondo                           |
| 09318      | Riocavado de la Sierra             |
| 09323      | Rojas                              |
| 09326      | Rubena                             |
| 09327      | Rublacedo de Abajo                 |
| 09328      | Rucandio                           |
| 09329      | Salas de Bureba                    |
| 09334      | Salinillas de Bureba               |
| 09335      | San Adrián de Juarros              |
| 09338      | San Mamés de Burgos                |
| 09339      | San Martín de Rubiales             |
| 09340      | San Millán de Lara                 |
| 09343      | Santa Cecilia                      |
| 09345      | Santa Cruz de la Salceda           |
| 09348      | Santa Inés                         |
| 09352      | Santa María del Mercadillo         |
| 09353      | Santa María Ribarredonda           |
| 09354      | Santa Olalla de Bureba             |
| 09355      | Santibáñez de Esgueva              |
| 09356      | Santibáñez del Val                 |
| 09360      | San Vicente del Valle              |
| 09366      | Solarana                           |
| 09372      | Sotragero                          |
| 09374      | Susinos del Páramo                 |
| 09375      | Tamarón                            |
| 09378      | Tejada                             |
| 09380      | Terradillos de Esgueva             |
| 09381      | Tinieblas de la Sierra             |
| 09382      | Tobar                              |
| 09388      | Torrelara                          |
| 09389      | Torrepadre                         |
| 09392      | Tosantos                           |
| 09396      | Tubilla del Lago                   |
| 09400      | Vadocondes                         |
| 09403      | Valdeande                          |
| 09405      | Valdezate                          |
| 09407      | Valmala                            |
| 09409      | Valle de Manzanedo                 |
| 09411      | Valle de Oca                       |
| 09413      | Valle de Valdebezana               |
| 09414      | Valle de Valdelaguna               |
| 09416      | Valle de Zamanzas                  |
| 09417      | Vallejera                          |
| 09418      | Valles de Palenzuela               |
| 09421      | Vid y Barrios, La                  |
| 09422      | Vid de Bureba, La                  |
| 09423      | Vileña                             |
| 09424      | Viloria de Rioja                   |
| 09425      | Vilviestre del Pinar               |
| 09428      | Villaescusa de Roa                 |
| 09430      | Villaespasa                        |
| 09431      | Villafranca Montes de Oca          |
| 09433      | Villagalijo                        |
| 09437      | Villahoz                           |
| 09438      | Villalba de Duero                  |
| 09440      | Villalbilla de Gumiel              |
| 09442      | Villalmanzo                        |
| 09443      | Villamayor de los Montes           |
| 09445      | Villambistia                       |
| 09446      | Villamedianilla                    |
| 09447      | Villamiel de la Sierra             |
| 09448      | Villangómez                        |
| 09454      | Villanueva de Teba                 |
| 09455      | Villaquirán de la Puebla           |
| 09466      | Villaverde del Monte               |
| 09467      | Villaverde-Mogina                  |
| 09471      | Villayerno Morquillas              |
| 09476      | Villoruebo                         |
| 09478      | Vizcaínos                          |
| 09482      | Zarzosa de Río Pisuerga            |
| 09485      | Zuñeda                             |
| 09901      | Quintanilla del Agua y Tordueles   |
| 09902      | Valle de Santibáñez                |
| 09904      | Valle de las Navas                 |
| 24001      | Acebedo                            |
| 24003      | Alija del Infantado                |
| 24005      | Antigua, La                        |
| 24006      | Ardón                              |
| 24007      | Arganza                            |
| 24011      | Barjas                             |
| 24012      | Barrios de Luna, Los               |
| 24015      | Benavides                          |
| 24017      | Bercianos del Páramo               |
| 24022      | Borrenes                           |
| 24024      | Burgo Ranero, El                   |
| 24025      | Burón                              |
| 24026      | Bustillo del Páramo                |
| 24028      | Cabreros del Río                   |
| 24029      | Cabrillanes                        |
| 24032      | Campazas                           |
| 24033      | Campo de Villavidel                |
| 24034      | Camponaraya                        |
| 24038      | Carracedelo                        |
| 24039      | Carrizo                            |
| 24040      | Carrocera                          |
| 24042      | Castilfalé                         |
| 24044      | Castrillo de la Valduerna          |
| 24046      | Castrocalbón                       |
| 24047      | Castrocontrigo                     |
| 24049      | Castropodame                       |
| 24051      | Cea                                |
| 24053      | Cebrones del Río                   |
| 24054      | Cimanes de la Vega                 |
| 24055      | Cimanes del Tejar                  |
| 24057      | Congosto                           |
| 24058      | Corbillos de los Oteros            |
| 24061      | Cuadros                            |
| 24062      | Cubillas de los Oteros             |
| 24066      | Destriana                          |
| 24071      | Folgoso de la Ribera               |
| 24074      | Fuentes de Carbajal                |
| 24083      | Igüeña                             |
| 24084      | Izagre                             |
| 24086      | Joarilla de las Matas              |
| 24087      | Laguna Dalga                       |
| 24088      | Laguna de Negrillos                |
| 24092      | Llamas de la Ribera                |
| 24094      | Mansilla de las Mulas              |
| 24096      | Maraña                             |
| 24098      | Matallana de Torío                 |
| 24099      | Matanza                            |
| 24104      | Omañas, Las                        |
| 24106      | Oseja de Sajambre                  |
| 24107      | Pajares de los Oteros              |
| 24108      | Palacios de la Valduerna           |
| 24114      | Pola de Gordón, La                 |
| 24117      | Pozuelo del Páramo                 |
| 24119      | Priaranza del Bierzo               |
| 24121      | Puebla de Lillo                    |
| 24122      | Puente de Domingo Flórez           |
| 24125      | Quintana y Congosto                |
| 24127      | Regueras de Arriba                 |
| 24129      | Reyero                             |
| 24130      | Riaño                              |
| 24131      | Riego de la Vega                   |
| 24133      | Rioseco de Tapia                   |
| 24136      | Roperuelos del Páramo              |
| 24137      | Sabero                             |
| 24146      | San Esteban de Nogales             |
| 24148      | San Justo de la Vega               |
| 24149      | San Millán de los Caballeros       |
| 24151      | Santa Colomba de Curueño           |
| 24153      | Santa Cristina de Valmadrigal      |
| 24155      | Santa María de la Isla             |
| 24156      | Santa María del Monte de Cea       |
| 24159      | Santa Marina del Rey               |
| 24160      | Santas Martas                      |
| 24164      | Sena de Luna                       |
| 24166      | Soto de la Vega                    |
| 24167      | Soto y Amío                        |
| 24169      | Toreno                             |
| 24170      | Torre del Bierzo                   |
| 24173      | Turcia                             |
| 24174      | Urdiales del Páramo                |
| 24176      | Valdefuentes del Páramo            |
| 24178      | Valdemora                          |
| 24180      | Valdepolo                          |
| 24181      | Valderas                           |
| 24183      | Valderrueda                        |
| 24184      | Valdesamario                       |
| 24185      | Val de San Lorenzo                 |
| 24187      | Valdevimbre                        |
| 24189      | Valverde de la Virgen              |
| 24190      | Valverde-Enrique                   |
| 24191      | Vallecillo                         |
| 24193      | Vecilla, La                        |
| 24194      | Vegacervera                        |
| 24198      | Vega de Valcarce                   |
| 24199      | Vegaquemada                        |
| 24202      | Villablino                         |
| 24203      | Villabraz                          |
| 24207      | Villademor de la Vega              |
| 24215      | Villamol                           |
| 24216      | Villamontán de la Valduerna        |
| 24217      | Villamoratiel de las Matas         |
| 24218      | Villanueva de las Manzanas         |
| 24221      | Villaquejida                       |
| 24222      | Villaquilambre                     |
| 24224      | Villares de Órbigo                 |
| 24226      | Villaselán                         |
| 24227      | Villaturiel                        |
| 24230      | Zotes del Páramo                   |
| 24902      | Villaornate y Castro               |
| 34009      | Amayuelas de Arriba                |
| 34011      | Amusco                             |
| 34012      | Antigüedad                         |
| 34015      | Arconada                           |
| 34018      | Autilla del Pino                   |
| 34022      | Baltanás                           |
| 34031      | Belmonte de Campos                 |
| 34033      | Boada de Campos                    |
| 34038      | Bustillo de la Vega                |
| 34039      | Bustillo del Páramo de Carrión     |
| 34041      | Calahorra de Boedo                 |
| 34045      | Capillas                           |
| 34046      | Cardeñosa de Volpejera             |
| 34048      | Castil de Vela                     |
| 34049      | Castrejón de la Peña               |
| 34050      | Castrillo de Don Juan              |
| 34051      | Castrillo de Onielo                |
| 34057      | Cevico de la Torre                 |
| 34058      | Cevico Navero                      |
| 34068      | Dehesa de Romanos                  |
| 34073      | Fresno del Río                     |
| 34082      | Hérmedes de Cerrato                |
| 34087      | Hornillos de Cerrato               |
| 34089      | Itero de la Vega                   |
| 34093      | Vid de Ojeda, La                   |
| 34096      | Lomas                              |
| 34106      | Meneses de Campos                  |
| 34112      | Nogal de las Huertas               |
| 34122      | Páramo de Boedo                    |
| 34126      | Pedrosa de la Vega                 |
| 34129      | Pino del Río                       |
| 34134      | Polentinos                         |
| 34136      | Poza de la Vega                    |
| 34137      | Pozo de Urama                      |
| 34143      | Quintanilla de Onsoña              |
| 34147      | Renedo de la Vega                  |
| 34156      | Riberos de la Cueza                |
| 34157      | Saldaña                            |
| 34165      | San Román de la Cuba               |
| 34167      | Santa Cecilia del Alcor            |
| 34168      | Santa Cruz de Boedo                |
| 34174      | Santoyo                            |
| 34175      | Serna, La                          |
| 34185      | Triollo                            |
| 34189      | Valdeolmillos                      |
| 34190      | Valderrábano                       |
| 34192      | Valde-Ucieza                       |
| 34201      | Vertavillo                         |
| 34204      | Villacidaler                       |
| 34205      | Villaconancio                      |
| 34211      | Villaherreros                      |
| 34218      | Villaluenga de la Vega             |
| 34220      | Villamartín de Campos              |
| 34221      | Villamediana                       |
| 34223      | Villamoronta                       |
| 34224      | Villamuera de la Cueza             |
| 34227      | Villanueva del Rebollar            |
| 34230      | Villarmentero de Campos            |
| 34236      | Villaturde                         |
| 34237      | Villaumbrales                      |
| 34240      | Villerías de Campos                |
| 34902      | Valle del Retortillo               |
| 34903      | Loma de Ucieza                     |
| 37002      | Agallas                            |
| 37004      | Ahigal de Villarino                |
| 37019      | Aldearrodrigo                      |
| 37020      | Aldearrubia                        |
| 37022      | Aldeaseca de la Frontera           |
| 37029      | Anaya de Alba                      |
| 37030      | Añover de Tormes                   |
| 37034      | Arco, El                           |
| 37060      | Buenavista                         |
| 37063      | Cabeza de Béjar, La                |
| 37065      | Cabeza del Caballo                 |
| 37071      | Calzada de Béjar, La               |
| 37078      | Candelario                         |
| 37080      | Cantagallo                         |
| 37096      | Castillejo de Martín Viejo         |
| 37098      | Cepeda                             |
| 37100      | Cerezal de Peñahorcada             |
| 37102      | Cerro, El                          |
| 37109      | Colmenar de Montemayor             |
| 37125      | Escurial de la Sierra              |
| 37126      | Espadaña                           |
| 37130      | Forfoleda                          |
| 37135      | Fuente de San Esteban, La          |
| 37139      | Fuentes de Béjar                   |
| 37145      | Gallegos de Argañán                |
| 37155      | Guijo de Ávila                     |
| 37157      | Herguijuela de Ciudad Rodrigo      |
| 37159      | Herguijuela del Campo              |
| 37161      | Horcajo de Montemayor              |
| 37162      | Horcajo Medianero                  |
| 37163      | Hoya, La                           |
| 37170      | Ledesma                            |
| 37175      | Machacón                           |
| 37182      | Martinamor                         |
| 37185      | Castellanos de Villiquera          |
| 37190      | Mieza                              |
| 37201      | Montemayor del Río                 |
| 37202      | Monterrubio de Armuña              |
| 37204      | Morasverdes                        |
| 37207      | Moriscos                           |
| 37212      | Navacarros                         |
| 37249      | Peralejos de Arriba                |
| 37257      | Pozos de Hinojo                    |
| 37259      | Puebla de San Medel                |
| 37262      | Puertas                            |
| 37265      | Rágama                             |
| 37268      | Rinconada de la Sierra, La         |
| 37274      | Salamanca                          |
| 37280      | Sanchón de la Ribera               |
| 37287      | San Miguel de Valero               |
| 37290      | San Pedro del Valle                |
| 37297      | Santibáñez de Béjar                |
| 37304      | Sepulcro-Hilario                   |
| 37307      | Serradilla del Llano               |
| 37310      | Sieteiglesias de Tormes            |
| 37316      | Tamames                            |
| 37320      | Tejeda y Segoyuela                 |
| 37327      | Torresmenudas                      |
| 37328      | Trabanca                           |
| 37332      | Valdehijaderos                     |
| 37333      | Valdelacasa                        |
| 37340      | Valsalabroso                       |
| 37341      | Valverde de Valdelacasa            |
| 37343      | Vallejera de Riofrío               |
| 37349      | Vídola, La                         |
| 37352      | Villagonzalo de Tormes             |
| 37355      | Villanueva del Conde               |
| 37359      | Villar de la Yegua                 |
| 37361      | Villar de Samaniego                |
| 37363      | Villares de Yeltes                 |
| 37372      | Villaverde de Guareña              |
| 37376      | Vitigudino                         |
| 37380      | Zarapicos                          |
| 40063      | Cuéllar                            |
| 40075      | Escobar de Polendos                |
| 40076      | Espinar, El                        |
| 40077      | Espirdo                            |
| 40091      | Fuentesoto                         |
| 40099      | Honrubia de la Cuesta              |
| 40126      | Melque de Cercos                   |
| 40132      | Moral de Hornuez                   |
| 40155      | Palazuelos de Eresma               |
| 40162      | Prádena                            |
| 40215      | Valtiendas                         |
| 40229      | Villaverde de Montejo              |
| 42011      | Aldealpozo                         |
| 42013      | Aldehuela de Periáñez              |
| 42024      | Arancón                            |
| 42027      | Arévalo de la Sierra               |
| 42141      | Póveda de Soria, La                |
| 42205      | Villaciervos                       |
| 42219      | Yelo                               |
| 47002      | Aguasal                            |
| 47008      | Almenara de Adaja                  |
| 47017      | Bercero                            |
| 47021      | Bocigas                            |
| 47068      | Fuente-Olmedo                      |
| 47076      | Laguna de Duero                    |
| 47079      | Llano de Olmedo                    |
| 47085      | Medina del Campo                   |
| 47091      | Monasterio de Vega                 |
| 47099      | Mudarra, La                        |
| 47104      | Olmedo                             |
| 47114      | Peñafiel                           |
| 47115      | Peñaflor de Hornija                |
| 47126      | Puras                              |
| 47132      | Ramiro                             |
| 47139      | Rueda                              |
| 47145      | San Miguel del Arroyo              |
| 47147      | San Pablo de la Moraleja           |
| 47149      | San Pelayo                         |
| 47156      | San Vicente del Palacio            |
| 47158      | Seca, La                           |
| 47161      | Simancas                           |
| 47162      | Tamariz de Campos                  |
| 47163      | Tiedra                             |
| 47166      | Torrecilla de la Abadesa           |
| 47168      | Torrecilla de la Torre             |
| 47180      | Valdearcos de la Vega              |
| 47183      | Valdunquillo                       |
| 47192      | Ventosa de la Cuesta               |
| 47196      | Villabaruz de Campos               |
| 47209      | Villalán de Campos                 |
| 47218      | Villanueva de Duero                |
| 47222      | Villanueva de San Mancio           |
| 49002      | Abezames                           |
| 49003      | Alcañices                          |
| 49006      | Algodre                            |
| 49013      | Argujillo                          |
| 49017      | Asturianos                         |
| 49018      | Ayoó de Vidriales                  |
| 49023      | Bermillo de Sayago                 |
| 49025      | Bretó                              |
| 49029      | Burganes de Valverde               |
| 49032      | Calzadilla de Tera                 |
| 49033      | Camarzana de Tera                  |
| 49036      | Carbajales de Alba                 |
| 49038      | Casaseca de Campeán                |
| 49039      | Casaseca de las Chanas             |
| 49042      | Castronuevo                        |
| 49048      | Cernadilla                         |
| 49050      | Cobreros                           |
| 49054      | Corrales del Vino                  |
| 49059      | Cuelgamures                        |
| 49063      | Faramontanos de Tábara             |
| 49067      | Ferreras de Arriba                 |
| 49068      | Ferreruela                         |
| 49069      | Figueruela de Arriba               |
| 49071      | Fonfría                            |
| 49075      | Fresno de la Polvorosa             |
| 49077      | Fresno de Sayago                   |
| 49078      | Friera de Valverde                 |
| 49084      | Fuentespreadas                     |
| 49085      | Galende                            |
| 49087      | Gallegos del Río                   |
| 49090      | Gema                               |
| 49092      | Granucillo                         |
| 49094      | Hermisende                         |
| 49098      | Losacino                           |
| 49099      | Losacio                            |
| 49100      | Lubián                             |
| 49101      | Luelmo                             |
| 49104      | Mahide                             |
| 49108      | Manganeses de la Lampreana         |
| 49110      | Manzanal de Arriba                 |
| 49111      | Manzanal del Barco                 |
| 49112      | Manzanal de los Infantes           |
| 49114      | Matilla la Seca                    |
| 49116      | Melgar de Tera                     |
| 49117      | Micereces de Tera                  |
| 49121      | Mombuey                            |
| 49123      | Montamarta                         |
| 49124      | Moral de Sayago                    |
| 49127      | Morales del Vino                   |
| 49128      | Morales de Rey                     |
| 49129      | Morales de Toro                    |
| 49130      | Morales de Valverde                |
| 49132      | Moreruela de los Infanzones        |
| 49135      | Muelas del Pan                     |
| 49138      | Olmillos de Castro                 |
| 49139      | Otero de Bodas                     |
| 49143      | Palacios de Sanabria               |
| 49149      | Peñausende                         |
| 49150      | Peque                              |
| 49153      | Perilla de Castro                  |
| 49154      | Pías                               |
| 49156      | Pinilla de Toro                    |
| 49163      | Pozoantiguo                        |
| 49164      | Pozuelo de Tábara                  |
| 49165      | Prado                              |
| 49166      | Puebla de Sanabria                 |
| 49167      | Pueblica de Valverde               |
| 49171      | Quiruelas de Vidriales             |
| 49172      | Rabanales                          |
| 49173      | Rábano de Aliste                   |
| 49176      | Riofrío de Aliste                  |
| 49177      | Rionegro del Puente                |
| 49179      | Robleda-Cervantes                  |
| 49181      | Rosinos de la Requejada            |
| 49185      | San Agustín del Pozo               |
| 49186      | San Cebrián de Castro              |
| 49187      | San Cristóbal de Entreviñas        |
| 49189      | San Justo                          |
| 49194      | San Pedro de la Nave-Almendra      |
| 49202      | Santa Eufemia del Barco            |
| 49205      | Santibáñez de Tera                 |
| 49206      | Santibáñez de Vidriales            |
| 49208      | San Vicente de la Cabeza           |
| 49209      | San Vitero                         |
| 49223      | Trabazos                           |
| 49224      | Trefacio                           |
| 49231      | Vega de Tera                       |
| 49237      | Videmala                           |
| 49238      | Villabrázaro                       |
| 49240      | Villadepera                        |
| 49241      | Villaescusa                        |
| 49245      | Villalazán                         |
| 49247      | Villalcampo                        |
| 49249      | Villalonso                         |
| 49257      | Villanueva de Azoague              |
| 49262      | Villardeciervos                    |
| 49264      | Villar del Buey                    |
| 49265      | Villardiegua de la Ribera          |
| 49267      | Villardondiego                     |
| 49270      | Villavendimio                      |
| 49273      | Viñas                              |

### Castilla-La Mancha

- Motivo: Ausente de la relación oficial de fiestas locales de 2026 del DOCM y de las resoluciones provinciales (BOP).
- Motivo: La relación oficial del DOCM contiene una sola fecha o un número no resoluble de fechas para este municipio en 2026.
- Motivo: La relación oficial del DOCM publica las fiestas por núcleos constituyentes o EATIMs, sin un par de fiestas de ámbito municipal.

| Código INE | Municipio                  |
| ---------- | -------------------------- |
| 16173      | Valle de Altomira, El      |
| 16272      | Villas de la Ventosa       |
| 16901      | Campos del Paraíso         |
| 16904      | Fuentenava de Jábaga       |
| 16908      | Pozorrubielos de la Mancha |
| 16909      | Sotorribas                 |
| 16910      | Villar y Velasco           |
| 19196      | Muduex                     |
| 19209      | Pardos                     |
| 19239      | Robledillo de Mohernando   |
| 19243      | Rueda de la Sierra         |
| 19246      | Saelices de la Sal         |
| 19285      | Torrubia                   |
| 19289      | Traíd                      |
| 45080      | Illán de Vacas             |

### Cataluña

- Motivo: El DOGC declara «proposta no formulada» para este municipio o publica sus fiestas locales únicamente a nivel de EMD con fechas distintas, sin un par de ámbito municipal demostrable para 2026.

| Código INE | Municipio                             |
| ---------- | ------------------------------------- |
| 08013      | Avinyonet del Penedès                 |
| 08014      | Aiguafreda                            |
| 08023      | Bigues i Riells del Fai               |
| 08031      | Calaf                                 |
| 08042      | Cànoves i Samalús                     |
| 08043      | Canyelles                             |
| 08050      | Castellar del Riu                     |
| 08058      | Castellet i la Gornal                 |
| 08059      | Castellfollit del Boix                |
| 08062      | Castellnou de Bages                   |
| 08086      | Franqueses del Vallès, Les            |
| 08092      | Gironella                             |
| 08127      | Monistrol de Montserrat               |
| 08139      | Mura                                  |
| 08142      | Nou de Berguedà, La                   |
| 08177      | Quar, La                              |
| 08185      | Rubió                                 |
| 08229      | Sant Mateu de Bages                   |
| 08256      | Santa Maria de Martorelles            |
| 08273      | Subirats                              |
| 08293      | Vallcebre                             |
| 08308      | Viver i Serrateix                     |
| 08903      | Sant Julià de Cerdanyola              |
| 17028      | Brunyola i Sant Martí Sapresa         |
| 17034      | Calonge i Sant Antoni                 |
| 17048      | Castell d'Aro, Platja d'Aro i s'Agaró |
| 17100      | Masarac i Vilarnadal                  |
| 17187      | Saus, Camallera i Llampaies           |
| 17207      | Vall d'en Bas, La                     |
| 17902      | Forallac                              |
| 25005      | Alàs i Cerc                           |
| 25024      | Alt Àneu                              |
| 25025      | Naut Aran                             |
| 25030      | Pont de Bar, El                       |
| 25037      | Avellanes i Santa Linya, Les          |
| 25043      | Vall de Boí, La                       |
| 25045      | Bausen                                |
| 25100      | Gósol                                 |
| 25115      | Isona i Conca Dellà                   |
| 25139      | Montellà i Martinet                   |
| 25161      | Conca de Dalt                         |
| 25185      | Ribera d'Urgellet                     |
| 25186      | Riner                                 |
| 25239      | Valls de Valira, Les                  |
| 25243      | Vielha e Mijaran                      |
| 25901      | Vall de Cardós                        |
| 25902      | Sant Martí de Riucorb                 |
| 25904      | Castell de Mur                        |
| 25906      | Valls d'Aguilar, Les                  |
| 25907      | Torrefeta i Florejacs                 |
| 25908      | Fígols i Alinyà                       |
| 25909      | Vansa i Fórnols, La                   |
| 25910      | Josa i Tuixén                         |
| 25912      | Gimenells i el Pla de la Font         |
| 43057      | Febró, La                             |
| 43162      | Vandellòs i l'Hospitalet de l'Infant  |

### Comunitat Valenciana

- Motivo: Sin par de fiestas locales en la resolución oficial del DOGV 10238 (y su modificación DOGV 10281) para 2026.

| Código INE | Municipio          |
| ---------- | ------------------ |
| 12097      | Sacañet            |
| 12132      | Vilanova d'Alcolea |
| 46186      | Paiporta           |

### Comunidad de Madrid

- Motivo: El BOCM publica días festivos por núcleo de población para este municipio (Valdeolmos y Alalpardo) sin un par de ámbito municipal.

| Código INE | Municipio            |
| ---------- | -------------------- |
| 28162      | Valdeolmos-Alalpardo |

### Navarra

- Motivo: La resolución oficial del BON solo fija la fiesta local de concejos para este municipio, sin fecha de ámbito municipal para 2026.

| Código INE | Municipio                                   |
| ---------- | ------------------------------------------- |
| 31011      | Allín/Allin                                 |
| 31013      | Améscoa Baja                                |
| 31017      | Anue                                        |
| 31020      | Araitz                                      |
| 31025      | Arakil                                      |
| 31028      | Arce/Artzi                                  |
| 31040      | Atetz                                       |
| 31049      | Basaburua                                   |
| 31054      | Bertizarana                                 |
| 31056      | Biurrun-Olcoz                               |
| 31076      | Cizur                                       |
| 31086      | Valle de Egüés/Eguesibar                    |
| 31088      | Valle de Elorz/Elortzibar                   |
| 31091      | Ergoiena                                    |
| 31095      | Esparza de Salazar/Espartza Zaraitzu        |
| 31098      | Esteribar                                   |
| 31101      | Ezcabarte                                   |
| 31118      | Val de Goñi/Goñerri                         |
| 31120      | Guesálaz/Gesalatz                           |
| 31124      | Ibargoiti                                   |
| 31126      | Imotz                                       |
| 31137      | Beintza-Labaien                             |
| 31139      | Lana                                        |
| 31144      | Larraun                                     |
| 31156      | Lizoain-Arriasgoiti/Lizoainibar-Arriasgoiti |
| 31158      | Lónguida/Longida                            |
| 31187      | Oiz                                         |
| 31193      | Cendea de Olza/Oltza Zendea                 |
| 31194      | Valle de Ollo/Ollaran                       |
| 31209      | Romanzado/Erromantzatua                     |
| 31228      | Tiebas-Muruarte de Reta                     |
| 31236      | Ultzama                                     |
| 31241      | Urraul Alto                                 |
| 31242      | Urraul Bajo                                 |
| 31243      | Urroz-Villa                                 |
| 31260      | Valle de Yerri/Deierri                      |

### País Vasco

- Motivo: El conjunto de datos oficial de Open Data Euskadi solo publica días locales de núcleos submunicipales para este municipio, sin día local de ámbito municipal para 2026.

| Código INE | Municipio      |
| ---------- | -------------- |
| 01010      | Ayala/Aiara    |
| 20024      | Bidania-Goiatz |
| 20031      | Elduain        |
| 20035      | Ezkio-Itsaso   |
| 20050      | Leaburu        |
| 20064      | Pasaia         |

### La Rioja

- Motivo: Ausente de la resolución oficial de fiestas locales de 2026 del BOR 159 o con una sola fecha; la cláusula de «fiestas tradicionales» no fija fechas concretas.

| Código INE | Municipio              |
| ---------- | ---------------------- |
| 26035      | Cabezón de Cameros     |
| 26071      | Haro                   |
| 26081      | Jalón de Cameros       |
| 26104      | Navajún                |
| 26107      | Nieva de Cameros       |
| 26113      | Pazuengos              |
| 26115      | Pinillos               |
| 26121      | Rabanera               |
| 26122      | Rasillo de Cameros, El |
| 26126      | Robres del Castillo    |
| 26129      | San Asensio            |
| 26140      | Santurde de Rioja      |
| 26154      | Torremontalbo          |

## Procedencia y licencias

`data/sources/2026/manifest.json` registra la URL exacta, autoridad, licencia, hora de descarga, ruta local y SHA-256 de cada entrada. Los archivos normalizados están vinculados a esos hashes, de modo que sustituir un archivo original sin auditar su derivación hace fallar la validación.

| Fuente                                                                                                                                                     | Uso                                                                                                 | Reutilización                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| [boe-2026-labour-calendar](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667)                                                                      | Agencia Estatal Boletín Oficial del Estado                                                          | AEBOE reuse conditions effective 2024-06-28                                                |
| [ine-municipalities-2026](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177031&idp=1254734710990)                              | Instituto Nacional de Estadística                                                                   | Creative Commons Attribution 4.0 International                                             |
| [andalucia-work-calendar](https://www.juntadeandalucia.es/datosabiertos/portal/dataset/calendario-de-dias-inhabiles-en-la-comunidad-autonoma-de-andalucia) | Junta de Andalucía, Consejería de Empleo, Empresa y Trabajo Autónomo                                | Creative Commons Attribution 4.0 International                                             |
| [euskadi-calendario-laboral-2026](https://opendata.euskadi.eus/catalogo/-/calendario-laboral-de-euskadi-para-el-2026/)                                     | Gobierno Vasco, Departamento de Economía, Trabajo y Empleo (Open Data Euskadi)                      | Creative Commons Attribution 4.0                                                           |
| [balears-calendari-laboral-2026](https://intranet.caib.es/opendatacataleg/dataset/calendari-laboral-general-i-local-illes-balears-2026)                    | Conselleria de Treball, Funció Pública i Diàleg Social, Govern de les Illes Balears (Dades Obertes) | CC BY (Open Definition), stated on the dataset page                                        |
| [borm-163-2025](https://www.carm.es/web/pagina/integra.servlets.Blob/pagina?IDCONTENIDO=75394&IDTIPO=100&RASTRO=c2135$m5897)                               | Comunidad Autónoma de la Región de Murcia, Consejería de Empresa, Empleo y Economía Social (BORM)   | Official gazette (BORM) reuse terms; PSI reuse, no explicit open-data license detected     |
| [bocm-20251212-34](https://www.comunidad.madrid/empleo/calendario-laboral-comunidad-madrid-municipios)                                                     | Comunidad de Madrid, Consejería de Economía, Hacienda y Empleo (BOCM)                               | Official gazette (BOCM) reuse terms; PSI reuse, no explicit open-data license detected     |
| [bocm-20251229-19](https://www.comunidad.madrid/empleo/calendario-laboral-comunidad-madrid-municipios)                                                     | Comunidad de Madrid, Consejería de Economía, Hacienda y Empleo (BOCM)                               | Official gazette (BOCM) reuse terms; PSI reuse, no explicit open-data license detected     |
| [doe-204-2025](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                           | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [docm-240-2025](https://calendariolaboral.castillalamancha.es/2026/calendarioIndex.php)                                                                    | Junta de Comunidades de Castilla-La Mancha, Consejería de Economía, Empresas y Empleo (DOCM)        | Official gazette (DOCM) reuse terms; open-data distribution precedent CC BY-SA 3.0 ES      |
| [docm-51-2026](https://calendariolaboral.castillalamancha.es/2026/calendarioIndex.php)                                                                     | Junta de Comunidades de Castilla-La Mancha, Consejería de Economía, Empresas y Empleo (DOCM)        | Official gazette (DOCM) reuse terms; open-data distribution precedent CC BY-SA 3.0 ES      |
| [bop-albacete-138-2025](https://bop.dipualba.es/)                                                                                                          | Delegación Provincial de Economía, Empresas y Empleo en Albacete (BOP Albacete)                     | Official provincial gazette (BOP Albacete); reuse per BOP aviso legal                      |
| [bop-ciudad-real-199-2025](https://bop.dipucr.es/buscador)                                                                                                 | Delegación Provincial de Economía, Empresas y Empleo en Ciudad Real (BOP Ciudad Real)               | Official provincial gazette (BOP Ciudad Real); reuse per BOP aviso legal                   |
| [cyl-fiestas-locales-api](https://analisis.datosabiertos.jcyl.es/explore/dataset/fiestas-locales-calendario-de-fiestas-de-caracter-local/)                 | Junta de Castilla y León, Consejería de Industria, Comercio y Empleo (Open Data CyL)                | Creative Commons Attribution 4.0 España                                                    |
| [bop-avila-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                              | Oficina Territorial de Trabajo de Ávila, Junta de Castilla y León (BOP de Ávila)                    | Official provincial gazette (BOP de Ávila); reuse per Diputación aviso legal               |
| [bop-burgos-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                             | Oficina Territorial de Trabajo de Burgos, Junta de Castilla y León (BOPBUR)                         | Official provincial gazette (BOPBUR); reuse per Diputación aviso legal                     |
| [bop-leon-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                               | Oficina Territorial de Trabajo de León, Junta de Castilla y León (BOP León)                         | Official provincial gazette (BOP León); reuse per Diputación aviso legal                   |
| [bop-palencia-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                           | Oficina Territorial de Trabajo de Palencia, Junta de Castilla y León (BOP Palencia)                 | Official provincial gazette (BOP Palencia); reuse per Diputación aviso legal               |
| [bop-salamanca-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                          | Oficina Territorial de Trabajo de Salamanca, Junta de Castilla y León (BOP Salamanca)               | Official provincial gazette (BOP Salamanca); reuse per Diputación aviso legal              |
| [bop-segovia-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                            | Oficina Territorial de Trabajo de Segovia, Junta de Castilla y León (BOP Segovia)                   | Official provincial gazette (BOP Segovia); reuse per Diputación aviso legal                |
| [bop-soria-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                              | Oficina Territorial de Trabajo de Soria, Junta de Castilla y León (BOP Soria)                       | Official provincial gazette (BOP Soria); reuse per Diputación aviso legal                  |
| [bop-valladolid-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                         | Oficina Territorial de Trabajo de Valladolid, Junta de Castilla y León (BOP Valladolid)             | Official provincial gazette (BOP Valladolid); reuse per Diputación aviso legal             |
| [bop-zamora-2026](https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html)                                             | Oficina Territorial de Trabajo de Zamora, Junta de Castilla y León (BOP Zamora)                     | Official provincial gazette (BOP Zamora); reuse per Diputación aviso legal                 |
| [bopa-114-2025](https://sede.asturias.es/bopa)                                                                                                             | Principado de Asturias, Consejería de Ciencia, Industria y Empleo (BOPA)                            | Official gazette (BOPA); Principado open-data policy, reuse by attribution                 |
| [boc-238-2025](https://dgte.cantabria.es/-/calendario-fiestas-laborales-2026)                                                                              | Gobierno de Cantabria, Dirección General de Trabajo, Economía Social y Empleo Autónomo (BOC)        | Official gazette (BOC); portal content CC BY 3.0 España, bulletin reuse per aviso legal    |
| [bor-159-2025](https://www.larioja.org/relaciones-laborales/es/calendario-festivos-laborales-2026)                                                         | Gobierno de La Rioja, Dirección General de Trabajo y Salud Laboral (BOR)                            | Official gazette (BOR); public service access, reuse per larioja.org aviso legal           |
| [bon-241-2025](https://www.lexnavarra.navarra.es/detalle.asp?r=58256)                                                                                      | Gobierno de Navarra, Dirección General de Economía Social y Trabajo (BON)                           | Official gazette (BON); Gobierno de Navarra open-data policy (CC BY 4.0 for datasets)      |
| [bon-1-2026-765](https://bon.navarra.es/es/anuncio/-/texto/2026/1/25)                                                                                      | Gobierno de Navarra, Dirección General de Economía Social y Trabajo (BON)                           | Official gazette (BON); Gobierno de Navarra open-data policy (CC BY 4.0 for datasets)      |
| [dog-210-2025](https://www.xunta.gal/dog/Publicados/2025/20251030/AnuncioG0767-221025-0001_es.html)                                                        | Xunta de Galicia, Consellería de Emprego, Comercio e Emigración (DOG)                               | Official gazette (DOG); Xunta open-data catalogue (datos.gal) CC BY 4.0                    |
| [dog-210-2025-pdf](https://www.xunta.gal/dog/Publicados/2025/20251030/AnuncioG0767-221025-0001_es.html)                                                    | Xunta de Galicia, Consellería de Emprego, Comercio e Emigración (DOG)                               | Official gazette (DOG); Xunta open-data catalogue (datos.gal) CC BY 4.0                    |
| [boa-225-2025](https://www.aragon.es/trabajo-y-relaciones-laborales/calendario-laboral)                                                                    | Gobierno de Aragón, Dirección General de Trabajo (BOA)                                              | Official gazette (BOA); CC BY 4.0 (boa.aragon.es footer)                                   |
| [boa-56-2026](https://www.aragon.es/trabajo-y-relaciones-laborales/calendario-laboral)                                                                     | Gobierno de Aragón, Dirección General de Trabajo (BOA)                                              | Official gazette (BOA); CC BY 4.0 (boa.aragon.es footer)                                   |
| [dogc-emt208-2025](https://dogc.gencat.cat/ca/document-del-dogc/?documentId=1032232)                                                                       | Generalitat de Catalunya, Departament d'Empresa i Treball (DOGC)                                    | Official gazette (DOGC); Generalitat dades obertes policy (CC BY 4.0 for datasets)         |
| [dogc-emt3-2026](https://dogc.gencat.cat/ca/document-del-dogc/?documentId=1034587)                                                                         | Generalitat de Catalunya, Departament d'Empresa i Treball (DOGC)                                    | Official gazette (DOGC); Generalitat dades obertes policy (CC BY 4.0 for datasets)         |
| [dogv-10238-2025](https://dogv.gva.es/)                                                                                                                    | Generalitat Valenciana, Conselleria d'Educació, Cultura, Universitats i Ocupació (DOGV)             | Official gazette (DOGV); GVA open-data policy (CC BY 4.0 for datasets)                     |
| [doe-24-2026-26060276](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-58-2026-26060628](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-64-2026-26060720](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-68-2026-26060780](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-81-2026-26060941](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-98-2026-26061253](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                   | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [doe-141-2026-26061914](https://www.juntaex.es/w/calendario-laboral-2026)                                                                                  | Junta de Extremadura, Consejería de Economía, Empleo y Transformación Digital (DOE)                 | Official gazette (DOE) reuse terms; PSI reuse, no explicit open-data license detected      |
| [boc-decreto-61-2025](https://www.gobiernodecanarias.org/boc/2025/088/1659.html)                                                                           | Gobierno de Canarias, Consejería de Turismo y Empleo (BOC)                                          | Official bulletin (BOC); legal texts outside copyright (LPI art. 13), reuse by attribution |
| [boc-orden-3029-2025](https://www.gobiernodecanarias.org/boc/2025/165/3029.html)                                                                           | Gobierno de Canarias, Consejería de Turismo y Empleo (BOC)                                          | Official bulletin (BOC); legal texts outside copyright (LPI art. 13), reuse by attribution |
| [bocce-6551-2025](https://www.ceuta.es/ceuta/documentos/secciones/bocces)                                                                                  | Ciudad Autónoma de Ceuta, Presidencia (BOCCE)                                                       | Official bulletin (BOCCE); no explicit open license; attribution and citation required     |
| [bome-2025-1033](https://www.melilla.es/melillaPortal/contenedor.jsp?seccion=s_fact_d4_v1.jsp&contenido=41767&nivel=1400&tipo=2&anuncio=1)                 | Ciudad Autónoma de Melilla, Consejo de Gobierno (BOME)                                              | Official bulletin (BOME); no explicit open license; attribution and citation required      |
| [bocm-20260108-18](https://www.comunidad.madrid/empleo/calendario-laboral-comunidad-madrid-municipios)                                                     | Comunidad de Madrid, Consejería de Economía, Hacienda y Empleo (BOCM)                               | Official gazette (BOCM) reuse terms; PSI reuse, no explicit open-data license detected     |
| [dogv-10281-2026](https://dogv.gva.es/)                                                                                                                    | Generalitat Valenciana, Conselleria d'Educació, Cultura, Universitats i Ocupació (DOGV)             | Official gazette (DOGV); GVA open-data policy (CC BY 4.0 for datasets)                     |

Los calendarios generados son datos adaptados y combinados. No deben presentarse como oficiales, avalados ni continuamente actualizados.

## Ruta rápida para colaboradores

Requiere Node.js 22 o posterior y Python 3 solo para los pasos de extracción auditada.

```sh
npm ci
npm run verify
```

`verify` comprueba formato, lint, tipos, tests, generación, sumas de comprobación de fuentes, estructura de calendarios, invariantes de cobertura y una segunda reconstrucción byte a byte. El CI de pull-request no accede a la red y falla si los archivos generados confirmados difieren de una construcción nueva.

## Actualizar las fuentes oficiales

La actualización está deliberadamente separada de las construcciones normales y del CI:

```sh
npm run sources:check
npm run sources:refresh
python3 scripts/extract-ine-xlsx.py
python3 scripts/prep/prep-boe.py
python3 scripts/prep/prep-<comunidad>.py   # por comunidad
npm run verify
```

Tras cualquier cambio de hash, un mantenedor debe comparar de forma independiente los archivos normalizados afectados con la nueva instantánea antes de actualizar su `sourceSha256`. Después ejecute `npm run verify`, revise el diff de cobertura y confirme juntos la instantánea, las derivaciones, la documentación y la salida generada.

Añadir otra comunidad autónoma significa añadir un adaptador aislado de fuente oficial y un contrato de cobertura medido. No debe debilitar la regla de que solo los municipios con evidencia completa e inequívoca reciben un archivo anunciado.
