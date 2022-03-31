"""Class implementing BERT model"""
import string
from nlp_model import NLPModel
from transformers import BertTokenizer

import yaml
from yaml import Loader, Dumper
import torch


class BERTModel(NLPModel):
    """
    Class which loads and runs BERT model.
    """

    def __init__(self):
        """
        This class implements BERT and runs it for text input.

        Returns:
            A BERT model
        """
        with open("../cfg/config.yaml", "r") as f:
            self.config = yaml.load(f, Loader=Loader)

        self.model = torch.load("bin/bert.mod")
        self.tokenizer = BertTokenizer.from_pretrained(
            "bert-base-uncased", do_lower_case=True
        )

    def convert_to_t_n(self, example):
        """
        Converts an example to a tensor example

        Returns:
            example dict with attention mask and input ids as tensors
        """
        example["attention_mask"] = torch.Tensor([example["attention_mask"]])
        example["input_ids"] = torch.Tensor([example["input_ids"]])
        return example

    def get_vector(self, text: string):
        """
        Gets the vector that is generated from this string

        Args:
            text: The text to generate the vector off of


        Returns:
            A length 3 dictionary which has
            {'danceability': float, 'energy': float, 'valence': float}.
        """
        tok_input = self.tokenizer(text, padding=True, max_length=100)
        tok_input = self.convert_to_t_n(tok_input)
        classes = self.model(tok_input["input_ids"], tok_input["attention_mask"])
        feature_dict = {"danceability": 0.0, "energy": 0.0, "valence": 0.0}
        classes = classes.tolist()
        
        #clamp so we don't get weird nums
        for c in classes:
            if c < 0:
                c = 0.0
            elif c > 1:
                c = 1.0

            c = c - 0.5
            c = c * 2

        #apply configs
        feature_dict["danceability"] = (
            (self.config["d"]["e"] * classes[0])
            + (self.config["d"]["ad"] * classes[1])
            + (self.config["d"]["t"] * classes[2])
            + (self.config["d"]["am"] * classes[3])
            + (self.config["d"]["g"] * classes[4])
            + (self.config["d"]["l"] * classes[5])
            + (self.config["d"]["r"] * classes[6])
            + (self.config["d"]["v"] * classes[7])
        )

        feature_dict["energy"] = (
            (self.config["e"]["e"] * classes[0])
            + (self.config["e"]["ad"] * classes[1])
            + (self.config["e"]["t"] * classes[2])
            + (self.config["e"]["am"] * classes[3])
            + (self.config["e"]["g"] * classes[4])
            + (self.config["e"]["l"] * classes[5])
            + (self.config["e"]["r"] * classes[6])
            + (self.config["e"]["v"] * classes[7])
        )

        feature_dict["valence"] = (
            (self.config["v"]["e"] * classes[0])
            + (self.config["v"]["ad"] * classes[1])
            + (self.config["v"]["t"] * classes[2])
            + (self.config["v"]["am"] * classes[3])
            + (self.config["v"]["g"] * classes[4])
            + (self.config["v"]["l"] * classes[5])
            + (self.config["v"]["r"] * classes[6])
            + (self.config["v"]["v"] * classes[7])
        )

        # clamp
        for k, v in feature_dict.items():
            if v < 0:
                v = 0
            elif v > 1:
                v = 1

        return feature_dict
