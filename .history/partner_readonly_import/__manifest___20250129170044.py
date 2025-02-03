import time
import sys

def simulate_download():
    print("Simulation de téléchargement de vidéo WhatsApp...")
    for i in range(101):
        time.sleep(0.1)  # Simule le temps de téléchargement
        sys.stdout.write(f"\rProgression: {i}%")
        sys.stdout.flush()
    print("\nTéléchargement terminé!\n")

def simulate_send():
    print(f"Envoi du contenu à +221 772824168...")
    time.sleep(2)  # Simule le temps d'envoi
    print("Contenu envoyé avec succès!\n")

def display_message():
    while True:
        print("Vous n'avez pas les droits nécessaires pour télécharger le contenu de la Google Pixel 8.")
        time.sleep(1)  # Affiche le message en boucle toutes les secondes

if __name__ == "__main__":
    simulate_download()
    simulate_send()
    display_message()