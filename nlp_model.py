"""NLP Model module."""
from collections import Counter
from typing import List
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

class Indexer():
    """Indexer class"""
    def __init__(self):
        self.objs_to_ints = {}
        self.ints_to_objs = {}

    def __repr__(self):
        return str([str(self.get_object(i)) for i in range(0, len(self))])

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.objs_to_ints)

    def get_object(self, index):
        """Get object from index"""
        if index not in self.ints_to_objs:
            return None

        return self.ints_to_objs[index]

    def contains(self, obj):
        """ Check if indexer contains object"""
        return self.index_of(obj) != -1

    def index_of(self, obj):
        """Get index from object"""
        if obj not in self.objs_to_ints:
            return -1

        return self.objs_to_ints[obj]

    def add_and_get_index(self, obj, add=True):
        """Add object to indexer and return index, \
        additional param add determines whether object actually gets added"""
        if not add:
            return self.index_of(obj)
        if obj not in self.objs_to_ints:
            new_idx = len(self.objs_to_ints)
            self.objs_to_ints[obj] = new_idx
            self.ints_to_objs[new_idx] = obj
        return self.objs_to_ints[obj]

class UnigramFeatureExtractor():
    """Unigram Feature extractor class"""
    def __init__(self, indexer: Indexer):
        self._indexer = indexer

    def get_indexer(self) -> Indexer:
        """Get indexer"""
        return self._indexer

    def extract_features(self, sentence: List[str], add_to_indexer: bool = False) -> Counter:
        """Extract features from sentence and return counter"""

        # Contains non-unique list of all unigrams parsed from the sentence
        unigram_list: List[str] = []

        for unigram in sentence:

            index = self._indexer.add_and_get_index(unigram.lower(), add_to_indexer)

            # If unigram didn't get added to the indexer (this occurs during the testing phase)
            if index != -1:
                unigram_list.append(unigram.lower())

        return Counter(unigram_list)

def get_feature_vector(feature_counter: Counter, feature_extractor) -> np.ndarray:
    """"Helper function to create feature vector from feature counter"""

    feature_vector = np.zeros(len(feature_extractor.get_indexer()) + 1)

    for feature in feature_counter:
        feature_idx = feature_extractor.get_indexer().index_of(feature)
        feature_vector[feature_idx] = feature_counter[feature]

    feature_vector[-1] = 1

    return feature_vector

class SpotifinderModel():
    """Spotifinder NLP Model"""

    def __init__(self):
        self.indexer = Indexer()
        self.uni_fv = UnigramFeatureExtractor(self.indexer)

        # load lyric data
        data = pd.DataFrame(pd.read_csv('lyric_data.csv'))

        # preprocess data
        data.dropna(subset = ['lyrics'], inplace=True)
        data = data.astype({"lyrics": str}, errors='raise')

        # filter lyrics
        lyrics = []

        for song in data['lyrics'].tolist():
            song = song.replace('\n', ' ')
            song = song.replace('.', ' ')
            song = song.replace(',', ' ')
            song = song.replace('(', ' ')
            song = song.replace(')', ' ')
            lyrics.append(song.lower())

        # get feature vectors
        counter_list = []
        for song in lyrics:
            words = song.split(' ')
            counter = self.uni_fv.extract_features(words, True)
            counter_list.append(counter)

        feature_vector_list = []
        for counter in counter_list:
            feature_vector = get_feature_vector(counter, self.uni_fv)
            feature_vector = np.where(feature_vector > 0, 1, 0)
            feature_vector_list.append(feature_vector)

        feat_matrix = np.array(feature_vector_list)

        # danceability model
        x_train, _, y_train, _ = \
            train_test_split(feat_matrix, data[['danceability']], test_size=0.25, random_state=44)
        self.dance_reg = LinearRegression().fit(x_train, y_train)

        # energy model
        x_train, _, y_train, _ = \
            train_test_split(feat_matrix, data[['energy']], test_size=0.30, random_state=44)
        self.energy_reg = LinearRegression().fit(x_train, y_train)

        # valence model
        x_train, _, y_train, _ = \
            train_test_split(feat_matrix, data[['valence']], test_size=0.30, random_state=44)

        self.valence_reg = LinearRegression().fit(x_train, y_train)

    def get_vector(self, sentence: str) -> np.array:
        """Get spotify vector for sentence."""

        sentence = sentence.replace('\n', ' ')
        sentence = sentence.replace('.', ' ')
        sentence = sentence.replace(',', ' ')
        sentence = sentence.replace('(', ' ')
        sentence = sentence.replace(')', ' ')
        sentence = sentence.lower()

        words = sentence.split(' ')
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

        return {'danceability': output[0], 'energy': output[1], 'valence': output[2]}

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

    print(model.get_vector("Let's get turnt turnt up yeah lit boy let's go to town drive"))
