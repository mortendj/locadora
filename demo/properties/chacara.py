# demo/properties/chacara.py
#
# DEMO DATA — fictional doppelganger of the chácara property, for use as
# public-safe example/seed data. Not a real address.

data = {
    "category":                  "TEMPORADA",
    "subtitle":                  "CHÁCARA",
    "type":                      "chácara",
    "street_address":            "Rua Alameda das Palmeiras, 888",
    "neighborhood":               "Zona Rural",
    "city":                      "Cisne Negro",
    "state":                     "Paraná",
    "zip_code":                  "85999-999",
    "use":                       "temporada",
    "commercial_use_description": "",
    "common_areas": [
        "1 banheiro social completo e 1 lavabo (apenas vaso sanitário)",
        "cozinha integrada à sala, totalmente equipada (geladeira, fogão, micro-ondas, churrasqueira, TV)",
        "área externa coberta (cobertura destinada apenas à proteção contra chuva e granizo, sem paredes em três lados), com mesa grande e bancos com capacidade para 10 a 12 pessoas, além de vaga para 1 veículo protegido em uma das extremidades",
        "churrasqueira de alvenaria, situada a alguns metros da área coberta principal, com cobertura própria de aproximadamente 2 x 2 metros",
        "lago para pesca (vide Cláusula Décima Nona quanto a cuidados de segurança)",
        "5 vagas de estacionamento ao ar livre em área de cascalho",
    ],
    "bedrooms": {
        "suite":    "1 suíte com cama de casal e banheiro privativo",
        "quarto_1": "1 quarto com cama de casal",
        "quarto_2": "1 quarto com cama de casal e uma cama de solteiro adicional",
    },
    "configurations": {
        "full":     ["suite", "quarto_1", "quarto_2"],
        "no_suite": ["quarto_1", "quarto_2"],
        "dayuse":   [],
    },
    "water_hazards": [
        "dois açudes de porte considerável nos fundos do imóvel (o maior com aproximadamente 20 a 25 metros em um sentido e 10 metros no outro), com profundidade suficiente para representar risco de afogamento, especialmente para crianças",
    ],
    "parking_capacity": 6,
}
