import pygame
import sys
import data_taches_projets
import UserInterface
import temps_taches_personne
import math
import pert_engine

# Initialisation de Pygame
pygame.init()

# Paramètres d'affichage
largeur_fenetre = 1200
hauteur_fenetre = 800

# Création de la fenêtre
fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
pygame.display.set_caption("Visualisation du Réseau PERT")

# Boucle principale
def main():
    pert_engine.PertEngineGraphics.fenetre = fenetre
    pert_engine.PertEngineCore.taches = data_taches_projets.taches_sciado
    pert_engine.PertEngineCore.calculate()
    
    # print("Tâches à effectuer par catégorie:")
    # for projet in ordre_taches:
    #     print(f"Projet {projet[0]['id'] // 100}: {[tache['id'] for tache in projet]}")
    
    camera_x, camera_y = 0, 0  # Position de la caméra
    zoom = 1.0  # Niveau de zoom
    zoom_speed = 5
    speed = 2000
    frame_rate = 60
    delta_time = 1 / frame_rate
    mode = 1 # Mode de visualisation (1: Toutes les tâches, 2: Par projet)

    
    mouse_grabbing = False
    record_cam_x = 0
    record_cam_y = 0
    mouse_click_x = 0
    mouse_click_y = 0

    previus_mouse_pressed = False

    while True:
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            camera_x -= speed * delta_time / zoom
        if keys[pygame.K_RIGHT]:
            camera_x += speed * delta_time / zoom
        if keys[pygame.K_UP]:
            camera_y -= speed * delta_time / zoom
        if keys[pygame.K_DOWN]:
            camera_y += speed * delta_time / zoom
        if keys[pygame.K_v]:
            zoom += zoom_speed * zoom * delta_time
        if keys[pygame.K_c]:
            zoom -= zoom_speed * zoom * delta_time


        # Gestion des entrées souris pour le déplacement et le zoom
        if pygame.mouse.get_pressed(3)[0] and not mouse_grabbing:
            mouse_grabbing = True
            mouse_click_x, mouse_click_y = pygame.mouse.get_pos()
            record_cam_x = camera_x
            record_cam_y = camera_y
        
        if not pygame.mouse.get_pressed(3)[0]:
            mouse_grabbing = False
        
        if mouse_grabbing:
            mx, my = pygame.mouse.get_pos()
            vmx, vmy = (mouse_click_x - mx, mouse_click_y - my)
            camera_x, camera_y = (record_cam_x + vmx / zoom, record_cam_y + vmy / zoom)

        # Gestion des entrées clavier pour les captures d'écran
        if keys[pygame.K_s]:
            pert_engine.PertEngineGraphics.capturer_ecran("capture.png")
        if keys[pygame.K_r]:
            pert_engine.PertEngineGraphics.capturer_reseau_complet(mode, pert_engine.PertEngineCore.tache_priorisees, pert_engine.PertEngineCore.taches)  # Capturer tout le réseau

        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                zoom += 0.1 * zoom * event.y
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                pygame.quit()
                sys.exit()
            if keys[pygame.K_m]:
                mode = 1 if mode == 2 else 2
            
        
        # Remplir l'écran de blanc
        fenetre.fill(pert_engine.PertEngineGraphics.BLANC)

        pert_engine.PertEngineGraphics.dessiner_taches(pert_engine.PertEngineCore.taches, zoom, mode, camera_x, camera_y)

        # Render user interface
        UserInterface.render_interface(fenetre, pygame.mouse.get_pos(), previus_mouse_pressed and not pygame.mouse.get_pressed(3)[0])
        UserInterface.hot_bar.width = largeur_fenetre
        previus_mouse_pressed = pygame.mouse.get_pressed(3)[0]
        
        if UserInterface.button_mode.clicked:
            mode = 1 if mode == 2 else 2
        if UserInterface.button_screen.clicked:
            pert_engine.PertEngineGraphics.capturer_reseau_complet(mode, pert_engine.PertEngineCore.tache_priorisees)  # Capturer tout le réseau

        # Affiche l'ordre des tâches en fonction de la priorité en haut à gauche
        # tache_priorisees = prioriser_taches_par_impact(taches)
        # font = pygame.font.Font(None, 24)
        # for i, tache in enumerate(tache_priorisees):
        #     x = 10 + 70 * (i % 17)
        #     y = 30 * (i // 17) + 10
        #     text = font.render(f"{tache['id']} : {tache['priorite']} |", True, NOIR)
        #     fenetre.blit(text, (x, y))
        
        # Actualiser l'affichage
        pygame.display.flip()
        # Limiter la vitesse de rafraîchissement
        pygame.time.Clock().tick(frame_rate)
        

# Exécuter la fonction principale
if __name__ == "__main__":
    main()