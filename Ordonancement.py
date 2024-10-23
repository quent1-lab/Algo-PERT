from temps_taches_personne import *
from Taches import *

class Tache:
    def __init__(self, id: int, duree: float, parents: list[int]):
        self.id = id
        self.fait = False
        self.duree = duree
        self.parents = parents
        self.childs = []
    
    def __repr__(self):
        return f"{self.id} -> {self.parents} | {self.childs}"

class OrdonancementRessources:
    def __init__(self):
        self.jour_sup = [0, 0, 0, 0]
        self.taches: dict[int, Tache] = {}

        # Initialise le dictionaire de taches.
        for tache in taches:
            self.taches[tache["id"]] = Tache(tache["id"], tache["duree"], tache["predecesseurs"])

        # Initialise les enfants des taches.
        for tache in self.taches.values():
            for t in self.taches.values():
                if t.parents.count(tache.id) > 0:
                    tache.childs.append(t.id)
        
        print("init ok")

    # Trouve le temps que met une personne à réaliser une tache.
    def temps_tache(self, personne: int, tache: int):
        if tache >= 100 and tache < 200: # Choix de la personne qui est dans paiement.
            for x in temps_personne_taches_paiement:
                if x["id"] == personne:
                    for tt in x["temps_taches"]:
                        if tt["tache"] == tache:
                            return tt["temps"]

    # Retourne le temps diponible d'une personne.
    def temps_dispo(self, personne: int):
        for x in temps_disponible:
            if x["id"] == personne:
                return x["temps"]
    
    def tache_faisable(self, tache: int):
        faisable = True
        for tache_parent in self.tache_parentes(tache):
            if not self.taches[tache_parent].fait:
                faisable = False
        return faisable
    
    def tache_parentes(self, tache: int) -> list[int]:
        return self.taches[tache].parents

    def tache_enfants(self, tache: int) -> list[int]:
        mes_enfants = []
        

if __name__ == "__main__":
    mo = OrdonancementRessources()
    print(mo.taches)
