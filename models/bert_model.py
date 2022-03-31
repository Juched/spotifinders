"""Class implementing BERT model"""
import string
import os
from models.nlp_model import NLPModel
from transformers import BertTokenizer, BertModel

import yaml
from yaml import Loader, Dumper
import torch


class CamembertRegressor(torch.nn.Module):
    def __init__(self, drop_rate=0.2, freeze_camembert=False):
        super(CamembertRegressor, self).__init__()
        D_in, D_out = 768, 8

        self.camembert = BertModel.from_pretrained("bert-base-uncased")
        self.regressor = torch.nn.Sequential(
            torch.nn.Dropout(drop_rate), torch.nn.Linear(D_in, D_out)
        )

    def forward(self, input_ids=None, attention_mask=None, labels=None):
        outputs = self.camembert.forward(
            input_ids=input_ids, attention_mask=attention_mask
        )
        class_label_output = outputs[1]
        outputs = self.regressor(class_label_output)
        return outputs


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

        direc = os.path.dirname(__file__)
        filename = os.path.join(direc, "../cfg/config.yaml")
        with open(filename, "r") as f:
            self.config = yaml.load(f, Loader=Loader)

        direc = os.path.dirname(__file__)
        filename = os.path.join(direc, "bin/bert.mod")
        device = torch.device("cpu")

        self.model = CamembertRegressor(drop_rate=0.2)
        self.model.load_state_dict(torch.load(filename, map_location=device))
        self.model.eval()
        self.tokenizer = BertTokenizer.from_pretrained(
            "bert-base-uncased", do_lower_case=True
        )
        print("Loaded model")

    def convert_to_t_n(self, example):
        """
        Converts an example to a tensor example

        Returns:
            example dict with attention mask and input ids as tensors
        """
        example["attention_mask"] = torch.Tensor([example["attention_mask"]]).long()
        example["input_ids"] = torch.Tensor([example["input_ids"]]).long()
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
        classes = classes.tolist()[0]
        print(f"Raw Classes = {classes}")
        # clamp so we don't get weird nums
        for idx, c in enumerate(classes):
            if c < 0:
                classes[idx] = 0.0
            elif c > 1:
                classes[idx] = 1.0

            classes[idx] = c - 0.5
            classes[idx] = c * 2

        print(f"Clamped Classes = {classes}")
        # apply configs
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
                feature_dict[k] = 0
            elif v > 1:
                feature_dict[k] = 1

        print(feature_dict)

        return feature_dict
