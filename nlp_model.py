"""NLP Model module."""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from typing import List

from collections import Counter

class Indexer(object):
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
        if index not in self.ints_to_objs:
            return None
        else:
            return self.ints_to_objs[index]

    def contains(self, object):
        return self.index_of(object) != -1

    def index_of(self, object):
        if object not in self.objs_to_ints:
            return -1
        else:
            return self.objs_to_ints[object]

    def add_and_get_index(self, object, add=True):
        if not add:
            return self.index_of(object)
        if object not in self.objs_to_ints:
            new_idx = len(self.objs_to_ints)
            self.objs_to_ints[object] = new_idx
            self.ints_to_objs[new_idx] = object
        return self.objs_to_ints[object]

class UnigramFeatureExtractor():
    def __init__(self, indexer: Indexer):
        self._indexer = indexer

    def get_indexer(self) -> Indexer:
        return self._indexer

    def extract_features(self, sentence: List[str], add_to_indexer: bool = False) -> Counter:

        # Contains non-unique list of all unigrams parsed from the sentence
        unigram_list: List[str] = []

        for unigram in sentence:

            index = self._indexer.add_and_get_index(unigram.lower(), add_to_indexer)

            # If unigram didn't get added to the indexer (this occurs during the testing phase)
            if index != -1:
                unigram_list.append(unigram.lower())

        return Counter(unigram_list)

# Helper function to create feature vector from feature counter
def get_feature_vector(feature_counter: Counter, feature_extractor) -> np.ndarray:

    feature_vector = np.zeros(len(feature_extractor.get_indexer()) + 1)

    for feature in feature_counter:
        feature_idx = feature_extractor.get_indexer().index_of(feature)
        feature_vector[feature_idx] = feature_counter[feature]

    feature_vector[-1] = 1

    return feature_vector

class SpotifinderModel(object):

    def __init__(self):
        self.indexer = Indexer()
        self.uni_fv = UnigramFeatureExtractor(self.indexer)

        # load lyric data
        data = pd.read_csv('lyric_data.csv')

        # preprocess data
        data.dropna(subset = ['lyrics'], inplace=True)
        data = data.astype({"lyrics": str}, errors='raise')

        # filter lyrics
        pre_filter_lyrics = data['lyrics'].tolist()
        lyrics = []

        for song in pre_filter_lyrics:
            song = song.replace('\n', ' ')
            song = song.replace('.', ' ')
            song = song.replace(',', ' ')
            song = song.replace('(', ' ')
            song = song.replace(')', ' ')
            lyrics.append(song.lower())

        # get feature vectors
        counter_list = []
        for i, song in enumerate(lyrics):
            words = song.split(' ')
            counter = self.uni_fv.extract_features(words, True)
            counter_list.append(counter)

        feature_vector_list = []
        for counter in counter_list:
            feature_vector = get_feature_vector(counter, self.uni_fv)
            feature_vector = np.where(feature_vector > 0, 1, 0)
            feature_vector_list.append(feature_vector)

        feature_matrix = np.array(feature_vector_list)

        # danceability model
        X = feature_matrix
        y = data[['danceability']]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=44)

        self.dance_reg = LinearRegression().fit(X_train, y_train)

        # energy model
        X = feature_matrix
        y = data[['energy']]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=44)

        self.energy_reg = LinearRegression().fit(X_train, y_train)

        # valence model
        X = feature_matrix
        y = data[['valence']]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=44)

        self.valence_reg = LinearRegression().fit(X_train, y_train)

    def get_vector(self, sentence: str) -> np.array:

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

        dance = self.dance_reg.predict(feature_vector)[0][0]
        energy = self.energy_reg.predict(feature_vector)[0][0]
        valence = self.valence_reg.predict(feature_vector)[0][0]

        output = np.random.rand(3,1)

        # Ensure values between 0 and 1
        for i, feat in enumerate(output):
            if feat > 1.0:
                output[i] = 1.0
            elif feat < 0.0:
                output[i] = 0.0

        return {'danceability': output[0], 'energy': output[1], 'valence': output[2]}

if __name__ == "__main__":

    model = SpotifinderModel()

    sent1 = "Brown guilty eyes and\n\
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

    sent2 = "Remember the words you told me, love me 'til the day I die\n\
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


    print(model.get_vector(sent1))
    print(model.get_vector(sent2))

    sen3 = "I caught it bad yesterday\n\
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

    print(model.get_vector(sen3))

    print(model.get_vector("I just want to go to home depot"))

    print(model.get_vector("I feel really sad so bad today I'm hurt lonely"))

    print(model.get_vector("Let's get turnt turnt up yeah lit boy let's go to town drive"))
