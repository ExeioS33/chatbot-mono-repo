from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
from PIL import Image
import pytesseract
from transformers import pipeline
import re

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

# Initialisation des pipelines
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def extract_text_from_pdf(pdf_file):
    """Extraire le texte d'un PDF."""
    with pdfplumber.open(pdf_file) as pdf:
        return " ".join(page.extract_text() for page in pdf.pages)


def extract_text_from_image(image_file):
    """Extraire le texte d'une image avec amélioration de la qualité."""
    image = Image.open(image_file)

    # Conversion en niveaux de gris pour améliorer la reconnaissance
    image = image.convert("L")

    # Configuration de Tesseract pour améliorer la reconnaissance
    custom_config = r"--oem 3 --psm 6 -l fra"

    # Extraction du texte avec configuration personnalisée
    text = pytesseract.image_to_string(image, config=custom_config)

    return text


def classify_document(text):
    """Classifier le type de document."""
    # Définition des mots-clés spécifiques pour chaque type de document
    document_keywords = {
        "NOTE DE FRAIS": [
            "note de frais",
            "frais professionnels",
            "remboursement de frais",
            "frais de déplacement",
            "frais de repas",
            "frais kilométriques",
            "frais de transport",
            "justificatif",
            "dépenses",
            "remboursement",
            "mission",
            "déplacement professionnel",
        ],
        "FACTURE": [
            "facture",
            "numéro de facture",
            "tva",
            "total ttc",
            "total ht",
            "bon de commande",
            "devis",
            "acompte",
        ],
        "BULLETIN DE SALAIRE": [
            "bulletin de salaire",
            "bulletin de paie",
            "salaire net",
            "salaire brut",
            "cotisations",
            "charges sociales",
            "net à payer",
        ],
    }

    # Première passe : recherche de mots-clés spécifiques
    text_lower = text.lower()
    scores = {doc_type: 0 for doc_type in document_keywords.keys()}

    for doc_type, keywords in document_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                scores[doc_type] += 1

    # Si on trouve des correspondances fortes avec les mots-clés
    max_score = max(scores.values())
    if max_score > 0:
        best_match = max(scores.items(), key=lambda x: x[1])
        confidence = min(best_match[1] / len(document_keywords[best_match[0]]), 1.0)
        if confidence > 0.3:  # Seuil de confiance minimum
            return {"type": best_match[0], "scores": [confidence]}

    # Si pas de correspondance forte, utiliser le modèle zero-shot
    labels = [
        "NOTE DE FRAIS",
        "FACTURE",
        "BULLETIN DE SALAIRE",
        "CONTRAT",
        "CHEQUE",
        "AUTRE",
    ]

    # Amélioration du contexte pour le modèle zero-shot
    hypothesis_template = "Ce document est {}"
    result = classifier(
        text, labels, hypothesis_template=hypothesis_template, multi_label=False
    )

    return {
        "type": result["labels"][0],
        "scores": [round(score, 4) for score in result["scores"]],
    }


def extract_basic_info(text):
    """Extraire les informations de base du texte."""
    # Expressions régulières pour l'extraction
    patterns = {
        "montants": r"\b\d+[.,]\d{2}\s*€?\b",
        "dates": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
        "emails": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    }

    info = {}
    for key, pattern in patterns.items():
        matches = re.finditer(pattern, text)
        info[key] = [match.group() for match in matches]

    return info


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400

    file = request.files["file"]
    try:
        # Extraction du texte selon le type de fichier
        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file)
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            text = extract_text_from_image(file)
        else:
            return jsonify({"error": "Format de fichier non supporté"}), 400

        if not text:
            return jsonify({"error": "Aucun texte extrait"}), 400

        # Classification et extraction d'informations
        classification = classify_document(text)
        basic_info = extract_basic_info(text)

        return jsonify(
            {
                "message": "Analyse réussie",
                "text": text,
                "type": classification["type"],
                "confidence": classification["scores"][0],
                "informations": basic_info,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
