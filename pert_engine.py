import networkx as nx
import plan_actions
import math
import pygame
import temps_taches_personne
from PIL import Image
import sys

class Tache:
    def __init__(self, id: int, duree: float):
        self.id = id
        self.duree = duree
        self.debut_tot = 0
        self.fin_tot = 0
        self.debut_tard = 0
        self.fin_tard = 0
    
    def calcul_fin_tot(self):
        self.fin_tot = self.debut_tot + self.duree
    
    def calcul_debut_tard(self):
        self.debut_tard = self.fin_tard - self.duree

class ReseauPert:
    def __init__(self, taches: list[Tache], liens_oriente: list[tuple[int, int]]):
        self.taches = taches
        self.liens_oriente = liens_oriente
    
    def calcul_tot(self):
        pass

if __name__ == "__main__":
    pygame.init()
    window = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("TEST Réseau PERT")

    while True:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                pygame.quit()
                sys.exit()
        
        window.fill(pygame.colordict.THECOLORS["aliceblue"])
        pygame.display.flip()
        pygame.time.Clock().tick(60)


class PertEngineCore:
    taches: list[dict[str]] = None
    taches_ = None
    temps_taches = None
    chemin_critique = None
    ordre_taches = None
    tache_priorisees = None
    temps_taches_tard = None

    # Fonction pour trier les tâches selon l'ordre topologique
    def trier_taches_topologiquement(taches):
        G = nx.DiGraph()
        for tache in taches:
            G.add_node(tache["id"])
            for prec in tache["predecesseurs"]:
                G.add_edge(prec, tache["id"])

        try:
            ordre_topologique = list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            raise Exception("Le graphe des tâches contient des cycles, le tri topologique est impossible.")
        
        taches_triees = [tache for id_tache in ordre_topologique for tache in taches if tache["id"] == id_tache]
        return taches_triees

    # Calcul des temps de début et de fin
    def calcul_dates(taches):
        temps_taches = {}
        for tache in taches:
            if not tache["predecesseurs"]:
                debut = 0
            else:
                debut = max(temps_taches[prec][1] for prec in tache["predecesseurs"])
            fin = debut + tache["duree"]
            temps_taches[tache["id"]] = (debut, fin)
        return temps_taches

    # Calcul des temps au plus tard
    def calcul_temps_tard(taches, temps_taches):
        G = nx.DiGraph()
        for tache in taches:
            G.add_node(tache["id"], duree=tache["duree"])
            for prec in tache["predecesseurs"]:
                G.add_edge(prec, tache["id"])

        # Trouver les tâches finales (celles sans successeurs)
        taches_finales = [tache for tache in taches if not list(G.successors(tache["id"]))]
        temps_le_plus_tard = max(temps_taches[tache["id"]][1] for tache in taches_finales)

        # Initialiser les temps au plus tard
        temps_tard = {tache["id"]: {"end_tard": float('inf'), "start_tard": float('inf')} for tache in taches}
        for tache in taches_finales:
            temps_tard[tache["id"]]["end_tard"] = temps_le_plus_tard
            temps_tard[tache["id"]]["start_tard"] = temps_tard[tache["id"]]["end_tard"] - tache["duree"]

        # Parcourir les tâches en ordre inverse topologique
        for tache in reversed(taches):
            successeurs = list(G.successors(tache["id"]))
            if successeurs:
                temps_tard[tache["id"]]["end_tard"] = min(temps_tard[succ]["start_tard"] for succ in successeurs)
                temps_tard[tache["id"]]["start_tard"] = temps_tard[tache["id"]]["end_tard"] - tache["duree"]

        return temps_tard

    # Fonction pour calculer le chemin critique
    def calcul_chemin_critique(taches):
        G = nx.DiGraph()
        for tache in taches:
            G.add_node(tache["id"], duree=tache["duree"])
            for prec in tache["predecesseurs"]:
                G.add_edge(prec, tache["id"])

        # Calculer le chemin critique
        chemin_critique = nx.dag_longest_path(G, weight='duree')
        return chemin_critique
    
    # Fonction pour prioriser les tâches en fonction de l'impact inter-projets
    def prioriser_taches_par_impact(taches):
        G = nx.DiGraph()
        for tache in taches:
            G.add_node(tache["id"], projet=tache["id"] // 100)
            for prec in tache["predecesseurs"]:
                G.add_edge(prec, tache["id"])

        # Calculer le nombre de successeurs pour chaque tâche
        nombre_successeurs = {tache["id"]: len(list(nx.descendants(G, tache["id"]))) for tache in taches}
        
        # Ajouter une priorité basée sur l'impact sur d'autres projets
        for tache in taches:
            successeurs = list(nx.descendants(G, tache["id"]))
            impact_inter_projet = len([s for s in successeurs if G.nodes[s]["projet"] != G.nodes[tache["id"]]["projet"]])
            tache["priorite"] = nombre_successeurs[tache["id"]] + impact_inter_projet * 2  # Pondérer plus fortement les impacts inter-projets

        # Trier les tâches par priorité décroissante (plus de successeurs et d'impact inter-projet en premier)
        taches_triees = sorted(taches, key=lambda t: t["priorite"], reverse=True)
        return taches_triees

    def definir_ordre_taches(taches):
        # Séparer les tâches par catégorie
        ordre_taches_digit = []
        ordre_taches_paiement = []
        ordre_taches_interne = []
        ordre_taches_client = []
        
        for tache in taches:
            if tache["id"] < 100:
                ordre_taches_digit.append(tache)
            elif tache["id"] < 200:
                ordre_taches_paiement.append(tache)
            elif tache["id"] < 300:
                ordre_taches_interne.append(tache)
            else:
                ordre_taches_client.append(tache)
        
        # Calculer le chemin critique pour chaque catégorie
        chemin_critique_digit = PertEngineCore.calcul_chemin_critique(ordre_taches_digit)
        chemin_critique_paiement = PertEngineCore.calcul_chemin_critique(ordre_taches_paiement)
        chemin_critique_interne = PertEngineCore.calcul_chemin_critique(ordre_taches_interne)
        chemin_critique_client = PertEngineCore.calcul_chemin_critique(ordre_taches_client)
        
        # Fonction pour trier les tâches en fonction du chemin critique et du temps des tâches
        def trier_taches_par_chemin_critique_et_temps(ordre_taches, chemin_critique):
            taches_critique = [tache for tache in ordre_taches if tache["id"] in chemin_critique]
            taches_non_critique = [tache for tache in ordre_taches if tache["id"] not in chemin_critique]
            
            # Trier les tâches critiques par ordre de leur apparition dans le chemin critique
            taches_critique.sort(key=lambda t: chemin_critique.index(t["id"]))
            
            # Trier les tâches non critiques par leur temps de début au plus tard
            taches_ = PertEngineCore.trier_taches_topologiquement(taches)
            temps_taches = PertEngineCore.calcul_dates(taches_)
            temps_tard = PertEngineCore.calcul_temps_tard(ordre_taches, temps_taches)
            taches_non_critique.sort(key=lambda t: temps_tard[t["id"]]["start_tard"])
            
            return taches_critique + taches_non_critique
        
        # Trier les tâches de chaque catégorie
        ordre_taches_digit = trier_taches_par_chemin_critique_et_temps(ordre_taches_digit, chemin_critique_digit)
        ordre_taches_paiement = trier_taches_par_chemin_critique_et_temps(ordre_taches_paiement, chemin_critique_paiement)
        ordre_taches_interne = trier_taches_par_chemin_critique_et_temps(ordre_taches_interne, chemin_critique_interne)
        ordre_taches_client = trier_taches_par_chemin_critique_et_temps(ordre_taches_client, chemin_critique_client)
        
        # Combiner les tâches dans l'ordre global en fonction de leur catégorie
        ordre_global = (ordre_taches_digit, ordre_taches_paiement, ordre_taches_interne, ordre_taches_client)
        
        return ordre_global
    
    def calculate():
        PertEngineCore.taches_ = PertEngineCore.trier_taches_topologiquement(PertEngineCore.taches)
        PertEngineCore.temps_taches = PertEngineCore.calcul_dates(PertEngineCore.taches_)
        PertEngineCore.chemin_critique = PertEngineCore.calcul_chemin_critique(PertEngineCore.taches_)
        PertEngineCore.ordre_taches = PertEngineCore.definir_ordre_taches(PertEngineCore.taches)
        PertEngineCore.tache_priorisees = PertEngineCore.prioriser_taches_par_impact(PertEngineCore.taches)
        PertEngineCore.temps_taches_tard = PertEngineCore.calcul_temps_tard(PertEngineCore.taches_, PertEngineCore.temps_taches)


class PertEngineGraphics:
    fenetre: pygame.Surface = None
    taille_case = 100
    espace = 10

    # Couleurs
    BLANC = (255, 255, 255)
    NOIR = (0, 0, 0)
    BLEU = (173, 216, 230)
    ROUGE = (255, 0, 0)
    VERT = (0, 255, 0)
    GRIS = (200, 200, 200)

    # Fonction pour dessiner une tâche
    def dessiner_tache(tache, tache_priorisees, x, y, temps_taches, temps_tard, zoom, fonts):
        taille_case_zoom = PertEngineGraphics.taille_case * zoom
        espace_zoom = PertEngineGraphics.espace * zoom
        nom_projet = ""
        # Si tache < 100 en bleu, ou < 200 en vert, ou < 300 en orange, sinon en magenta
        if tache["id"] < 100:
            couleur = PertEngineGraphics.BLEU
            nom_projet = "Digitalisation"
        elif tache["id"] < 200:
            couleur = (0, 128, 0)
            nom_projet = "Paiement"
        elif tache["id"] < 300:
            couleur = (255, 165, 0)
            nom_projet = "Interne"
        else:
            couleur = (255, 0, 255)
            nom_projet = "Client"
        
        if str(tache['id']) in list(plan_actions.taches_valeurs.keys()):
            v_tache = plan_actions.taches_valeurs[str(tache['id'])]
            if 'ext' in v_tache.keys():
                if v_tache['ext']:
                    couleur = PertEngineGraphics.ROUGE
            if 'fait' in v_tache.keys():
                if v_tache['fait']:
                    couleur = PertEngineGraphics.lerp_color(couleur, PertEngineGraphics.GRIS, 0.8)

        font, font_bold = fonts

        # Fond de la tâche
        pygame.draw.rect(PertEngineGraphics.fenetre, couleur, (x, y, 3 * taille_case_zoom + 2 * espace_zoom, 1 * taille_case_zoom + 3 * espace_zoom), 0, 20)
        # Bordure de la tâche
        pygame.draw.rect(PertEngineGraphics.fenetre, PertEngineGraphics.NOIR, (x, y, 3 * taille_case_zoom + 2 * espace_zoom, 1 * taille_case_zoom + 3 * espace_zoom), 2, 20)
        
        # Temps de début
        debut_text = font.render(f"Début: {temps_taches[tache['id']][0]:.1f}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(debut_text, (x + espace_zoom, y + espace_zoom))
        
        # Priorité de la tâche
        priorite_text = font.render(f"Priorité: {tache['priorite']}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(priorite_text, (x + 0.0 * taille_case_zoom + 3 * espace_zoom, y + 0.5 *  taille_case_zoom + espace_zoom))

        # PROJET
        projet_text = font.render(f"{nom_projet}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(projet_text, (x + 1.2 * taille_case_zoom + 3 * espace_zoom, y + 0.5 * taille_case_zoom + espace_zoom))
        
        # Nom de la tâche
        nom_text = font_bold.render(f"Tâche {tache['id']}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(nom_text, (x + 3 * espace_zoom + taille_case_zoom, y + espace_zoom))

        # Temps de fin
        fin_text = font.render(f"Fin: {temps_taches[tache['id']][1]:.1f}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(fin_text, (x + 2 * taille_case_zoom + 3 * espace_zoom, 
                                y + espace_zoom))
        
        # Durée
        duree_text = font.render(f"Durée: {tache['duree']}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(duree_text, (x + 1 * taille_case_zoom + 3 * espace_zoom, 
                                y + taille_case_zoom + espace_zoom))
        id = tache['id']

        # Temps start tard
        start_tard_text = font.render(f"Début: {temps_tard[id]['start_tard']:.1f}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(start_tard_text, (x + espace_zoom, y + taille_case_zoom + espace_zoom))
        
        # Temps end tard
        tard_text = font.render(f"Fin: {temps_tard[id]['end_tard']:.1f}", True, PertEngineGraphics.NOIR)
        PertEngineGraphics.fenetre.blit(tard_text, (x + 2 * taille_case_zoom + 3 * espace_zoom, 
                                y + taille_case_zoom + espace_zoom))
        
        # Meilleur personne TACHE:
        bt = temps_taches_personne.best_person_tache[int(tache['id'])]
        if not bt == "None":
            best_pers = font.render(f"{bt}", True, PertEngineGraphics.NOIR)
            PertEngineGraphics.fenetre.blit(best_pers, (x + 1.2 * taille_case_zoom + 3 * espace_zoom, y + 0.25 * taille_case_zoom + espace_zoom))

        
        # temps_taches_personne.temps_personne_taches_paiement.temps_tache(101, )
    
    # Interpolation entre deux couleurs.
    def lerp_color(couleur1, couleur2, t: float):
        r1, g1, b1 = couleur1
        r2, g2, b2 = couleur2
        return (r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)

    # Rotation du point (px, py) de centre (cx, cy) d'angle a en radians
    def rotate(px: float, py: float, cx: float, cy: float, a: float):
        x = px - cx
        y = py - cy
        rx = math.cos(a) * x - math.sin(a) * y
        ry = math.sin(a) * x + math.cos(a) * y
        return (rx + cx, ry + cy)

    # Fonction pour dessiner une flèche entre deux tâches
    def dessiner_fleche(x1, y1, x2, y2, zoom, couleur=NOIR):
        line_width = max(1, int(1.5 * zoom))  # Adapter la taille de la ligne en fonction du zoom, avec une taille minimale de 1
        pygame.draw.line(PertEngineGraphics.fenetre, couleur, (x1, y1), (x2, y2), line_width)

        a = math.atan2(y2 - y1, x2 - x1)

        pygame.draw.polygon(PertEngineGraphics.fenetre, couleur, [(x2, y2), PertEngineGraphics.rotate(x2 - 10 * zoom, y2 - 5 * zoom, x2, y2, a), PertEngineGraphics.rotate(x2 - 10 * zoom, y2 + 5 * zoom, x2, y2, a)])

    # Faire une transformation de translation puis d'échelle et enfin translater les éléments au centre.
    def camera_transformation(x, y, cam_x, cam_y, zoom):
        return ((x - cam_x) * zoom + PertEngineGraphics.fenetre.get_width() / 2 , (y - cam_y) * zoom + PertEngineGraphics.fenetre.get_height() / 2)

    # Faire une transformation inverse de (translation puis d'échelle et enfin translater les éléments au centre).
    def inverse_camera_transformation(x, y, cam_x, cam_y, zoom):
        return ((x + cam_x) / zoom - PertEngineGraphics.fenetre.get_width() / 2 , (y + cam_y) / zoom - PertEngineGraphics.fenetre.get_height() / 2)

    # Fonction pour capturer l'écran
    def capturer_ecran(filename="Image/capture.png"):
        pygame.image.save(PertEngineGraphics.fenetre, filename)

    # Fonction pour capturer le réseau complet
    def capturer_reseau_complet(mode, tache_priorisees, taches):
        taches_ = PertEngineCore.trier_taches_topologiquement(taches)
        temps_taches = PertEngineCore.calcul_dates(taches_)
        chemin_critique = PertEngineCore.calcul_chemin_critique(taches_)
        temps_tard = PertEngineCore.calcul_temps_tard(taches_, temps_taches)

        positions = {}
        colonnes = {}
        y_position = 10
        
        for tache in taches_:
            if not tache["predecesseurs"]:
                # Tâches de début de ligne
                x_position = 10
                if x_position not in colonnes:
                    colonnes[x_position] = y_position
                else:
                    colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                y_position = colonnes[x_position]
            else:
                # Tâches liées
                max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                x_position = max_x_position + 3 * PertEngineGraphics.taille_case + 20 * PertEngineGraphics.espace
                if x_position not in colonnes:
                    colonnes[x_position] = 10
                else:
                    colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                y_position = colonnes[x_position]

            positions[tache["id"]] = (x_position, y_position)

        # Calculer les dimensions totales du réseau
        max_x = max(positions[tache["id"]][0] for tache in taches_) + 3 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
        max_y = max(positions[tache["id"]][1] for tache in taches_) + 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace

        # Calculer le nombre de captures nécessaires
        captures_x = (max_x // PertEngineGraphics.fenetre.get_width()) + 1
        captures_y = (max_y // PertEngineGraphics.fenetre.get_height()) + 1
        
        # Capturer les images
        images = []
        for i in range(int(captures_x)):
            for j in range(int(captures_y)):
                offset_x = -i * PertEngineGraphics.fenetre.get_width()
                offset_y = -j * PertEngineGraphics.fenetre.get_height()
                PertEngineGraphics.fenetre.fill(PertEngineGraphics.BLANC)
                y_position = 10
                positions = {}
                colonnes = {}
                font = pygame.font.Font(None, 24)
                font_bold = pygame.font.Font(None, 24)
                font_bold.set_bold(True)
                if mode == 1:
                    for tache in taches_:
                        if not tache["predecesseurs"]:
                            x_position = 10
                            if x_position not in colonnes:
                                colonnes[x_position] = y_position
                            else:
                                colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                            y_position = colonnes[x_position]
                        else:
                            max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                            x_position = max_x_position + 3 * PertEngineGraphics.taille_case + 5 * PertEngineGraphics.espace
                            if x_position not in colonnes:
                                colonnes[x_position] = 10
                            else:
                                colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                            y_position = colonnes[x_position]
                        positions[tache["id"]] = (x_position, y_position)
                        PertEngineGraphics.dessiner_tache(tache,tache_priorisees, x_position + offset_x, y_position + offset_y, temps_taches, temps_tard, 1.0, (font, font_bold))
                    for tache in taches_:
                        for prec in tache["predecesseurs"]:
                            x1, y1 = positions[prec]
                            x2, y2 = positions[tache["id"]]
                            couleur = PertEngineGraphics.ROUGE if prec in chemin_critique and tache["id"] in chemin_critique else PertEngineGraphics.NOIR
                            PertEngineGraphics.dessiner_fleche(x1 + 3 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace + offset_x, y1 + PertEngineGraphics.taille_case + offset_y, x2 + offset_x, y2 + PertEngineGraphics.taille_case + offset_y, 1.0, couleur)
                
                elif mode == 2:
                    print(offset_x, offset_y)
                    PertEngineGraphics.afficher_taches_par_projet(taches_,tache_priorisees, temps_taches, temps_tard, chemin_critique, -offset_x, -offset_y, 1.0, (font, font_bold))
                    
                pygame.display.flip()
                pygame.image.save(PertEngineGraphics.fenetre, f"Image/capture_{i}_{j}.png")
                images.append(f"Image/capture_{i}_{j}.png")

        # Assembler les images
        largeur_totale = int(captures_x * PertEngineGraphics.fenetre.get_width())
        hauteur_totale = int(captures_y * PertEngineGraphics.fenetre.get_height())
        image_finale = Image.new("RGB", (largeur_totale, hauteur_totale))
        for i in range(int(captures_x)):
            for j in range(int(captures_y)):
                img = Image.open(f"Image/capture_{i}_{j}.png")
                image_finale.paste(img, (i * PertEngineGraphics.fenetre.get_width(), j * PertEngineGraphics.fenetre.get_height()))
        image_finale.save("reseau_complet.png")
        print("Réseau complet capturé avec succès.")


    def afficher_taches_par_projet(taches,tache_priorisees, temps_taches, temps_tard, chemin_critique, offset_x, offset_y, zoom, font):
        # Séparer les tâches par catégorie
        taches_digit = [tache for tache in taches if tache["id"] < 100]
        taches_paiement = [tache for tache in taches if 100 <= tache["id"] < 200]
        taches_interne = [tache for tache in taches if 200 <= tache["id"] < 300]
        taches_client = [tache for tache in taches if tache["id"] >= 300]

        # Dictionnaire pour stocker les positions de toutes les tâches
        positions = {}

        # Fonction pour afficher un groupe de tâches
        def afficher_groupe_taches(taches_groupe, start_x, start_y):
            y_position = start_y
            colonnes = {}

            for tache in taches_groupe:
                if not tache["predecesseurs"]:
                    # Tâches de début de ligne
                    x_position = start_x
                    if x_position not in colonnes:
                        colonnes[x_position] = y_position
                    else:
                        colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                    y_position = colonnes[x_position]
                else:
                    # Tâches liées
                    try:
                        max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                    except KeyError as e:
                        # Si une tâche précédente n'a pas été trouvée, la placer à la fin de la ligne 
                        max_x_position = start_x
                        for prec in tache["predecesseurs"]:
                            if prec in positions:
                                max_x_position = max(max_x_position, positions[prec][0])
                        
                    x_position = max_x_position + 3 * PertEngineGraphics.taille_case + 20 * PertEngineGraphics.espace
                    if x_position not in colonnes:
                        colonnes[x_position] = start_y
                    else:
                        colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                    y_position = colonnes[x_position]

                positions[tache["id"]] = (x_position, y_position)
                px, py = PertEngineGraphics.camera_transformation(x_position, y_position, offset_x, offset_y, zoom)
                PertEngineGraphics.dessiner_tache(tache,tache_priorisees, px, py, temps_taches, temps_tard, zoom, font)

        # Afficher chaque groupe de tâches
        start_x = 10
        start_y = 10
        afficher_groupe_taches(taches_digit, start_x, start_y)
        afficher_groupe_taches(taches_paiement, start_x, start_y + 1300 + 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace)
        afficher_groupe_taches(taches_interne, start_x, start_y + 2800 + 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace)
        afficher_groupe_taches(taches_client, start_x, start_y + 4300 + 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace)
        
        # Dessiner les flèches entre toutes les tâches
        for tache in taches:
            for prec in tache["predecesseurs"]:
                if prec in positions:
                    x1, y1 = positions[prec]
                    x2, y2 = positions[tache["id"]]
                    couleur = PertEngineGraphics.ROUGE if prec in chemin_critique and tache["id"] in chemin_critique else PertEngineGraphics.NOIR
                    px1, py1 = PertEngineGraphics.camera_transformation(x1 + 3 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace, y1 + (PertEngineGraphics.taille_case + 3 * PertEngineGraphics.espace) / 2, offset_x, offset_y, zoom)
                    px2, py2 = PertEngineGraphics.camera_transformation(x2, y2 + (PertEngineGraphics.taille_case + 3 * PertEngineGraphics.espace) / 2, offset_x, offset_y, zoom)
                    PertEngineGraphics.dessiner_fleche(px1, py1, px2, py2, zoom, couleur)
    

    def dessiner_taches(taches, zoom, mode, camera_x, camera_y):
        # Genérer la police d'écriture en dehors de la boucles du dessin des taches.
        font = pygame.font.Font(None, int(24 * zoom))
        font_bold = pygame.font.Font(None, int(24 * zoom))
        font_bold.set_bold(True)
        
        if mode == 1:
            # Dessiner les tâches
            y_position = 10  # Position de départ pour l'affichage des tâches
            positions = {}
            colonnes = {}  # Dictionnaire pour suivre les colonnes et les lignes

            for tache in PertEngineCore.taches_:
                if not tache["predecesseurs"]:
                    # Tâches de début de ligne
                    x_position = 10
                    if x_position not in colonnes:
                        colonnes[x_position] = y_position
                    else:
                        colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                    y_position = colonnes[x_position]
                else:
                    # Tâches liées
                    max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                    x_position = max_x_position + 3 * PertEngineGraphics.taille_case + 20 * PertEngineGraphics.espace
                    if x_position not in colonnes:
                        colonnes[x_position] = 10
                    else:
                        colonnes[x_position] += 2 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace
                    y_position = colonnes[x_position]

                positions[tache["id"]] = (x_position, y_position)
                px, py = PertEngineGraphics.camera_transformation(x_position, y_position, camera_x, camera_y, zoom)
                PertEngineGraphics.dessiner_tache(tache, PertEngineCore.tache_priorisees, px, py, PertEngineCore.temps_taches, PertEngineCore.temps_taches_tard, zoom, (font, font_bold))

            # Dessiner les flèches
            for tache in PertEngineCore.taches_:
                for prec in tache["predecesseurs"]:
                    x1, y1 = positions[prec]
                    x2, y2 = positions[tache["id"]]
                    couleur = PertEngineGraphics.ROUGE if prec in PertEngineCore.chemin_critique and tache["id"] in PertEngineCore.chemin_critique else PertEngineGraphics.NOIR
                    px1, py1 = PertEngineGraphics.camera_transformation(x1 + 3 * PertEngineGraphics.taille_case + 2 * PertEngineGraphics.espace, y1 + (PertEngineGraphics.taille_case + 3 * PertEngineGraphics.espace) / 2, camera_x, camera_y, zoom)
                    px2, py2 = PertEngineGraphics.camera_transformation(x2, y2 + (PertEngineGraphics.taille_case + 3 * PertEngineGraphics.espace) / 2, camera_x, camera_y, zoom)
                    PertEngineGraphics.dessiner_fleche(px1, py1, px2, py2, zoom, couleur)
        else:
            # Afficher les tâches par projet
            PertEngineGraphics.afficher_taches_par_projet(PertEngineCore.taches_,PertEngineCore.tache_priorisees, PertEngineCore.temps_taches, PertEngineCore.temps_taches_tard, PertEngineCore.chemin_critique, camera_x, camera_y, zoom, (font, font_bold))

