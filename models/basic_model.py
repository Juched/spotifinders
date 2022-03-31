"""NLP Model module."""
from collections import Counter

# from typing import List


from basic_regression_helper import Indexer, UnigramFeatureExtractor
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from nlp_model import NLPModel
import yaml
from yaml import Loader


def get_feature_vector(feature_counter: Counter, feature_extractor) -> np.ndarray:
    """ "Helper function to create feature vector from feature counter"""

    feature_vector = np.zeros(len(feature_extractor.get_indexer()) + 1)

    for feature in feature_counter:
        feature_idx = feature_extractor.get_indexer().index_of(feature)
        feature_vector[feature_idx] = feature_counter[feature]

    feature_vector[-1] = 1

    return feature_vector


class SpotifinderModel(NLPModel):
    """Spotifinder NLP Model"""

    def __init__(self):
        super().__init__()
        self.indexer = Indexer()
        self.uni_fv = UnigramFeatureExtractor(self.indexer)

        # load lyric data
        data = pd.DataFrame(pd.read_csv("lyric_data.csv"))

        # preprocess data
        data.dropna(subset=["lyrics"], inplace=True)
        data = data.astype({"lyrics": str}, errors="raise")

        # filter lyrics
        lyrics = []

        self.ecstacy = 0
        self.admiration = 0
        self.terror = 0
        self.amazement = 0
        self.grief = 0
        self.loathing = 0
        self.rage = 0
        self.vigilance = 0
        with open("../cfg/config.yaml", "r", encoding="utf8") as file:
            config = yaml.load(file, Loader=Loader)
        self.ecstacy = config["ecstacy"]
        self.admiration = config["admiration"]
        self.terror = config["terror"]
        self.amazement = config["amazement"]
        self.grief = config["grief"]
        self.loatsentencehing = config["loathing"]
        self.rage = config["rage"]
        self.vigilance = config["vigilance"]

        for song in data["lyrics"].tolist():
            song = song.replace("\n", " ")
            song = song.replace(".", " ")
            song = song.replace(",", " ")
            song = song.replace("(", " ")
            song = song.replace(")", " ")
            lyrics.append(song.lower())

        # get feature vectors
        counter_list = []
        for song in lyrics:
            words = song.split(" ")
            counter = self.uni_fv.extract_features(words, True)
            counter_list.append(counter)

        feature_vector_list = []
        for counter in counter_list:
            feature_vector = get_feature_vector(counter, self.uni_fv)
            feature_vector = np.where(feature_vector > 0, 1, 0)
            feature_vector_list.append(feature_vector)

        feat_matrix = np.array(feature_vector_list)

        # danceability model
        x_train, _, y_train, _ = train_test_split(
            feat_matrix, data[["danceability"]], test_size=0.25, random_state=44
        )
        self.dance_reg = LinearRegression().fit(x_train, y_train)

        # energy model
        x_train, _, y_train, _ = train_test_split(
            feat_matrix, data[["energy"]], test_size=0.30, random_state=44
        )
        self.energy_reg = LinearRegression().fit(x_train, y_train)

        # valence model
        x_train, _, y_train, _ = train_test_split(
            feat_matrix, data[["valence"]], test_size=0.30, random_state=44
        )

        self.valence_reg = LinearRegression().fit(x_train, y_train)

    def get_vector(self, text: str) -> np.array:
        """Get spotify vector for sentence."""

        text = text.replace("\n", " ")
        text = text.replace(".", " ")
        text = text.replace(",", " ")
        text = text.replace("(", " ")
        text = text.replace(")", " ")
        text = text.lower()

        words = text.split(" ")
        counter = self.uni_fv.extract_features(words, False)

        feature_vector = get_feature_vector(counter, self.uni_fv)
        feature_vector = np.where(feature_vector > 0, 1, 0)
        feature_vector = np.reshape(feature_vector, (1, feature_vector.shape[0]))

        # dance = self.dance_reg.predict(feature_vector)[0][0]
        # energy = self.energy_reg.predict(feature_vector)[0][0]
        # valence = self.valence_reg.predict(feature_vector)[0][0]

        output = np.random.rand(3)

        # Ensure values between 0 and 1
        for i, feat in enumerate(output):
            if feat > 1.0:
                output[i] = 1.0
            elif feat < 0.0:
                output[i] = 0.0

        return {"danceability": output[0], "energy": output[1], "valence": output[2]}

    def do_nothing(self):
        """Do nothing."""


if __name__ == "__main__":

    model = SpotifinderModel()

    SENT_1 = "Brown guilty eyes and\n\
            Little white lies, yeah\n\
            I played dumb but I always knew\n\
            That you talked to her\n\
            Maybe did even worse\n\
            I kept quiet so I could keep you\n\
            And ain't it funny how you ran to her\n\
            The second that we called it quits?\n\
            And ain't it funny how you said you were friends?\n\
            Now it sure as hell don't look like it\n\
            You betrayed me\n\
            And I know that you'll never feel sorry\n\
            For the way I hurt, yeah\n\
            You talked to her when we were together\n\
            Loved you at your worst but that didn't matter\n\
            It took you two weeks to go off and date her\n\
            Guess you didn't cheat, but you're still a traitor"

    SENT_2 = "Remember the words you told me, love me 'til the day I die\n\
            Surrender my everything 'cause you made me believe you're mine\n\
            Yeah, you used to call me baby, now you calling me by name\n\
            Takes one to know one, yeah\n\
            You beat me at my own damn game\n\
            \n\
            You push and you push and I'm pulling away\n\
            Pulling away from you\n\
            I give and I give and I give and you take, give and you take\n\
            \n\
            Youngblood\n\
            Say you want me\n\
            Say you want me\n\
            Out of your life\n\
            \n\
            And I'm just a dead man walking tonight\n\
            But you need it, yeah, you need it\n\
            All of the time\n\
            Yeah, ooh ooh ooh\n\
            \n\
            Youngblood\n\
            Say you want me\n\
            Say you want me\n\
            Back in your life\n\
            \n\
            So I'm just a dead man crawling tonight\n\
            'Cause I need it, yeah, I need it\n\
            All of the time\n\
            Yeah, ooh ooh ooh\n\
            \n\
            Lately our conversations end like it's the last goodbye"

    print(model.get_vector(SENT_1))
    print(model.get_vector(SENT_2))

    SENT_3 = "I caught it bad yesterday\n\
            You hit me with a call to your place\n\
            Ain't been out in a while anyway\n\
            Was hoping I could catch you throwing smiles in my face\n\
            Romantic talking? You don't even have to try\n\
            You're cute enough to fuck with me tonight\n\
            Looking at the table and I see the reason why\n\
            Baby, you living the life, but nigga, you ain't livin' right\n\
            Cocaine and drinking with your friends\n\
            You live in the dark, boy, I cannot pretend\n\
            I'm not fazed, only here to sin\n\
            If Eve ain't in your garden, you know that you can\n\
            Call me when you want, call me when you need\n\
            Call me in the morning, I'll be on the way\n\
            Call me when you want, call me when you need\n\
            Call me out by your name, I'll be on the way like"

    print(model.get_vector(SENT_3))

    print(model.get_vector("I just want to go to home depot"))

    print(model.get_vector("I feel really sad so bad today I'm hurt lonely"))

    print(
        model.get_vector("Let's get turnt turnt up yeah lit boy let's go to town drive")
    )
