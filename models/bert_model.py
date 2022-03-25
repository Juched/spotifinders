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
            config = yaml.load(f, Loader=Loader)
        self.ecstacy = config["ecstacy"]
        self.admiration = config["admiration"]
        self.terror = config["terror"]
        self.amazement = config["amazement"]
        self.grief = config["grief"]
        self.loathing = config["loathing"]
        self.rage = config["rage"]
        self.vigilance = config["vigilance"]
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

        return self.model(tok_input["input_ids"], tok_input["attention_mask"])
