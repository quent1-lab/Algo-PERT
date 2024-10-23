import networkx as nx
import pygame
import sys
import Taches

# Initialisation de Pygame
pygame.init()

# Paramètres d'affichage
largeur_fenetre = 1200
hauteur_fenetre = 800
taille_case = 50
espace = 20

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
def dessiner_tache(tache, x, y, temps_taches, zoom):
    taille_case_zoom = taille_case * zoom
    espace_zoom = espace * zoom
    # Si tache < 100 en bleu, ou < 200 en vert, ou < 300 en orange, sinon en magenta
    if tache["id"] < 100:
        couleur = BLEU
    elif tache["id"] < 200:
        couleur = (0, 128, 0)
    elif tache["id"] < 300:
        couleur = (255, 165, 0)
    else:
        couleur = (255, 0, 255)
    
    pygame.draw.rect(fenetre, couleur, (x, y, 3 * taille_case_zoom + 2 * espace_zoom, 2 * taille_case_zoom + espace_zoom))
    # Affichage des informations
    font = pygame.font.Font(None, int(24 * zoom))
    
    # Temps de début
    debut_text = font.render(f"Début: {temps_taches[tache['id']][0]:.1f}", True, NOIR)
    fenetre.blit(debut_text, (x + espace_zoom, y + espace_zoom))
    
    # Nom de la tâche
    nom_text = font.render(f"Tâche {tache['id']}", True, NOIR)
    fenetre.blit(nom_text, (x + espace_zoom, y + taille_case_zoom + espace_zoom))
    
    # Temps de fin
    fin_text = font.render(f"Fin: {temps_taches[tache['id']][1]:.1f}", True, NOIR)
    fenetre.blit(fin_text, (x + 2 * taille_case_zoom + espace_zoom, y + espace_zoom))
    
    # Durée
    duree_text = font.render(f"Durée: {tache['duree']}", True, NOIR)
    fenetre.blit(duree_text, (x + 2 * taille_case_zoom + espace_zoom, y + taille_case_zoom + espace_zoom))

# Fonction pour dessiner une flèche entre deux tâches
def dessiner_fleche(x1, y1, x2, y2, zoom, couleur=NOIR):
    pygame.draw.line(fenetre, couleur, (x1, y1), (x2, y2), int(3 * zoom))
    pygame.draw.polygon(fenetre, couleur, [(x2, y2), (x2 - 10 * zoom, y2 - 5 * zoom), (x2 - 10 * zoom, y2 + 5 * zoom)])
    
# Boucle principale
def main():
    global taches
    taches_ = trier_taches_topologiquement(taches)
    temps_taches = calcul_dates(taches_)
    chemin_critique = calcul_chemin_critique(taches_)
    offset_x, offset_y = 0, 0  # Offsets pour le déplacement
    zoom = 1.0  # Niveau de zoom
    speed = 50

    while True:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            offset_x += speed
        if keys[pygame.K_RIGHT]:
            offset_x -= speed
        if keys[pygame.K_UP]:
            offset_y += speed
        if keys[pygame.K_DOWN]:
            offset_y -= speed
        if keys[pygame.K_c]:
            zoom = 0.3  # Dézoomer
            # Recentrer l'affichage
            offset_x = 0
            offset_y = 0
        if keys[pygame.K_v]:
            zoom = 1.0  # Revenir à la normale
            # Recentrer l'affichage
            offset_x = 0
            offset_y = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Remplir l'écran de blanc
        fenetre.fill(BLANC)

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
                x_position = max_x_position + 3 * taille_case + 5 * espace
                if x_position not in colonnes:
                    colonnes[x_position] = 50
                else:
                    colonnes[x_position] += 2 * taille_case + 2 * espace
                y_position = colonnes[x_position]

            positions[tache["id"]] = (x_position, y_position)
            dessiner_tache(tache, x_position * zoom + offset_x, y_position * zoom + offset_y, temps_taches, zoom)

        # Dessiner les flèches
        for tache in taches_:
            for prec in tache["predecesseurs"]:
                x1, y1 = positions[prec]
                x2, y2 = positions[tache["id"]]
                couleur = ROUGE if prec in chemin_critique and tache["id"] in chemin_critique else NOIR
                dessiner_fleche(x1 * zoom + 3 * taille_case * zoom + 2 * espace * zoom + offset_x, y1 * zoom + taille_case * zoom + offset_y, x2 * zoom + offset_x, y2 * zoom + taille_case * zoom + offset_y, zoom, couleur)

        # Actualiser l'affichage
        pygame.display.flip()
        # Limiter la vitesse de rafraîchissement
        pygame.time.Clock().tick(60)
        

# Exécuter la fonction principale
if __name__ == "__main__":
    main()