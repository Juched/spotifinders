#!/usr/bin/env python
# coding: utf-8

# In[15]:


import spacy
nlp = spacy.load("en_core_web_sm")


# In[16]:


#open text file in read mode
text_file = open("emotion_text.txt", "r", encoding='utf-8')
 
#read whole file to a string
data = text_file.read()
 
#close file
text_file.close()


# In[34]:


# file path
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

