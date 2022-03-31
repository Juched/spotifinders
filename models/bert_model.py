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
            config = yaml.load(f, Loader=Loader)
        self.ecstacy = config["ecstacy"]
        self.admiration = config["admiration"]
        self.terror = config["terror"]
        self.amazement = config["amazement"]
        self.grief = config["grief"]
        self.loathing = config["loathing"]
        self.rage = config["rage"]
        self.vigilance = config["vigilance"]
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

        return self.model(tok_input["input_ids"], tok_input["attention_mask"]).tolist()
