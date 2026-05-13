const CHUNK_SIZE = 50;
let visibleCount = 0;
let filteredEvents = [];

// KRISTALL_OUTER = outer silhouette only (first sub-path), used as the coloured
// base for featured icons so that the facet holes show through in the accent colour.
const KRISTALL_OUTER = "M138.657303,28.517735   C146.050125,22.916147 152.092194,23.738714 158.558838,30.729765   C185.689545,60.060654 212.861816,89.353088 240.010941,118.666939   C247.025681,126.241005 254.003220,133.849503 261.015717,141.425644   C263.277466,143.869171 264.347839,146.728302 264.316040,150.045334   C264.145264,167.847733 262.599823,185.576996 261.515686,203.331177   C261.079987,210.466568 260.882904,217.609711 260.411743,224.750656   C258.474457,254.112854 256.946472,283.502258 255.302246,312.883575   C254.177414,332.983215 252.869858,353.077515 252.156357,373.192383   C251.932175,379.512695 250.024887,384.291534 245.460449,388.578369   C221.547668,411.036743 197.783157,433.652893 173.947144,456.193115   C167.655197,462.143005 161.309692,468.036621 154.956757,473.921509   C149.818848,478.680908 145.328018,478.874847 140.033768,474.051758   C122.796875,458.348785 105.697311,442.495178 88.520966,426.725647   C76.132774,415.352081 64.101189,403.542450 51.154858,392.841614   C42.876194,385.998840 39.923889,377.834717 39.787407,367.711090   C39.616905,355.063812 39.064960,342.421844 38.688187,329.777252   C37.994343,306.491821 37.655338,283.189484 36.538605,259.924438   C34.799309,223.689362 33.507641,187.444916 32.602081,151.181580   C32.453022,145.212448 34.657768,140.771973 38.639645,136.508789   C56.932762,116.923302 74.999825,97.126892 93.193771,77.448479   C108.225090,61.190731 123.320442,44.992184 138.657303,28.517735";

const KRISTALL_PATH = "M138.657303,28.517735   C146.050125,22.916147 152.092194,23.738714 158.558838,30.729765   C185.689545,60.060654 212.861816,89.353088 240.010941,118.666939   C247.025681,126.241005 254.003220,133.849503 261.015717,141.425644   C263.277466,143.869171 264.347839,146.728302 264.316040,150.045334   C264.145264,167.847733 262.599823,185.576996 261.515686,203.331177   C261.079987,210.466568 260.882904,217.609711 260.411743,224.750656   C258.474457,254.112854 256.946472,283.502258 255.302246,312.883575   C254.177414,332.983215 252.869858,353.077515 252.156357,373.192383   C251.932175,379.512695 250.024887,384.291534 245.460449,388.578369   C221.547668,411.036743 197.783157,433.652893 173.947144,456.193115   C167.655197,462.143005 161.309692,468.036621 154.956757,473.921509   C149.818848,478.680908 145.328018,478.874847 140.033768,474.051758   C122.796875,458.348785 105.697311,442.495178 88.520966,426.725647   C76.132774,415.352081 64.101189,403.542450 51.154858,392.841614   C42.876194,385.998840 39.923889,377.834717 39.787407,367.711090   C39.616905,355.063812 39.064960,342.421844 38.688187,329.777252   C37.994343,306.491821 37.655338,283.189484 36.538605,259.924438   C34.799309,223.689362 33.507641,187.444916 32.602081,151.181580   C32.453022,145.212448 34.657768,140.771973 38.639645,136.508789   C56.932762,116.923302 74.999825,97.126892 93.193771,77.448479   C108.225090,61.190731 123.320442,44.992184 138.657303,28.517735  M123.305115,396.509918   C123.342659,405.675079 123.328262,414.840942 123.452522,424.004944   C123.485558,426.441223 123.364059,428.934631 125.599899,430.878479   C131.883911,436.341736 138.051086,441.940247 144.223831,447.530182   C146.541229,449.628754 148.457947,450.025452 151.034576,447.551544   C157.397552,441.442169 164.025833,435.607635 170.593811,429.714233   C172.205429,428.268188 172.864166,426.566467 172.953659,424.442108   C173.808701,404.145569 174.819107,383.855072 175.571121,363.554901   C176.421722,340.593536 176.713409,317.605835 177.946136,294.667053   C178.437973,285.514709 178.455307,276.368744 178.854370,267.225616   C179.870178,243.952377 180.663437,220.669342 181.704956,197.397339   C181.892151,193.214661 180.347534,191.912552 176.282562,191.878860   C159.457870,191.739471 142.635498,191.330048 125.811913,191.041214   C119.228630,190.928177 119.126640,190.995712 119.255745,197.713760   C119.873291,229.848389 120.638687,261.980591 121.137222,294.117004   C121.661629,327.921295 122.048683,361.727173 123.305115,396.509918  M81.548332,391.942200   C88.295135,397.972382 95.041939,404.002563 101.945496,410.172852   C103.128639,407.945007 102.674408,406.264069 102.686584,404.648956   C102.764381,394.326111 102.133926,384.014221 101.949326,373.706024   C101.388947,342.414276 100.491432,311.129791 99.957047,279.840942   C99.459518,250.710297 98.134384,221.587677 98.618324,192.440674   C98.656891,190.118073 98.405701,187.790741 98.292107,185.465485   C98.152596,182.609802 96.660667,181.186417 93.914055,180.222931   C82.612946,176.258667 71.406677,172.024277 60.158310,167.908997   C58.468987,167.290939 56.784946,166.455109 54.902901,167.131531   C53.921124,168.714096 54.280960,170.427643 54.335133,172.048004   C55.341438,202.146698 56.165344,232.254501 57.573387,262.334839   C57.978287,270.984924 58.040489,279.634949 58.445686,288.277100   C59.723221,315.524994 61.116035,342.767914 62.251705,370.021606   C62.398163,373.536316 63.538422,375.946503 66.119240,378.152649   C71.181297,382.479919 76.064453,387.016479 81.548332,391.942200  M233.705444,314.538422   C236.143158,265.811005 238.580872,217.083603 241.074799,167.232880   C228.177795,173.064636 216.684570,178.257919 205.195541,183.460480   C203.318054,184.310638 203.385300,186.021118 203.308487,187.714554   C202.675308,201.674179 201.819412,215.626694 201.402664,229.592468   C200.668106,254.208496 199.310593,278.798370 198.429535,303.403442   C197.250656,336.325165 196.296371,369.251648 194.300613,402.138367   C194.230453,403.294769 193.564194,404.792725 195.441910,405.828888   C206.396622,395.951477 217.393326,386.040375 228.383392,376.121887   C229.789612,374.852753 230.644791,373.363312 230.746399,371.361023   C231.691269,352.742096 232.696259,334.126221 233.705444,314.538422  M174.489899,169.893845   C183.088364,171.002136 190.902008,168.838257 198.217865,164.360245   C200.049911,163.238861 202.130844,162.529327 204.076340,161.587082   C213.470139,157.037445 222.856766,152.472992 233.075958,147.510742   C207.542313,117.945435 181.069122,90.266533 154.799637,60.771126   C142.849930,97.633858 131.271439,133.351471 119.425697,169.893524   C138.260559,169.893524 155.876907,169.893524 174.489899,169.893845  M74.234901,151.160446   C83.109688,154.361465 91.871796,157.904724 101.386978,160.508621   C111.711998,131.217224 120.291267,101.782471 128.541168,71.983711   C105.551384,96.154175 82.561592,120.324646 59.214722,144.870529   C64.084526,147.830917 68.921501,149.075516 74.234901,151.160446  z";

function getKristallIcon(visible = false, crystalColor = null) {
  const visibilityClass = visible ? "visible" : "";
  const featuredClass = crystalColor ? " featured" : "";
  const paths = crystalColor
    ? `<path fill="${crystalColor}" d=" ${KRISTALL_OUTER}" />
       <path fill="currentColor" fill-rule="evenodd" d=" ${KRISTALL_PATH}" />`
    : `<path fill="currentColor" stroke="currentColor" stroke-width="2" d=" ${KRISTALL_PATH}" />`;
  return `<span class="filter-icon${featuredClass} ${visibilityClass}">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 288 480" width="1em" height="1em">
      ${paths}
    </svg>
  </span>`;
}

function renderRows() {
  const tbody = document.getElementById("tbody");
  tbody.innerHTML = '';
  
  const isMobile = window.innerWidth < 768;
  
  document.getElementById("header-date").innerHTML =
    `<span class="has-icon date-header-label" onclick="toggleDateDropdown(event)">När${getKristallIcon(currentFilter.date !== null)}</span>` +
    `<div id="date-dropdown" class="date-dropdown"></div>`;
  const hdrEvent = document.getElementById("header-event");
  if (wowMode === 'on') {
    hdrEvent.innerHTML =
      `<span class="event-header"><span>Vad</span>` +
      `<a href="#" class="wow-link${currentFilter.wow ? ' active' : ''}" onclick="toggleWowFilter(event)">(WoW)</a>` +
      `<span></span></span>`;
  } else {
    hdrEvent.innerHTML = `Vad`;
  }
  document.getElementById("header-venue").innerHTML =
    `<span class="venue-header"><span class="has-icon">Var${getKristallIcon(currentFilter.venue !== null)}</span><a href="/om" class="om-link">(om<span class="om-kristall"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 288 480" width="1em" height="1em" style="vertical-align:middle"><path fill="currentColor" stroke="currentColor" stroke-width="2" d=" ${KRISTALL_PATH}" /></svg></span>)</a></span>`;
  document.getElementById("header-category").innerHTML =
    `<span class="has-icon">${isMobile ? 'Konst' : 'Konstform'}${getKristallIcon(currentFilter.category !== null)}</span>`;
  
  visibleCount = 0;
  filteredEvents = applyFilters();

  if (filteredEvents.length === 0) {
    const isFiltered = currentFilter.date || currentFilter.venue || currentFilter.category;
    if (isFiltered) {
      trackFilterEmpty(currentFilter);
      tbody.innerHTML = `<tr><td colspan="4" style="padding: 1em; opacity: 0.55;">
        Inga evenemang matchar filtret. <a href="#" id="clear-filter">Rensa filter</a>
      </td></tr>`;
      document.getElementById('clear-filter').addEventListener('click', e => {
        e.preventDefault();
        trackFilterReset();
        currentFilter = { date: null, venue: null, category: null, wow: currentFilter.wow };
        renderRows();
      });
    } else {
      tbody.innerHTML = `<tr><td colspan="4" style="padding: 1em; opacity: 0.55;">Inga kommande evenemang.</td></tr>`;
    }
    return;
  }

  renderChunk();
}

// ── Feed-end data ─────────────────────────────────────────────────────────────

const NAMEDAYS = {
  "01-01":[],"01-02":["Svea"],"01-03":["Alfred","Alfrida"],"01-04":["Rut"],
  "01-05":["Hanna","Hannele"],"01-06":["Baltsar","Kasper","Melker"],
  "01-07":["August","Augusta"],"01-08":["Erland"],"01-09":["Gunder","Gunnar"],
  "01-10":["Sigbritt","Sigurd"],"01-11":["Jan","Jannike"],
  "01-12":[],"01-13":["Knut"],"01-14":["Felicia","Felix"],
  "01-15":["Laura","Lorentz"],"01-16":["Helmer","Hjalmar"],
  "01-17":["Anton","Tony"],"01-18":["Hilda","Hildur"],"01-19":["Henrik"],
  "01-20":["Fabian","Sebastian"],"01-21":["Agnes","Agneta"],
  "01-22":["Viktor","Vincent"],"01-23":["Frej","Freja"],"01-24":["Erika"],
  "01-25":["Pål","Paul"],"01-26":["Bodil","Boel"],"01-27":[],
  "01-28":["Karl","Karla"],"01-29":["Diana"],"01-30":["Gunhild","Gunilla"],
  "01-31":["Ivar","Joar"],
  "02-01":["Max","Maximilian"],"02-02":[],"02-03":[],
  "02-04":[],"02-05":["Agata","Agda"],
  "02-06":["Doris","Dorotea"],"02-07":["Dick","Rikard"],"02-08":["Bert","Berta"],
  "02-09":["Fanny","Franciska"],"02-10":["Iris"],"02-11":["Inge","Yngve"],
  "02-12":["Evelina","Evy"],"02-13":["Ove"],"02-14":["Valentin"],
  "02-15":["Sigfrid"],"02-16":["Julia","Julius"],"02-17":["Alexandra","Sandra"],
  "02-18":["Frida","Fritiof"],"02-19":["Ella","Gabriella"],"02-20":["Vivianne"],
  "02-21":["Hilding"],"02-22":["Pia"],"02-23":["Torsten","Torun"],
  "02-24":["Mats","Mattias"],"02-25":[],
  "02-26":[],"02-27":[],"02-28":["Maria"],"02-29":[],
  "03-01":["Albin","Elvira"],"03-02":["Erna","Ernst"],
  "03-03":[],"03-04":["Adrian","Adriana"],
  "03-05":["Tora","Tove"],"03-06":["Ebba","Ebbe"],"03-07":["Camilla"],
  "03-08":["Siv"],"03-09":["Torbjörn"],"03-10":["Ada"],
  "03-11":["Egon"],"03-12":["Viktoria"],"03-13":["Greger"],
  "03-14":["Matilda","Maud"],"03-15":["Christel","Kristoffer"],
  "03-16":["Gilbert","Herbert"],"03-17":["Gertrud"],
  "03-18":["Edvard"],"03-19":["Josef","Josefina"],
  "03-20":["Joakim","Kim"],"03-21":["Bengt"],"03-22":["Kennet","Kent"],
  "03-23":["Gerd","Gerda"],"03-24":["Gabriel","Rafael"],"03-25":[],
  "03-26":["Emanuel"],"03-27":["Ralf","Rudolf"],"03-28":["Malkolm","Morgan"],
  "03-29":["Jens","Jonas"],"03-30":["Holger"],"03-31":["Ester"],
  "04-01":["Harald","Hervor"],"04-02":[],
  "04-03":["Nanna"],"04-04":["Marianne","Marlene"],
  "04-05":["Irene","Irja"],"04-06":["Vilhelm","William"],
  "04-07":["Irma","Irmelin"],"04-08":["Nadja","Tanja"],
  "04-09":["Otto"],"04-10":["Ingvar","Ingvor"],
  "04-11":["Ulf","Ylva"],"04-12":["Liv"],"04-13":["Artur","Douglas"],
  "04-14":[],"04-15":["Oliver","Olivia"],
  "04-16":["Patricia","Patrik"],"04-17":["Elias","Elis"],
  "04-18":[],"04-19":["Ola","Olaus"],
  "04-20":["Amalia","Amelie"],"04-21":["Anneli","Annika"],
  "04-22":["Allan","Glenn"],"04-23":["Georg","Göran"],"04-24":["Vega"],
  "04-25":["Markus"],"04-26":["Terese","Teresia"],"04-27":[],
  "04-28":["Ture","Tyra"],"04-29":[],"04-30":["Mariana"],
  "05-01":["Valborg"],"05-02":["Filip","Filippa"],"05-03":["Jane","John"],
  "05-04":["Mona","Monika"],"05-05":[],
  "05-06":["Marit","Rita"],"05-07":["Carina","Carita"],"05-08":["Åke"],
  "05-09":["Reidar","Reidun"],"05-10":[],
  "05-11":["Märit","Märta"],"05-12":["Charlotta","Lotta"],
  "05-13":["Linn","Linnea"],"05-14":[],
  "05-15":["Sofia","Sonja"],"05-16":["Ronald","Ronny"],
  "05-17":["Rebecka","Ruben"],"05-18":["Erik"],"05-19":["Maj","Majken"],
  "05-20":["Carola","Karolina"],"05-21":["Conny","Konstantin"],
  "05-22":[],"05-23":["Desideria","Desirée"],
  "05-24":["Ivan","Vanja"],"05-25":["Urban"],"05-26":["Vilhelmina","Vilma"],
  "05-27":["Blenda"],"05-28":["Ingeborg"],
  "05-29":["Jeanette","Yvonne"],"05-30":["Vera","Veronika"],
  "05-31":["Pernilla"],
  "06-01":["Gun","Gunnel"],"06-02":["Roger","Rutger"],
  "06-03":[],"06-04":["Solveig"],"06-05":["Bo"],
  "06-06":["Gösta","Gustav"],"06-07":["Robert","Robin"],
  "06-08":[],"06-09":["Birger","Börje"],
  "06-10":["Boris","Svante"],"06-11":["Berthold","Bertil"],"06-12":[],
  "06-13":["Aina","Aino"],"06-14":["Håkan","Hakon"],
  "06-15":["Margit","Margot"],"06-16":["Axel","Axelina"],
  "06-17":[],"06-18":["Bjarne","Björn"],
  "06-19":[],"06-20":["Linda"],"06-21":["Alf","Alvar"],
  "06-22":["Paula","Paulina"],"06-23":["Adolf","Alice"],"06-24":[],
  "06-25":["David","Salomon"],"06-26":["Lea","Rakel"],
  "06-27":["Selma"],"06-28":["Leo"],"06-29":["Peter","Petra"],
  "06-30":["Leif"],
  "07-01":["Aron","Mirjam"],"07-02":["Rosa","Rosita"],"07-03":["Aurora"],
  "07-04":["Ulla","Ulrika"],"07-05":["Laila"],
  "07-06":["Jessika"],"07-07":[],"07-08":[],
  "07-09":["Jörgen","Örjan"],"07-10":["André","Andrea"],
  "07-11":["Eleonora","Ellinor"],"07-12":["Herman","Hermine"],
  "07-13":["Joel","Judit"],"07-14":[],"07-15":[],
  "07-16":[],"07-17":[],
  "07-18":["Fredrik","Fritz"],"07-19":["Sara"],"07-20":["Greta","Margareta"],
  "07-21":["Johanna"],"07-22":["Madeleine","Magdalena"],"07-23":["Emma"],
  "07-24":["Kerstin","Kristina"],"07-25":["Jakob"],"07-26":["Jesper"],
  "07-27":["Marta"],"07-28":[],"07-29":["Olof"],
  "07-30":[],"07-31":["Elin","Helena"],
  "08-01":["Per"],"08-02":["Kajsa","Karin"],"08-03":["Tage"],
  "08-04":["Arne","Arnold"],"08-05":["Alrik","Ulrik"],
  "08-06":["Alfons","Inez"],"08-07":["Denise","Dennis"],
  "08-08":["Silvia","Sylvia"],"08-09":["Roland"],"08-10":["Lars"],
  "08-11":["Susanna"],"08-12":["Klara"],"08-13":["Kaj"],"08-14":["Uno"],
  "08-15":["Estelle","Stella"],"08-16":[],
  "08-17":["Valter","Verner"],"08-18":["Ellen","Lena"],
  "08-19":["Magnus","Måns"],"08-20":["Bernhard","Bernt"],
  "08-21":["Jon","Jonna"],"08-22":["Henrietta","Henrika"],
  "08-23":["Signe","Signhild"],"08-24":[],
  "08-25":["Louise","Lovisa"],"08-26":[],"08-27":["Raoul","Rolf"],
  "08-28":["Fatima","Leila"],"08-29":["Hampus","Hans"],
  "08-30":["Albert","Albertina"],"08-31":["Arvid","Vidar"],
  "09-01":["Sam","Samuel"],"09-02":["Justina","Justus"],
  "09-03":["Alva"],"09-04":["Gisela"],"09-05":["Adela","Heidi"],
  "09-06":["Lilian","Lilly"],"09-07":["Kevin","Roy"],"09-08":["Alma","Hulda"],
  "09-09":["Anita","Annette"],"09-10":["Tord","Turid"],
  "09-11":["Dagny","Helny"],"09-12":["Åsa","Åslög"],"09-13":["Sture"],
  "09-14":["Ida"],"09-15":["Sigrid","Siri"],"09-16":["Dag","Daga"],
  "09-17":["Hildegard","Magnhild"],"09-18":[],"09-19":["Fredrika"],
  "09-20":["Elise","Lisa"],"09-21":["Matteus"],"09-22":[],
  "09-23":["Tea","Tekla"],"09-24":["Gerhard","Gert"],"09-25":[],
  "09-26":["Einar"],"09-27":[],
  "09-28":["Lennart","Leonard"],"09-29":["Mikael","Mikaela"],
  "09-30":["Helge"],
  "10-01":["Ragna","Ragnar"],"10-02":["Love","Ludvig"],
  "10-03":[],"10-04":["Frank","Frans"],"10-05":["Bror"],
  "10-06":["Jennifer","Jenny"],"10-07":["Birgitta","Britta"],"10-08":["Nils"],
  "10-09":["Inger","Ingrid"],"10-10":["Harriet","Harry"],
  "10-11":[],"10-12":[],
  "10-13":["Berit","Birgit"],"10-14":["Stellan"],
  "10-15":["Hedvig","Hillevi"],"10-16":["Finn"],"10-17":["Antonia","Toini"],
  "10-18":["Lukas"],"10-19":["Tor","Tore"],"10-20":["Sibylla"],
  "10-21":["Ursula","Yrsa"],"10-22":["Marika","Marita"],
  "10-23":["Severin","Sören"],"10-24":["Evert"],
  "10-25":["Inga","Ingalill"],"10-26":["Amanda","Rasmus"],"10-27":["Sabina"],
  "10-28":["Simon","Simone"],"10-29":["Viola"],"10-30":["Elsa","Isabella"],
  "10-31":["Edgar","Edit"],
  "11-01":[],"11-02":["Tobias"],"11-03":["Hubert","Hugo"],"11-04":["Sverker"],
  "11-05":["Eugen","Eugenia"],"11-06":["Adolf","Gustav"],
  "11-07":["Ingegerd","Ingela"],"11-08":["Vendela"],
  "11-09":["Teodor","Teodora"],"11-10":["Martin","Martina"],
  "11-11":["Mårten"],"11-12":["Konrad","Kurt"],"11-13":["Krister","Kristian"],
  "11-14":["Emil","Emilia"],"11-15":["Leopold"],"11-16":["Vibeke","Viveka"],
  "11-17":["Naemi","Naima"],"11-18":["Lillemor","Moa"],
  "11-19":["Elisabet","Lisbet"],"11-20":["Marina","Pontus"],
  "11-21":["Helga","Olga"],"11-22":["Cecilia","Sissela"],"11-23":[],
  "11-24":[],"11-25":["Katarina","Katja"],"11-26":["Linus"],
  "11-27":["Asta","Astrid"],"11-28":["Malte"],"11-29":[],
  "11-30":["Anders","Andreas"],
  "12-01":["Oskar"],"12-02":["Beata","Beatrice"],"12-03":["Lydia"],
  "12-04":["Barbara","Barbro"],"12-05":["Sven"],"12-06":["Niklas","Nikolaus"],
  "12-07":["Angela","Angelika"],"12-08":["Virginia"],"12-09":["Anna"],
  "12-10":["Malena","Malin"],"12-11":["Daniel","Daniela"],
  "12-12":["Alexander","Alexis"],"12-13":["Lucia"],"12-14":["Sixten"],
  "12-15":[],"12-16":[],"12-17":[],
  "12-18":["Abraham"],"12-19":["Isak"],"12-20":["Israel","Moses"],
  "12-21":["Tomas"],"12-22":["Jonatan","Natanael"],"12-23":["Adam"],
  "12-24":["Eva"],"12-25":[],"12-26":["Staffan","Stefan"],
  "12-27":["Johan","Johannes"],"12-28":["Benjamin"],
  "12-29":["Natalia","Natalie"],"12-30":["Abel","Set"],"12-31":[],
};

// Namn för dagar utan namnsdagsnamn (Nyårsdagen, Alla Helgons dag m.fl.)
const NAMEDAY_FALLBACK = [
  "Timothy","Blanka","Céline","Mohammed","Nour","Zahra",
  "Melissa","Nadia","Hamid","Yasmine","Roxana","Axl",
  "Mehmet","Sasha","Emelie","Leandro","Aziz","Tilda",
  "Alicia","Younes","Amelia","Charlotte","George","James",
  "Noah","Camille","Manon","Pierre","Louis","Chloé",
  "Leon","Nora","Luca","Ben","Maja","Ahmed",
  "Omar","Hassan","Aisha","Ibrahim","Reza","Amir",
  "Mehdi","Parisa","Shirin","Arash","Nasrin","Bahar",
  "Maryam","Navid","Roozbeh","Sam","Carlos","José",
  "Juan","Ana","Miguel","Pablo","Carmen","Antonio",
  "Diego","Alejandro","Joan","Laura"
];

const FEED_END_QUOTES = [
  { t: '"Livet skjuts inte upp — det rinner förbi."',
    a: "Seneca, Epistulae Morales ad Lucilium, Brev I (65 e.Kr.)" },
  { t: '"Distraktionen roar oss och låter oss omärkligt glida mot döden."',
    a: "Blaise Pascal, Pensées, fragment 171 (postumt 1670)" },
  { t: '"Smartphonen är ett dominansredskap. Den fungerar som ett radband."',
    a: "Byung-Chul Han, intervju i El País (oktober 2021)" },
  { t: '"Mitt i vintern fann jag till sist att det inom mig fanns en oövervinnerlig sommar."',
    a: "Albert Camus, Retour à Tipasa (1954), i L'Été" },
  { t: '"Priset på en sak är den mängd liv som måste bytas ut mot den."',
    a: 'Henry David Thoreau, Walden (1854), kap. "Economy"' },
  { t: '"Denna dagen ett liv."',
    a: "Farbror Melker, i Astrid Lindgrens Vi på Saltkråkan (1964); senare hennes personliga motto" },
  { t: '"Vad in i helvete — landet ska ju arbeta, tycker du inte?"',
    a: "Pehr G. Gyllenhammar, gatuintervju för SVT i Göteborg (april 2017)" },
]

function getTodayName() {
  const d = new Date();
  const key = String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  const names = NAMEDAYS[key] || [];
  const fallback = () => NAMEDAY_FALLBACK[Math.floor(Math.random() * NAMEDAY_FALLBACK.length)];
  const r = Math.random();
  if (names.length >= 2) return r < 0.4 ? names[0] : r < 0.8 ? names[1] : fallback();
  if (names.length === 1) return r < 0.4 ? names[0] : fallback();
  return fallback();
}

function getActiveVenue() {
  const now = new Date();
  const cutoff = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  const counts = {};
  (window.allEvents || []).forEach(e => {
    const d = new Date(e.date);
    if (d >= now && d <= cutoff) counts[e.venue] = (counts[e.venue] || 0) + 1;
  });
  const pool = Object.entries(counts).filter(([, n]) => n >= 5).map(([v]) => v);
  return pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
}

function buildFeedEndText() {
  if (Math.random() < 0.5) {
    const name = getTodayName();
    const venue = getActiveVenue();
    if (venue) {
      return { type: 'venue', venue,
        html: `<span id="feed-end-text"><span class="feed-end-dim feed-end-venue">Är det inte dags att bjuda med <strong>${name}</strong> till <a href="#" class="feed-venue-link" data-venue="${venue}">${venue}</a>?</span></span>` };
    }
  }
  const pool = [...FEED_END_QUOTES, null];
  const pick = pool[Math.floor(Math.random() * pool.length)];
  if (!pick) {
    return { type: 'default',
      html: `<span id="feed-end-text"><span class="feed-end-dim">Nu är du färdigscrollad för idag.<br>Du vann!!</span></span>` };
  }
  return { type: 'quote',
    html: `<span id="feed-end-text"><span class="feed-quote-t">${pick.t}</span><span class="feed-quote-a">— ${pick.a}</span></span>` };
}

function showFeedEnd() {
  trackFeedEnd(filteredEvents.length);
  const result = buildFeedEndText();
  const tbody = document.getElementById("tbody");
  const tr = document.createElement("tr");
  tr.id = "feed-end";
  tr.innerHTML = `<td colspan="4"><div id="feed-end-inner">` +
    `<span id="feed-end-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 288 480" width="100%" height="100%">` +
    `<path fill="currentColor" stroke="currentColor" stroke-width="2" d=" ${KRISTALL_PATH}" /></svg></span>` +
    result.html +
    `</div></td>`;
  tbody.appendChild(tr);
  if (result.type === 'venue') {
    tr.querySelector('.feed-venue-link').addEventListener('click', e => {
      e.preventDefault();
      trackFeedEndVenueClick(result.venue);
      currentFilter.venue = result.venue;
      renderRows();
      window.scrollTo(0, 0);
    });
  }
}
function renderChunk() {
	if (visibleCount >= filteredEvents.length) return;
  const tbody = document.getElementById("tbody");
  const slice = filteredEvents.slice(visibleCount, visibleCount + CHUNK_SIZE);
  slice.forEach(event => {
    const dateKey = getDateKey(event.date);
    const { label, time } = formatDate(event.date);

    const crystalColor = event.crystal_color || (event.featured ? '#bef2ff' : null);
    const row = document.createElement("tr");
    if (event.highlight) row.classList.add(`variant-${event.highlight}`);
    row.innerHTML = `
      <td>
        <span>
          <a href="#" class="filter-date" data-date="${dateKey}">${label}</a>, ${time}
        </span>
      </td>
      <td>
        <span class="event-title-text">
          ${event.title}
          <a href="${event.link}" target="_blank" class="event-icon${crystalColor ? ' event-icon-featured' : ''}" title="Till evenemang">${getKristallIcon(true, crystalColor)}</a>
        </span>
      </td>
      <td>
        <span>
          <a href="#" class="filter-venue" data-venue="${event.venue}">${event.venue}</a>
        </span>
      </td>
      <td>
        <span>
          <a href="#" class="filter-category" data-category="${event.category}">${event.category}</a>
        </span>
      </td>
    `;
    row.querySelector('.event-icon').addEventListener('click', () => {
      if (crystalColor) {
        trackFeaturedClick(event.venue, event.title);
      } else {
        trackExternalLink(event.venue, event.title);
      }
    });
    tbody.appendChild(row);
  });
  visibleCount += slice.length;
  if (visibleCount >= filteredEvents.length) showFeedEnd();
}

window.addEventListener('scroll', () => {
  if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 300) {
        renderChunk();
  }
   
}
);

// Update headers on resize (desktop <-> mobile)
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    const isMobile = window.innerWidth < 768;
    document.getElementById("header-category").innerHTML =
      `<span class="has-icon">${isMobile ? 'Konst' : 'Konstform'}${getKristallIcon(currentFilter.category !== null)}</span>`;
  }, 250);
});
