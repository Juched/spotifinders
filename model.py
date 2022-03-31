"""App module."""

from flask import Flask, request, jsonify

from models.bert_model import BERTModel

app = Flask(__name__)

model = BERTModel()


@app.route("/api/v1/bert", methods=["POST"])
def bert():
    """Route for BERT model"""
    vector = model.get_vector(request.json["text"])
    return jsonify({"vector": vector})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
