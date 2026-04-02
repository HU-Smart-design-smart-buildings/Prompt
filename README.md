# Prompt
oefening met prompt
Eerst volgt een korte inleiding over de aannames die gedaan worden in het project, hierna ga ik je een instructie geven over het maken van een routine die automatisch werkt (deze zal je zelf aanvullen). Ik wil dat je op basis van deze prompt mij een uitgebreide planning opstelt over de te nemen stappen. Ga erbij het ontwerp van uit dat je de applicatie netjes opbouwt, dat wil zeggen, gebruik maakt van meerdere python modulen die elkaar kunnen aanroepen zodat we straks de code goed kunnen beheren

Het doel van dit project is het ontwikkelen van een geautomatiseerde methode (beroepsproduct) die betrouwbare materiaalgegevens uit BIM-modellen extraheert. Aan de hand van ifc modellen 2.3 en 4.3 en wat ertussen zit. Met behulp van BIM-modellen maken we de logistieke materiaalstromen en de circulaire potentie van gebouwen inzichtelijk.
De aannames die we gedaan hebben 
Een eerste aanname: De objectstructuur van het model overeenkomt met de fysieke opbouw van het gebouw. Dit betekent dat bouwonderdelen zoals wanden, vloeren en kolommen correct gemodelleerd zijn en dat de geometrie van deze elementen de werkelijkheid benadert.

Een tweede aanname: De aanwezigheid van materiaalinformatie. Voor het genereren van een dataset wordt ervan uitgegaan dat materialen gekoppeld zijn aan de objecten in het model. Wanneer materiaalinformatie ontbreekt of onvolledig is ingevuld kan dit invloed hebben op de betrouwbaarheid van de dataset.

Een derde aanname: Deze aanname kan gemaakt worden op basis van het detailniveau van de BIM-modellen. Sommige modellen bevatten uitgebreide materiaalinformatie, terwijl andere modellen minder informatie bevatten. Hierdoor kan de hoeveelheid bruikbare data variëren. Dit heeft ermee te maken dat verschillende architecten/aannemers/installatieadviseurs op andere wijzen hun modellen opbouwen, er is geen standaard maatstaf.

Ook al hebben we deze aannames gedaan moet er een zo nauwkeurig mogelijk script gegenereerd worden. Het script zal gemaakt worden in verschillende fases 


Voor het uitwerken van het project zijn de volgende fases nodig. Hiervoor zijn al een aantal stappen opgesteld, maar deze mogen aangepast en uitgebreid worden. 
-	Fase 1 analyseer materialen verkregen ifc
-	Fase 2 materiaal met vernoemde volumes extraheren 
-	Fase 3 categoriseren materialen
-	Fase 4 exporten van materiaal met behorende data naar andere vorm 
  
Bij de volgende stappen zijn IFC-entiteiten benoemd als voorbeeld, deze voorbeelden moeten aangepast en aangevuld worden zodat de meeste informatie vanuit de IFC bestanden opgehaald kan worden! 

Stap 0 — Bestand inlezen & schema detecteren
Open het IFC-bestand met ifcopenshell.open() en lees ifc.schema uit. Dit geeft de letterlijke string uit de IFC-header ("IFC2X3" of "IFC4"). Gebruik dit als schemaflag voor alle vervolgstappen — geen aannames op basis van bestandsnaam of versienummer.

Stap 1 — Alle bouwelementen ophalen
Gebruik ifc.by_type ("IfcElement", include_subtypes=True). Dit geeft alle fysieke objecten terug (muren, kolommen, balken, vloeren, etc.) zonder dat je per entiteitstype hoeft te itereren. Bewaar per element: GlobalId, Name, en het werkelijke IFC-entiteitstype via element.is_a().

Stap 2 — Materiaalkoppelingen ophalen
Loop over element.HasAssociations en filter op rel.is_a("IfcRelAssociatesMaterial"). De daadwerkelijke materiaaldata zit in rel.RelatingMaterial — dit is het startpunt voor stap 3.

Stap 3 — Materiaaltype expliciet bepalen (geen aannames)
Controleer het type van RelatingMaterial met is_a() en verwerk elk geval apart:
·	IfcMaterial → .Name direct uitlezen
·	IfcMaterialList → itereer over .Materials, lees per item .Name
·	IfcMaterialLayerSetUsage → via .ForLayerSet.MaterialLayers, per laag: .Material.Name + .LayerThickness
·	IfcMaterialLayerSet → direct .MaterialLayers itereren
·	IfcMaterialProfileSet (IFC4) → .MaterialProfiles, per profiel: .Material.Name + .Profile
·	IfcMaterialConstituentSet (IFC4) → .MaterialConstituents, per onderdeel: .Material.Name + .Fraction indien aanwezig
Vang onbekende typen op met een else-tak die het type logt zonder te crashen.
 
Stap 4 — Schema-specifieke correcties
Pas de schemaflag toe om type-conflicten te vermijden. In IFC2X3 bestaat IfcMaterialConstituentSet niet; in IFC4 is IfcMaterialLayerSetUsage anders genest dan in 2X3. Verwerk alleen entiteiten die in het betreffende schema aanwezig zijn — geen try/except als vervanging voor schemakennis.

Stap 5 — Hoeveelheden uitlezen
Loop over element.IsDefinedBy, filter op IfcRelDefinesByProperties, en controleer of rel.RelatingPropertyDefinition.is_a("IfcElementQuantity"). Lees alleen de kwantiteiten uit die daadwerkelijk aanwezig zijn: NetVolume, GrossVolume, NetArea, GrossArea, Length. Gebruik de werkelijke waarde via .wrappedValue — sla ontbrekende waarden op als None, niet als 0.

Stap 6 — Relevante properties ophalen
Via IfcPropertySet in dezelfde IsDefinedBy-loop. Per property: prop.NominalValue.wrappedValue. Interessante sets zijn onder andere Pset_MaterialCommon (met MassDensity) en elementspecifieke Psets. Vul nooit een defaultwaarde in als een property ontbreekt.

Stap 7 — Materiaallijst samenvoegen
Groepeer rijen op materiaalNaam + ifcType. Aggregeer hoeveelheden (som van volumes/oppervlakken) per groep. Bewaar ook het aantal elementen per combinatie, en optioneel de lijst van GlobalIds als herleidbaarheid vereist is.

Stap 8 — Exporteren
Schrijf de geaggregeerde lijst naar CSV, Excel of JSON. Voeg altijd een kolom toe met het IFC-schema (IFC2X3/IFC4) zodat de herkomst traceerbaar blijft. Exporteer ook een detailregel-versie met één rij per element-materiaalcombinatie inclusief GUID, voor kwaliteitscontrole.Stap 0 — Bestand inlezen & schema detecteren

