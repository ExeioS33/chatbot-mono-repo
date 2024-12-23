from flask import Flask, request, jsonify
from flask_cors import CORS
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

# Initialisation du pipeline QA
qa_pipeline = pipeline(
    "question-answering",
    model="etalab-ia/camembert-base-squadFR-fquad-piaf",
    tokenizer="etalab-ia/camembert-base-squadFR-fquad-piaf",
)

# Stockage simple des documents
documents = {}


def get_document_specific_info(question, doc_type, text, informations):
    """Extraire les informations spécifiques selon le type de document."""
    question = question.lower()

    if doc_type == "BULLETIN DE SALAIRE":
        patterns = {
            "salaire_net": r"salaire net[:\s]*([0-9]+[.,][0-9]{2})",
            "salaire_brut": r"salaire brut[:\s]*([0-9]+[.,][0-9]{2})",
            "numero_secu": r"\b[12][0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])[0-9]{3}[0-9]{3}[0-9]{2}\b",
            "employeur": r"employeur[:\s]*([^\n]+)",
            "periode": r"période[:\s]*([^\n]+)",
        }

    elif doc_type == "CONTRAT":
        patterns = {
            "date_debut": r"date de début[:\s]*([^\n]+)",
            "salaire": r"salaire[:\s]*([0-9]+[.,][0-9]{2})",
            "poste": r"poste[:\s]*([^\n]+)",
            "durée": r"durée[:\s]*([^\n]+)",
        }

    elif doc_type == "NOTE DE FRAIS":
        patterns = {
            "montant_total": r"total[:\s]*([0-9]+[.,][0-9]{2})",
            "date_frais": r"date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})",
            "nature_frais": r"nature[:\s]*([^\n]+)",
        }

    elif doc_type == "FACTURE":
        patterns = {
            "numero_facture": r"facture n°[:\s]*([^\n]+)",
            "montant_ht": r"montant ht[:\s]*([0-9]+[.,][0-9]{2})",
            "montant_ttc": r"montant ttc[:\s]*([0-9]+[.,][0-9]{2})",
            "date_facture": r"date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})",
        }

    elif doc_type == "CHEQUE":
        patterns = {
            "montant": r"montant[:\s]*([0-9]+[.,][0-9]{2})",
            "beneficiaire": r"ordre[:\s]*([^\n]+)",
            "date_cheque": r"date[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})",
        }

    else:
        return None

    # Recherche des informations spécifiques selon les patterns
    for key, pattern in patterns.items():
        if key.lower() in question:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return {"answer": matches.group(1), "confidence": 1.0}

    return None


@app.route("/index", methods=["POST"])
def index_document():
    """Stocker un nouveau document."""
    data = request.json
    if not data or "text" not in data or "doc_id" not in data:
        return jsonify({"error": "Données manquantes"}), 400

    documents[data["doc_id"]] = {
        "text": data["text"],
        "type": data.get("type", "AUTRE"),
        "informations": data.get("informations", {}),
    }
    return jsonify({"message": "Document indexé"}), 200


@app.route("/query", methods=["POST"])
def answer_question():
    """Répondre à une question."""
    data = request.json
    if not data or "question" not in data:
        return jsonify({"error": "Question manquante"}), 400

    question = data["question"]
    doc_id = data.get("doc_id")

    if doc_id and doc_id in documents:
        doc = documents[doc_id]

        # Essayer d'abord l'extraction spécifique au type de document
        specific_answer = get_document_specific_info(
            question, doc["type"], doc["text"], doc["informations"]
        )

        if specific_answer:
            return jsonify(specific_answer)

        # Si pas de réponse spécifique, utiliser le modèle QA
        result = qa_pipeline(question=question, context=doc["text"])
        return jsonify(
            {"answer": result["answer"], "confidence": round(result["score"], 4)}
        )

    return jsonify({"error": "Document non trouvé"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
