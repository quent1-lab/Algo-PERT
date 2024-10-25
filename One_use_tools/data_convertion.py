import obsolete.data_taches_projets
import pert_engine
import json

taches = []
liens = []

for tache in obsolete.data_taches_projets.taches_sciado:
    taches.append({"id": tache["id"], "duree": tache["duree"]})
    for p in tache["predecesseurs"]:
        liens.append((p, tache["id"]))

data = {"taches": taches, "liens": liens}

with open("sciado_taches.json", 'w') as f:
    f.write(json.dumps(data, sort_keys=True, indent=4))