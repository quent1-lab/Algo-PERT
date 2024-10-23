import networkx as nx
import pygame
import sys
import Taches
from PIL import Image

# Initialisation de Pygame
pygame.init()

# Paramètres d'affichage
largeur_fenetre = 1200
hauteur_fenetre = 800
taille_case = 100
espace = 10

# Création de la fenêtre
fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
pygame.display.set_caption("Visualisation du Réseau PERT")

# Couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
BLEU = (173, 216, 230)
ROUGE = (255, 0, 0)

taches = Taches.taches

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

# Fonction pour calculer les temps au plus tard
def calcul_temps_tard2(taches, temps_taches):
    temps_max = 100.6
    last_taches = []
    
    for tache in taches:
        has_child = False
        for tache2 in taches:
            if tache['id'] in tache2['predecesseurs']:
                has_child = True
                break
        if not has_child:
            last_taches.append(tache)
    
    cur_taches = last_taches
    
    for t in cur_taches:
        t['end_tard'] = temps_max
        t['start_tard'] = t['end_tard'] - t['duree']
    
    while cur_taches:
        next_cur_taches = []
        for t in cur_taches:
            child = []
            child_complet = True
            if type(t) == int:
                continue
            for t2 in cur_taches:
                if t['id'] in t2['predecesseurs']:
                    child.append(t2)
                    if t2['start_tard'] == None:
                        child_complet = False
            if child_complet and child != []:
                min_start_tard = min([t2['start_tard'] for t2 in child])
                t['end_tard'] = min_start_tard
                t['start_tard'] = t['end_tard'] - t['duree']
            for t2 in t['predecesseurs']:
                next_cur_taches.append(t2)
        cur_taches = next_cur_taches

def calcul_temps_tard(taches, temps_taches):
    G = nx.DiGraph()
    for tache in taches:
        G.add_node(tache["id"], duree=tache["duree"])
        for prec in tache["predecesseurs"]:
            G.add_edge(prec, tache["id"])

    # Trouver les tâches finales (celles sans successeurs)
    taches_finales = [tache for tache in taches if not list(G.successors(tache["id"]))]

    # Initialiser les temps au plus tard
    temps_tard = {tache["id"]: {"end_tard": float('inf'), "start_tard": float('inf')} for tache in taches}
    for tache in taches_finales:
        temps_tard[tache["id"]]["end_tard"] = temps_taches[tache["id"]][1]
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

# Fonction pour dessiner une tâche
def dessiner_tache(tache, x, y, temps_taches, temps_tard, zoom, font):
    taille_case_zoom = taille_case * zoom
    espace_zoom = espace * zoom
    nom_projet = ""
    # Si tache < 100 en bleu, ou < 200 en vert, ou < 300 en orange, sinon en magenta
    if tache["id"] < 100:
        couleur = BLEU
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
    
    pygame.draw.rect(fenetre, couleur, (x, y, 3 * taille_case_zoom + 2 * espace_zoom, 1 * taille_case_zoom + 3 * espace_zoom))
    # Affichage des informations
    
    # Temps de début
    debut_text = font.render(f"Début: {temps_taches[tache['id']][0]:.1f}", True, NOIR)
    fenetre.blit(debut_text, (x + espace_zoom, y + espace_zoom))

    # PROJET
    debut_text = font.render(f"{nom_projet}", True, NOIR)
    fenetre.blit(debut_text, (x + 1 * taille_case_zoom + 3 * espace_zoom, y + 0.5 * taille_case_zoom + espace_zoom))
    
    # Nom de la tâche
    nom_text = font.render(f"Tâche {tache['id']}", True, NOIR)
    fenetre.blit(nom_text, (x + 3 * espace_zoom + taille_case_zoom, y + espace_zoom))

    # Temps de fin
    fin_text = font.render(f"Fin: {temps_taches[tache['id']][1]:.1f}", True, NOIR)
    fenetre.blit(fin_text, (x + 2 * taille_case_zoom + 3 * espace_zoom, 
                            y + espace_zoom))
    
    # Durée
    duree_text = font.render(f"Durée: {tache['duree']}", True, NOIR)
    fenetre.blit(duree_text, (x + 1 * taille_case_zoom + 3 * espace_zoom, 
                              y + taille_case_zoom + espace_zoom))
    id = tache['id']
    # Temps start tard
    start_tard_text = font.render(f"Début: {temps_tard[id]['start_tard']:.1f}", True, NOIR)
    fenetre.blit(start_tard_text, (x + espace_zoom, y + taille_case_zoom + espace_zoom))
    
    # Temps end tard
    tard_text = font.render(f"Fin: {temps_tard[id]['end_tard']:.1f}", True, NOIR)
    fenetre.blit(tard_text, (x + 2 * taille_case_zoom + 3 * espace_zoom, 
                             y + taille_case_zoom + espace_zoom))

# Fonction pour dessiner une flèche entre deux tâches
def dessiner_fleche(x1, y1, x2, y2, zoom, couleur=NOIR):
    line_width = int(1.5 / zoom) if zoom > 0 else 1
    pygame.draw.line(fenetre, couleur, (x1, y1), (x2, y2), line_width)
    pygame.draw.polygon(fenetre, couleur, [(x2, y2), (x2 - 10 * zoom, y2 - 5 * zoom), (x2 - 10 * zoom, y2 + 5 * zoom)])

# Faire une transformation de translatio puis d'échelle et enfin translater les éléments au centre.
def camera_transformation(x, y, cam_x, cam_y, zoom):
    return ((x - cam_x) * zoom + largeur_fenetre / 2 , (y - cam_y) * zoom + hauteur_fenetre / 2)

# Fonction pour capturer l'écran
def capturer_ecran(filename="capture.png"):
    pygame.image.save(fenetre, filename)

# Fonction pour capturer tout le réseau en plusieurs images et les assembler
def capturer_reseau_complet():
    taches_ = trier_taches_topologiquement(taches)
    temps_taches = calcul_dates(taches_)
    chemin_critique = calcul_chemin_critique(taches_)
    temps_tard = calcul_temps_tard(taches_, temps_taches)

    positions = {}
    colonnes = {}
    y_position = 50
    
    for tache in taches_:
        if not tache["predecesseurs"]:
            # Tâches de début de ligne
            x_position = 50
            if x_position not in colonnes:
                colonnes[x_position] = y_position
            else:
                colonnes[x_position] += 2 * taille_case + 2 * espace
            y_position = colonnes[x_position]
        else:
            # Tâches liées
            max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
            x_position = max_x_position + 3 * taille_case + 20 * espace
            if x_position not in colonnes:
                colonnes[x_position] = 50
            else:
                colonnes[x_position] += 2 * taille_case + 2 * espace
            y_position = colonnes[x_position]

        positions[tache["id"]] = (x_position, y_position)

    # Calculer les dimensions totales du réseau
    max_x = max(positions[tache["id"]][0] for tache in taches_) + 3 * taille_case + 2 * espace
    max_y = max(positions[tache["id"]][1] for tache in taches_) + 2 * taille_case + 2 * espace

    # Calculer le nombre de captures nécessaires
    captures_x = (max_x // largeur_fenetre) - 1
    captures_y = (max_y // hauteur_fenetre) + 1
    
    # Capturer les images
    images = []
    for i in range(int(captures_x)):
        for j in range(int(captures_y)):
            offset_x = -i * largeur_fenetre
            offset_y = -j * hauteur_fenetre
            fenetre.fill(BLANC)
            y_position = 50
            positions = {}
            colonnes = {}
            font = pygame.font.Font(None, 24)
            for tache in taches_:
                if not tache["predecesseurs"]:
                    x_position = 50
                    if x_position not in colonnes:
                        colonnes[x_position] = y_position
                    else:
                        colonnes[x_position] += 2 * taille_case + 2 * espace
                    y_position = colonnes[x_position]
                else:
                    max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                    x_position = max_x_position + 3 * taille_case + 5 * espace
                    if x_position not in colonnes:
                        colonnes[x_position] = 50
                    else:
                        colonnes[x_position] += 2 * taille_case + 2 * espace
                    y_position = colonnes[x_position]
                positions[tache["id"]] = (x_position, y_position)
                dessiner_tache(tache, x_position + offset_x, y_position + offset_y, temps_taches, temps_tard,1.0, font)
            for tache in taches_:
                for prec in tache["predecesseurs"]:
                    x1, y1 = positions[prec]
                    x2, y2 = positions[tache["id"]]
                    couleur = ROUGE if prec in chemin_critique and tache["id"] in chemin_critique else NOIR
                    dessiner_fleche(x1 + 3 * taille_case + 2 * espace + offset_x, y1 + taille_case + offset_y, x2 + offset_x, y2 + taille_case + offset_y, 1.0, couleur)
            pygame.display.flip()
            pygame.image.save(fenetre, f"Image/capture_{i}_{j}.png")
            images.append(f"capture_{i}_{j}.png")

    # Assembler les images
    largeur_totale = int(captures_x * largeur_fenetre)
    hauteur_totale = int(captures_y * hauteur_fenetre)
    image_finale = Image.new("RGB", (largeur_totale, hauteur_totale))
    for i in range(int(captures_x)):
        for j in range(int(captures_y)):
            img = Image.open(f"Image/capture_{i}_{j}.png")
            image_finale.paste(img, (i * largeur_fenetre, j * hauteur_fenetre))
    image_finale.save("reseau_complet.png")
    print("Réseau complet capturé avec succès.")


# Boucle principale
def main():
    global taches
    taches_ = trier_taches_topologiquement(taches)
    temps_taches = calcul_dates(taches_)
    chemin_critique = calcul_chemin_critique(taches_)
    # temps_taches_tard = calcul_temps_tard(taches_, temps_taches)
    offset_x, offset_y = 0, 0  # Offsets pour le déplacement
    veloci_x, veloci_y = 0, 0 # Velocité de déplacement.
    zoom = 1.0  # Niveau de zoom
    speed = 5000
    friction = 10
    zoom_speed = 0.6
    frame_rate = 60
    delta_time = 1 / frame_rate
    
    temps_taches_tard = calcul_temps_tard(taches_, temps_taches)

    while True:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            veloci_x -= speed / zoom * delta_time
        if keys[pygame.K_RIGHT]:
            veloci_x += speed / zoom * delta_time
        if keys[pygame.K_UP]:
            veloci_y -= speed / zoom * delta_time
        if keys[pygame.K_DOWN]:
            veloci_y += speed / zoom * delta_time
        if keys[pygame.K_c]:
            zoom -= zoom_speed * delta_time * zoom
        if keys[pygame.K_v]:
            zoom += zoom_speed * delta_time * zoom
        if keys[pygame.K_s]:
            capturer_ecran("capture.png")
        if keys[pygame.K_r]:
            capturer_reseau_complet()  # Capturer tout le réseau

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Mise à jour de l'offset et de la vélocité
        offset_x += veloci_x * delta_time
        offset_y += veloci_y * delta_time
        veloci_x -= veloci_x * delta_time * friction
        veloci_y -= veloci_y * delta_time * friction

        # Remplir l'écran de blanc
        fenetre.fill(BLANC)

        # Genérer la police d'écriture en dehors de la boucles du dessin des taches.
        font = pygame.font.Font(None, int(24 * zoom))


        # Dessiner les tâches
        y_position = 50  # Position de départ pour l'affichage des tâches
        positions = {}
        colonnes = {}  # Dictionnaire pour suivre les colonnes et les lignes

        for tache in taches_:
            if not tache["predecesseurs"]:
                # Tâches de début de ligne
                x_position = 50
                if x_position not in colonnes:
                    colonnes[x_position] = y_position
                else:
                    colonnes[x_position] += 2 * taille_case + 2 * espace
                y_position = colonnes[x_position]
            else:
                # Tâches liées
                max_x_position = max(positions[prec][0] for prec in tache["predecesseurs"])
                x_position = max_x_position + 3 * taille_case + 20 * espace
                if x_position not in colonnes:
                    colonnes[x_position] = 50
                else:
                    colonnes[x_position] += 2 * taille_case + 2 * espace
                y_position = colonnes[x_position]

            positions[tache["id"]] = (x_position, y_position)
            px, py = camera_transformation(x_position, y_position, offset_x, offset_y, zoom)
            dessiner_tache(tache, px, py, temps_taches, temps_taches_tard, zoom, font)

        # Dessiner les flèches
        for tache in taches_:
            for prec in tache["predecesseurs"]:
                x1, y1 = positions[prec]
                x2, y2 = positions[tache["id"]]
                couleur = ROUGE if prec in chemin_critique and tache["id"] in chemin_critique else NOIR
                px1, py1 = camera_transformation(x1 + 3 * taille_case + 2 * espace, y1 + (taille_case + 3 * espace) / 2, offset_x, offset_y, zoom)
                px2, py2 = camera_transformation(x2, y2 + (taille_case + 3 * espace) / 2, offset_x, offset_y, zoom)
                dessiner_fleche(px1, py1, px2, py2, zoom, couleur)

        # Actualiser l'affichage
        pygame.display.flip()
        # Limiter la vitesse de rafraîchissement
        pygame.time.Clock().tick(frame_rate)
        

# Exécuter la fonction principale
if __name__ == "__main__":
    main()