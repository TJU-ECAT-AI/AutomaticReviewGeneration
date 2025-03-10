DemoNumber=3
def Print(*Content,sep='\t'):
    with open('run.log','a',encoding='UTF8') as FILE:
        FILE.write(sep.join([str(i) for i in Content])+'\n')
ACS_publications = ["Journal of the American Chemical Society",
                    "ACS Catalysis",
                    "ACS sustainable chemistry & engineering",
                    "ACS sensors",
                    "analytical chemistry",
                    "Accounts of Chemical Research",
                    "ACS macro letters",
                    "acs central science",
                    "journal of chemical theory and computation",
                    "chemical reviews",
                    "JACS Au",
                    "ACS Materials Letters",
                    "MACROMOLECULES",
                    "Organic Letters"]
Wiley_publications = ["Angewandte Chemie International Edition",
                      "advanced science","Advanced Materials"]
ELSEVIER_publications_1 = ["Chemical Engineering Journal",
                           "Journal of Catalysis",
                           "Applied Catalysis B: Environmental",
                           "Joule",
                           "chem",
                           "Acta Pharmaceutica Sinica B",
                           "Carbohydrate Polymers",
                           "Sensors and Actuators B: Chemical",
                           "Journal of Energy Chemistry",
                           "Journal of Colloid and Interface Science",
                           "Talanta",
                           "Progress in Polymer Science",
                           "Progress in Materials Science"]
ELSEVIER_publications_2 = ["Advances in Colloid and Interface Science",
                           "Surface Science Reports",
                           "TrAC Trends in Analytical Chemistry",
                           "Ultrasonics sonochemistry",
                           "science bulletin",
                           "Chinese Journal of Catalysis",
                           "Journal of Photochemistry and Photobiology C: Photochemistry Reviews",
                           "Coordination Chemistry Reviews",
                           "International Journal of Biological Macromolecules",
                           "Trends in Chemistry",
                           "Progress in Nuclear Magnetic Resonance Spectroscopy",
                           "Bioorganic Chemistry",
                           "Analytica Chimica Acta",
                           "Chinese Chemical Letters"]
ELSEVIER_publications_3 = ["PROGRESS IN ENERGY AND COMBUSTION SCIENCE",
                           "APPLIED ENERGY",
                           "JOURNAL OF MEMBRANE SCIENCE",
                           "FUEL",
                           "FUEL PROCESSING TECHNOLOGY",
                           "PROCEEDINGS OF THE COMBUSTION INSTITUTE",
                           "SEPARATION AND PURIFICATION TECHNOLOGY",
                           "Green Energy & Environment"]
springer_publications_1 = ["Nature",
                           "Nature catalysis",
                           "nature sustainability",
                           "Nature chemistry",
                           "Nature nanotechnology",
                           "Nature communications",
                           "Nature Energy",
                           "Nature Reviews Materials",
                           "Science Advances"
                           "Nature Materials",
                           "Nature Reviews Chemistry",
                           "Nature communications"]
springer_publications_2 = ["npj Clean Water"]
Science = ["Science"]
RSC_publications_1 = ["chemical science",
                      "Natural Product Reports",
                      "Journal of Materials Chemistry A",
                      "Chemical Society Reviews",
                      "Green Chemistry",
                      "Inorganic Chemistry Frontiers",
                      "Organic Chemistry Frontiers"]
RSC_publications_2 = ["Energy & Environmental Science"]
ACS_second = ["The Journal of Physical Chemistry A",
              "The Journal of Physical Chemistry B",
              "The Journal of Physical Chemistry C",
              "The Journal of Physical Chemistry LETTERS",
              "ACS Applied Polymer Materials",
              "ACS Combinatorial Science",
              "ACS Earth and Space Chemistry",
              "ACS Omega",
              "Bioconjugate Chemistry",
              "Biomacromolecules",
              "CRYSTAL GROWTH & DESIGN",
              "INORGANIC CHEMISTRY",
              "JOURNAL OF CHEMICAL EDUCATION",
              "Journal of Chemical Information and Modeling",
              "The Journal of Organic Chemistry",
              "LANGMUIR",
              "ORGANIC PROCESS RESEARCH & DEVELOPMENT",
              "Organic Process Research &amp; Development",
              "ORGANOMETALLICS",
              "ATOMIC SPECTROSCOPY",
              "JOURNAL OF THE AMERICAN SOCIETY FOR MASS SPECTROMETRY"]
ACS_second_2 = ["ENERGY & FUELS",
                "INDUSTRIAL & ENGINEERING CHEMISTRY RESEARCH",
                "JOURNAL OF CHEMICAL AND ENGINEERING DATA",
                "AICHE JOURNAL"]
Wiley_second_search_1 = ["Acta Crystallographica Section B-Structural Science Crystal Engineering and Materials",
                         "ADVANCED SYNTHESIS & CATALYSIS",
                         "APPLIED ORGANOMETALLIC CHEMISTRY",
                         "Asian Journal of Organic Chemistry",
                         "ChemCatChem",
                         "ChemElectroChem",
                         "Chemical Record",
                         "Chemistry & Biodiversity",
                         "Chemistry – A European Journal",
                         "Chemistry—An Asian Journal",
                         "ChemistryOpen ",
                         "ChemPhotoChem",
                         "ChemPhysChem",
                         "ChemPlusChem",
                         "ChemSusChem",
                         "Chinese Journal of Chemistry",
                         "Computational Molecular Science"]
Wiley_second_search_2 = ["EUROPEAN JOURNAL OF INORGANIC CHEMISTRY",
                         "EUROPEAN JOURNAL OF ORGANIC CHEMISTRY",
                         "INTERNATIONAL JOURNAL OF QUANTUM CHEMISTRY",
                         "ISRAEL JOURNAL OF CHEMISTRY",
                         "JOURNAL OF APPLIED POLYMER SCIENCE",
                         "JOURNAL OF CHEMOMETRICS",
                         "JOURNAL OF COMPUTATIONAL CHEMISTRY",
                         "JOURNAL OF HETEROCYCLIC CHEMISTRY",
                         "JOURNAL OF POLYMER SCIENCE",
                         "JOURNAL OF RAMAN SPECTROSCOPY",
                         "MACROMOLECULAR RAPID COMMUNICATIONS",
                         "MAGNETIC RESONANCE IN CHEMISTRY",
                         "MASS SPECTROMETRY REVIEWS",
                         "POLYMER INTERNATIONAL",
                         "RAPID COMMUNICATIONS IN MASS SPECTROMETRY",
                         "Reviews in Computational Chemistry",
                         "Wiley Interdisciplinary Reviews - Computational Molecular Science"]
Wiley_second_search_3 = ["POLYMER ENGINEERING AND SCIENCE",
                         "JOURNAL OF FOOD PROCESS ENGINEERING",
                         "JOURNAL OF CHEMICAL TECHNOLOGY AND BIOTECHNOLOGY",
                         "JOURNAL OF SEPARATION SCIENCE",
                         "ACTA POLYMERICA SINICA"]
springer_second = ["ANALYTICAL AND BIOANALYTICAL CHEMISTRY",
                   "Chemical Research in Chinese Universities",
                   "Chinese Journal of Polymer Science",
                   "Communications Chemistry",
                   "Foundations of Chemistry",
                   "Heritage Science",
                   "IRANIAN POLYMER JOURNAL",
                   "JOURNAL OF BIOLOGICAL INORGANIC CHEMISTRY",
                   "Journal of Cheminformatics",
                   "Journal of Flow Chemistry",
                   "Journal of Inorganic and Organometallic Polymers and Materials",
                   "JOURNAL OF MATHEMATICAL CHEMISTRY",
                   "Journal of Nanostructure in Chemistry",
                   "JOURNAL OF POLYMER RESEARCH",
                   "MICROCHIMICA ACTA",
                   "MOLECULAR DIVERSITY",
                   "POLYMER BULLETIN",
                   "RESEARCH ON CHEMICAL INTERMEDIATES",
                   "Topics in Current Chemistry",
                   "POLYMER JOURNAL"]
springer_second_2 = ["PLASMA CHEMISTRY AND PLASMA PROCESSING",
                     "TRANSPORT IN POROUS MEDIA",
                     "BIOPROCESS AND BIOSYSTEMS ENGINEERING"]
RSC_second = ["Chemical Communications",
              "ANALYST",
              "Catalysis Science & Technology",
              "Catalysis Science &amp; Technology",
              "CRYSTENGCOMM",
              "Dalton Transactions",
              "FARADAY DISCUSSIONS",
              "Analytical Methods",
              "JOURNAL OF ANALYTICAL ATOMIC SPECTROMETRY",
              "NEW JOURNAL OF CHEMISTRY",
              "ORGANIC & BIOMOLECULAR CHEMISTRY",
              "PHOTOCHEMICAL & PHOTOBIOLOGICAL SCIENCES",
              "PHYSICAL CHEMISTRY CHEMICAL PHYSICS",
              "Polymer Chemistry",
              "Reaction Chemistry & Engineering",
              "RSC Advances",
              "Soft Matter",
              "Reaction Chemistry & Engineering"]
ELSEVIER_second_search_1 = ["ACTA PHYSICO-CHIMICA SINICA",
                            "Advances in Carbohydrate Chemistry and Biochemistry",
                            "Advances in Catalysis",
                            "Advances in Heterocyclic Chemistry",
                            "Advances in Organometallic Chemistry",
                            "Annual Reports on NMR Spectroscopy",
                            "APPLIED CATALYSIS A-GENERAL",
                            "Arabian Journal of Chemistry",
                            "BIOELECTROCHEMISTRY",
                            "Carbohydrate Research",
                            "Catalysis Today",
                            "Chemical Physics",
                            "Catalysis Communications"]
ELSEVIER_second_search_2 = ["Colloids and Surfaces A: Physicochemical and Engineering Aspects",
                            "CURRENT OPINION IN COLLOID & INTERFACE SCIENCE",
                            "Current Opinion in Electrochemistry",
                            "Current Opinion in Green and Sustainable Chemistry",
                            "EUROPEAN POLYMER JOURNAL",
                            "INORGANICA CHIMICA ACTA",
                            "JOURNAL OF ANALYTICAL AND APPLIED PYROLYSIS",
                            "JOURNAL OF CHROMATOGRAPHY A",
                            "JOURNAL OF ELECTROANALYTICAL CHEMISTRY",
                            "JOURNAL OF MAGNETIC RESONANCE",
                            "JOURNAL OF MOLECULAR LIQUIDS",
                            "JOURNAL OF MOLECULAR STRUCTURE",
                            "JOURNAL OF ORGANOMETALLIC CHEMISTRY",
                            "JOURNAL OF PHOTOCHEMISTRY AND PHOTOBIOLOGY A - CHEMISTRY",
                            "JOURNAL OF RARE EARTHS",
                            "Journal of Saudi Chemical Society",
                            "JOURNAL OF SOLID STATE CHEMISTRY"]
ELSEVIER_second_search_3 = ["Materials Today Chemistry",
                            "MICROCHEMICAL JOURNAL",
                            "Molecular Catalysis",
                            "POLYHEDRON",
                            "POLYMER",
                            "POLYMER DEGRADATION AND STABILITY",
                            "PROGRESS IN SOLID STATE CHEMISTRY",
                            "RADIATION PHYSICS AND CHEMISTRY",
                            "SOLID STATE NUCLEAR MAGNETIC RESONANCE",
                            "SOLID STATE SCIENCES",
                            "SPECTROCHIMICA ACTA PART A - MOLECULAR AND BIOMOLECULAR SPECTROSCOPY",
                            "SPECTROCHIMICA ACTA PART B - ATOMIC SPECTROSCOPY",
                            "SURFACE SCIENCE",
                            "Sustainable Chemistry and Pharmacy",
                            "TETRAHEDRON",
                            "THERMOCHIMICA ACTA",
                            "Trends in Environmental Analytical Chemistry",
                            "VIBRATIONAL SPECTROSCOPY"]
ELSEVIER_second_search_4 = ["DESALINATION",
                            "Journal of CO2 Utilization",
                            "JOURNAL OF FOOD ENGINEERING",
                            "POWDER TECHNOLOGY",
                            "Journal of Natural Gas Science and Engineering",
                            "MINERALS ENGINEERING",
                            "CHEMICAL ENGINEERING SCIENCE",
                            "JOURNAL OF PROCESS CONTROL",
                            "Journal of Environmental Chemical Engineering",
                            "Current Opinion in Chemical Engineering",
                            "FOOD AND BIOPRODUCTS PROCESSING",
                            "DYES AND PIGMENTS",
                            "JOURNAL OF SUPERCRITICAL FLUIDS",
                            "Journal of Water Process Engineering",
                            "JOURNAL OF INDUSTRIAL AND ENGINEERING CHEMISTRY"]
ELSEVIER_second_search_5 = [
    "International Journal of Greenhouse Gas Control",
    "INTERNATIONAL JOURNAL OF ADHESION AND ADHESIVES",
    "COMPUTERS & CHEMICAL ENGINEERING",
    "CHINESE JOURNAL OF CHEMICAL ENGINEERING",
    "JOURNAL OF LOSS PREVENTION IN THE PROCESS INDUSTRIES",
    "BIOCHEMICAL ENGINEERING JOURNAL",
    "PROCESS BIOCHEMISTRY",
    "CHEMICAL ENGINEERING RESEARCH & DESIGN",
    "REACTIVE & FUNCTIONAL POLYMERS",
    "JOURNAL OF AEROSOL SCIENCE",
    "Education for Chemical Engineers",
    "Chemical Engineering and Processing-Process Intensification",
    "Journal of the Taiwan Institute of Chemical Engineers",
    "FLUID PHASE EQUILIBRIA",
    "Particuology",
    "ADVANCED POWDER TECHNOLOGY",
    "PROCESS SAFETY AND ENVIRONMENTAL PROTECTION",
    "COMBUSTION AND FLAME",
    "ALDRICHIMICA ACTA"]
MDPI_second = ["MDPI",
               "MOLECULES",
               "Journal of Nanostructure in Chemistry",
               "Processes",
               "Separations",
               "Membranes",
               "Gels",
               "Inorganics",
               "Magnetochemistry",
               "MOLECULES",
               "Batteries - Basel",
               "Catalysts"]
Frontiers_second = ["Frontiers in Chemistry"]
Taylor_second = ["SEPARATION AND PURIFICATION REVIEWS",
                 "DRYING TECHNOLOGY",
                 "Journal of Energetic Materials",
                 "JOURNAL OF MICROENCAPSULATION",
                 "JOURNAL OF ADHESION",
                 "APPLIED SPECTROSCOPY",
                 "APPLIED SPECTROSCOPY REVIEWS",
                 "COMMENTS ON INORGANIC CHEMISTRY",
                 "CRITICAL REVIEWS IN ANALYTICAL CHEMISTRY",
                 "Crystallography Reviews",
                 "Green Chemistry Letters and Reviews",
                 "LIQUID CRYSTALS",
                 "NATURAL PRODUCT RESEARCH",
                 "Polymer Reviewsreview",
                 "SOLVENT EXTRACTION AND ION EXCHANGE"]
Other_second = ["JOURNAL OF CHEMICAL PHYSICS",
                "Express Polymer Letters",
                "RADIOCHIMICA ACTA",
                "ZEITSCHRIFT FUR PHYSIKALISCHE CHEMIE-INTERNATIONAL JOURNAL OF RESEARCH IN PHYSICAL CHEMISTRY & CHEMICAL PHYSICS",
                "Methods and Applications in Fluorescence",
                "RUSSIAN CHEMICAL REVIEWS",
                "Annual Review of Analytical Chemistry",
                "BMC Chemistry",
                "BULLETIN OF THE CHEMICAL SOCIETY OF JAPAN",
                "BIOINORGANIC CHEMISTRY AND APPLICATIONS",
                "ACTA CHIMICA SINICA",
                "MATCH-COMMUNICATIONS IN MATHEMATICAL AND IN COMPUTER CHEMISTRY"]
User_defined = []
