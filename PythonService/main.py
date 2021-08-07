#!/usr/bin/env python

import os
import json
import spacy
from units_model import units
from keys_model import keys_model


pipe_in = r'/pipeVolume/pipe-out'
pipe_out = r'/pipeVolume/pipe-in'


def main():
    try:
        os.mkfifo(pipe_in)
    except Exception as e:
        if str(e) == "[Errno 17] File exists":
            os.remove(pipe_in)
            os.mkfifo(pipe_in)
        else:
            print(e)
            quit(1)

    request = {"Action": "start", "Str": ""}
    byte_data = json.dumps(request)

    with open(pipe_out, 'rb+', 0) as pipe:
        pipe.write(byte_data.encode())
        pipe.close()

    nlp1 = spacy.load("./model1LVL")
    nlp2 = spacy.load("./model2LVL")
    nlp3 = units.SuperModel().get_model()
    nlp4 = keys_model.SuperModel().get_model()

    while True:
        fifo1 = open(pipe_in, 'rb+', 0)
        byte_json = fifo1.read(1024 * 10 ** 3)
        fifo1.close()
        str_json = byte_json.decode()
        data = json.loads(str_json)
        doc1 = nlp1(data["str"])
        keys = []
        unitsLVL_flag = False
        ent1_flag = False  # проверка на ненулевое содержание ent2

        dict1 = {
            'key': "",
            'values': []
        }

        dict2 = {
            'key': "",
            'value': "",
            'units1lvl': "",
            'units2lvl': "",
            'non-key': ""
        }

        for ent1 in doc1.ents:

            if ent1.label_ == "KEY":
                if dict1['key'] != "":
                    keys.append(dict(dict1))
                    dict1['key'] = ""
                    dict1['values'] = []
                    dict2['key'] = ""
                    dict2['value'] = ""
                    dict2['units1lvl'] = ""
                    dict2['units2lvl'] = ""
                    dict2['non-key'] = ""
                key1 = ent1.text
                dict1['key'] = nlp4[key1] if key1 in nlp4 else key1

            if ent1.label_ == "VALUE":
                doc2 = nlp2(ent1.text)
                key2_flag = False
                for ent2 in doc2.ents:
                    if ent2.label_ == "NON-KEY":
                        ent1_flag = True
                        if not key2_flag:
                            if dict2['key'] != "":
                                dict1['values'].append(dict(dict2))
                                dict2['key'] = ""
                                dict2['value'] = ""
                                dict2['units1lvl'] = ""
                                dict2['units2lvl'] = ""
                                dict2['non-key'] = ""
                            dict2['key'] = nlp4[ent2.text] if ent2.text in nlp4 else ent2.text
                            unitsLVL_flag = False
                        if key2_flag:
                            dict2['non-key'] = ent2.text
                    if ent2.label_ == "KEY":
                        if dict2['key'] != "":
                            dict1['values'].append(dict(dict2))
                            dict2['key'] = ""
                            dict2['value'] = ""
                            dict2['units1lvl'] = ""
                            dict2['units2lvl'] = ""
                            dict2['non-key'] = ""
                        ent1_flag = True
                        key2_flag = True
                        dict2['key'] = nlp4[ent2.text] if ent2.text in nlp4 else ent2.text
                        unitsLVL_flag = True
                    if ent2.label_ == "UNITS":
                        ent1_flag = True
                        if not unitsLVL_flag:
                            dict2['units1lvl'] = nlp3[ent2.text] if ent2.text in nlp3 else ent2.text
                        else:
                            dict2['units2lvl'] = nlp3[ent2.text] if ent2.text in nlp3 else ent2.text
                            unitsLVL_flag = False
                    if ent2.label_ == "VALUE":
                        ent1_flag = True
                        dict2['value'] = ent2.text
                        unitsLVL_flag = True
                if dict2['key'] != "":
                    dict1['values'].append(dict(dict2))
                if not ent1_flag:
                    dict1['values'].append(ent1.text)

        keys.append(dict1)
        byte_data = json.dumps(keys)
        fifo2 = open(pipe_out, 'rb+', 0)
        fifo2.write(byte_data.encode())
        fifo2.close()


if __name__ == "__main__":
    main()
