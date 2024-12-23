# Nom de l'image Docker
IMAGE_NAME = step_sanda
PORT = 8080

# Commande pour construire l'image Docker
build:
	docker build -t $(IMAGE_NAME) .

# Commande pour lancer un conteneur Docker
run:
	docker run -d -p $(PORT):8080 --name $(IMAGE_NAME)_container $(IMAGE_NAME)

# Commande pour arrêter et supprimer un conteneur Docker
clean:
	docker stop $(IMAGE_NAME)_container || true
	docker rm $(IMAGE_NAME)_container || true

# Commande pour reconstruire l'image et relancer le conteneur
rebuild: clean build run

