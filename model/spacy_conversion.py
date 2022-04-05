import os
import spacy

runProgram = os.environ.get('SPACY_CHANGE')

if runProgram != 0:
    nlp = spacy.load("en_core_web_sm")
    text_file = open("emotion_text.txt", "r", encoding='utf-8')

    data = text_file.read()
    text_file.close()

    # file paths
    in_filepath = 'emotion_text.txt'
    out_filepath = 'emotion_text_replaced.txt'

    # loop through sentences
    with open(out_filepath, 'w', encoding='utf8') as out_file:
        with open(in_filepath, 'r', encoding='utf-8') as in_file:
            line = in_file.readline()
            cnt = 1
            while line:
                line = in_file.readline()
                cnt += 1

                try:
                    sent = line.split(',')[1]
                    doc = nlp(sent)
                    out_file.write(" ".join([ent.text for ent in doc if not ent.ent_type_]))
                except:
                    print(line)

